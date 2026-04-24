from apps.cases.services.compose import compose_revised_hpi
from apps.cases.services.criteria import (
    enrich_structured_output_with_source_evidence,
    match_mcg_criteria,
    reconcile_diabetes_disposition,
)
from apps.cases.services.extract import extract_structured_output
from apps.cases.services.privacy import redact_phi
from apps.cases.services.validators import (
    calculate_admission_support_confidence,
    build_generation_warning_groups,
    build_uncertainties,
    collect_structured_validation_warnings,
    flatten_generation_warning_groups,
    validate_generated_structured_output,
    verify_revised_hpi,
)


def run_generate_pipeline(note: str) -> dict:
    redacted_note = redact_phi(note)
    raw_structured_output = extract_structured_output(redacted_note)
    structured_output = validate_generated_structured_output(raw_structured_output)
    structured_output = enrich_structured_output_with_source_evidence(
        structured_output,
        source_text=note,
    )
    validation_warnings = collect_structured_validation_warnings(
        raw_structured_output,
        structured_output,
    )
    mcg_result = match_mcg_criteria(structured_output, source_text=note)
    structured_output, mcg_result = reconcile_diabetes_disposition(
        structured_output,
        mcg_result,
        source_text=note,
    )

    revised_hpi = compose_revised_hpi(structured_output, mcg_result=mcg_result)
    verification = verify_revised_hpi(revised_hpi, structured_output, mcg_result=mcg_result)

    if verification["needs_regeneration"]:
        revised_hpi = compose_revised_hpi(
            structured_output,
            mcg_result=mcg_result,
            revision_instructions=verification["revision_instructions"],
        )
        verification = verify_revised_hpi(
            revised_hpi,
            structured_output,
            mcg_result=mcg_result,
        )

    warning_groups = build_generation_warning_groups(
        validation_warnings,
        verification,
        mcg_result=mcg_result,
        source_text=note,
        structured_output=structured_output,
    )
    warnings = flatten_generation_warning_groups(warning_groups)
    confidence_result = calculate_admission_support_confidence(
        verification,
        mcg_result,
        warnings,
        structured_output=structured_output,
        source_text=note,
    )
    structured_output["uncertainties_generated"] = build_uncertainties(
        structured_output,
        generation_warnings=warnings,
        mcg_result=mcg_result,
        verification=verification,
        source_text=note,
    )

    return {
        "structured_output": structured_output,
        "mcg_result": mcg_result,
        "revised_hpi": revised_hpi,
        "verification": verification,
        "warnings": warnings,
        "warning_groups": warning_groups,
        "confidence_result": confidence_result,
        "privacy": {
            "phi_redaction_applied": redacted_note != note,
            "redaction_types": [
                "SSN",
                "PHONE",
                "EMAIL",
                "DOB",
                "MRN",
                "PATIENT_ID",
                "NAME",
                "ADDRESS",
            ],
        },
    }
