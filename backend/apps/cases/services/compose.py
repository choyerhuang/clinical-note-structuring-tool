import json

from apps.cases.services.llm_client import get_llm_provider
from apps.cases.services.note_generation import (
    extract_text_response,
    normalize_generated_structured_input,
)
from apps.cases.services.prompts import REVISED_HPI_PROMPT_TEMPLATE


def _structured_search_text(normalized_structured: dict) -> str:
    return " ".join(
        [
            normalized_structured["chief_complaint_generated"],
            normalized_structured["hpi_summary_generated"],
            " ".join(normalized_structured["key_findings_generated"]),
            " ".join(normalized_structured["suspected_conditions_generated"]),
            " ".join(normalized_structured["uncertainties_generated"]),
            " ".join(normalized_structured["source_support"]),
        ]
    ).lower()


def _build_care_plan_context(normalized_structured: dict, mcg_result: dict) -> dict | None:
    search_text = _structured_search_text(normalized_structured)
    disposition = normalized_structured["disposition_generated"]
    matched_ids = {item.get("id", "") for item in (mcg_result or {}).get("matched_criteria", [])}

    if disposition == "Discharge":
        return {
            "setting": "outpatient",
            "monitoring": ["outpatient follow-up and reassessment if symptoms worsen"],
            "lower_level_limitations": ["inpatient-level care is not indicated by the available evidence"],
        }

    if disposition not in {"Admit", "Observe"}:
        return None

    if matched_ids & {"diabetic_ketoacidosis", "hyperosmolar_hyperglycemic_state"}:
        return {
            "setting": "inpatient",
            "interventions": [
                "continued glucose-directed therapy",
                "fluid resuscitation",
            ],
            "monitoring": [
                "close electrolyte monitoring",
                "serial metabolic reassessment",
            ],
            "lower_level_limitations": [
                "ongoing metabolic management and serial reassessment cannot be safely completed at a lower level of care",
            ],
        }

    if matched_ids & {"failed_observation_or_outpatient", "severe_hyperglycemia"}:
        return {
            "setting": "inpatient",
            "interventions": [
                "continued glucose control",
                "ongoing hydration support",
            ],
            "monitoring": [
                "close monitoring of glucose and hydration status",
                "reassessment after failed lower-level treatment",
            ],
            "lower_level_limitations": [
                "persistent symptoms after prior treatment require continued inpatient management and reassessment",
            ],
        }

    if any(token in search_text for token in ["pneumonia", "infection", "sepsis"]):
        interventions = []
        monitoring = ["monitoring of clinical response"]
        if "iv antibiotics" in search_text or "intravenous antibiotics" in search_text:
            interventions.append("continued IV antibiotic therapy")
        if any(token in search_text for token in ["hypoxemia", "oxygen", "supplemental oxygen"]):
            interventions.append("oxygen support as needed")
            monitoring.append("close respiratory monitoring")
        return {
            "setting": "inpatient",
            "interventions": interventions,
            "monitoring": monitoring,
            "lower_level_limitations": [
                "treatment and reassessment cannot yet be safely completed at a lower level of care",
            ],
        }

    if disposition == "Admit":
        return {
            "setting": "inpatient",
            "monitoring": ["continued monitoring and reassessment"],
            "lower_level_limitations": [
                "the available evidence supports ongoing management that cannot yet be safely stepped down",
            ],
        }

    return {
        "setting": "observation",
        "monitoring": ["continued monitoring and completion of the current evaluation"],
        "lower_level_limitations": [
            "the evaluation is not yet complete enough to safely step down care",
        ],
    }


def compose_revised_hpi(
    structured: dict,
    mcg_result: dict | None = None,
    revision_instructions: list[str] | None = None,
) -> str:
    normalized_structured = normalize_generated_structured_input(structured)
    mcg_result = mcg_result or {}
    has_minimal_content = any(
        [
            normalized_structured["chief_complaint_generated"],
            normalized_structured["hpi_summary_generated"],
            normalized_structured["key_findings_generated"],
        ]
    )
    if not has_minimal_content:
        return (
            "Limited structured information is available. The patient presented for "
            "evaluation, but the symptom history and supporting clinical details remain "
            "unclear in the current structured data."
        )

    provider, model = get_llm_provider()
    payload = {
        "chief_complaint_generated": normalized_structured["chief_complaint_generated"],
        "hpi_summary_generated": normalized_structured["hpi_summary_generated"],
        "key_findings_generated": normalized_structured["key_findings_generated"],
        "suspected_conditions_generated": normalized_structured[
            "suspected_conditions_generated"
        ],
        "disposition_generated": normalized_structured["disposition_generated"],
        "uncertainties_generated": normalized_structured["uncertainties_generated"],
    }
    care_plan_context = _build_care_plan_context(normalized_structured, mcg_result)
    if care_plan_context:
        payload["care_plan_context"] = care_plan_context

    if mcg_result.get("applicable"):
        matched_criteria = mcg_result.get("matched_criteria", [])
        matched_ids = {item.get("id", "") for item in matched_criteria}
        disposition_context = mcg_result.get("disposition_context") or {}
        explicit_treatment_failure = any(
            signal in {
                "glucose not stabilized after treatment",
                "failed initial management",
                "continued monitoring or treatment required",
            }
            for item in matched_criteria
            for signal in item.get("matched_signals", [])
        )
        treatment_failure_branch = bool(
            matched_ids & {"failed_observation_or_outpatient", "severe_hyperglycemia"}
        ) and explicit_treatment_failure and not bool(
            matched_ids & {"diabetic_ketoacidosis", "hyperosmolar_hyperglycemic_state"}
        )

        admission_support_context = {
            "applicable": True,
            "supported": bool(mcg_result.get("supported")),
            "support_level": mcg_result.get("support_level", "low"),
            "criteria_summary": mcg_result.get("criteria_summary", ""),
            "matched_criteria": [
                {
                    "id": item.get("id", ""),
                    "matched_signals": item.get("matched_signals", []),
                }
                for item in matched_criteria
            ],
        }
        if disposition_context.get("inpatient_level_care_not_required"):
            admission_support_context["support_branch"] = "outpatient_management"
            admission_support_context["branch_guidance"] = (
                "The available evidence supports discharge or outpatient follow-up. "
                "State clearly that inpatient-level care is not indicated. Do not describe "
                "instability, treatment failure, need for inpatient monitoring, or admission "
                "support unless those facts are explicitly documented."
            )
            admission_support_context["matched_criteria"] = []
        elif treatment_failure_branch:
            admission_support_context["support_branch"] = "treatment_failure"
            admission_support_context["branch_guidance"] = (
                "Independent admission support is present through persistent hyperglycemia, "
                "ongoing dehydration or instability, failure of lower-level care, and the need "
                "for continued inpatient monitoring and treatment. Missing DKA-specific labs "
                "should not be used to downplay this branch or to frame support as low."
            )
        else:
            admission_support_context["missing_data"] = mcg_result.get("missing_data", [])

        if disposition_context:
            admission_support_context["disposition_context"] = disposition_context

        payload["admission_support_context"] = admission_support_context

    structured_payload = json.dumps(payload, ensure_ascii=True)

    revision_block = ""
    if revision_instructions:
        revision_block = (
            "\n\nApply these revision instructions while still using only the supplied "
            f"structured facts:\n- " + "\n- ".join(revision_instructions)
        )

    response = provider.generate_text(
        model=model,
        system_prompt=REVISED_HPI_PROMPT_TEMPLATE,
        user_prompt=(
            "Write a revised HPI using only these structured facts:\n\n"
            f"{structured_payload}{revision_block}"
        ),
    )

    return extract_text_response(response)
