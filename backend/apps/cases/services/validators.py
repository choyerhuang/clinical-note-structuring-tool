from apps.cases.services.note_generation import normalize_generated_structured_input, safe_string_list, safe_text
from apps.cases.services.criteria import has_numeric_or_text_evidence


def validate_note_for_generation(note):
    normalized_note = (note or "").strip()
    if not normalized_note:
        raise ValueError("original_note cannot be empty or whitespace.")
    return normalized_note


VALID_DISPOSITIONS = {"Admit", "Observe", "Discharge", "Unknown"}
EXPECTED_STRUCTURED_KEYS = {
    "chief_complaint_generated",
    "hpi_summary_generated",
    "key_findings_generated",
    "suspected_conditions_generated",
    "disposition_generated",
    "uncertainties_generated",
}
LIST_FIELDS = {
    "key_findings_generated",
    "suspected_conditions_generated",
    "uncertainties_generated",
}

UNCERTAINTY_TEXT_MAP = {
    "ph": "pH not available to fully assess severity of acidosis",
    "serum osmolality": "Serum osmolality not available",
    "osmolality": "Serum osmolality not available",
    "response to treatment": "Response to treatment not yet documented",
    "post-treatment reassessment": "Post-treatment reassessment pending",
    "ketone level": "Ketone status not available",
    "bicarbonate": "Bicarbonate level not available",
    "anion gap": "Anion gap not available",
    "glucose": "Glucose value not available",
}

UNCERTAINTY_EXPANSIONS = {
    "bicarbonate and ph not available": [
        "Bicarbonate level not available",
        "pH not available to fully assess severity of acidosis",
    ],
    "ph and bicarbonate not available": [
        "pH not available to fully assess severity of acidosis",
        "Bicarbonate level not available",
    ],
}

UNCERTAINTY_GROUPS = {
    "no ketone testing performed": "ketone_status",
    "ketone status not available": "ketone_status",
}

UNCERTAINTY_PRIORITY = {
    "no ketone testing performed": 2,
    "ketone status not available": 1,
}

NON_CLINICAL_UNCERTAINTY_PHRASES = [
    "revised hpi may need regeneration",
    "revised hpi may not align with the stated disposition",
    "revised hpi may not be fully factually consistent",
    "admission disposition should more clearly explain",
    "chief complaint is not clearly stated",
    "narrative should explain why admission is still needed",
    "structured output should acknowledge uncertainty when facts are sparse",
    "matched criterion",
]

MISSING_DATA_WARNING_LABELS = {
    "ketone level": "Ketone level",
    "ketone status not available": "Ketone level",
    "no ketone testing performed": "Ketone level",
    "ph": "pH",
    "pH not available to fully assess severity of acidosis": "pH",
    "bicarbonate": "Bicarbonate",
    "bicarbonate level not available": "Bicarbonate",
    "anion gap": "Anion gap",
    "anion gap not available": "Anion gap",
    "serum osmolality": "Serum osmolality",
    "serum osmolality not available": "Serum osmolality",
    "osmolality": "Serum osmolality",
    "response to treatment": "Response to treatment documentation",
    "response to treatment not yet documented": "Response to treatment documentation",
    "post-treatment reassessment": "Post-treatment reassessment",
    "post-treatment reassessment pending": "Post-treatment reassessment",
    "glucose": "Glucose",
    "glucose value not available": "Glucose",
    "vital signs not documented": "Vital signs",
    "key laboratory severity markers not available": "Laboratory severity markers",
    "duration of symptoms not specified": "Symptom duration",
    "response to prior treatment not documented": "Response to prior treatment",
}

WARNING_TO_UNCERTAINTY_TEXT_MAP = {
    "vital signs": "Vital signs not documented",
    "laboratory severity markers": "Key laboratory severity markers not available",
    "symptom duration": "Duration of symptoms not specified",
    "response to prior treatment": "Response to prior treatment not documented",
    "ketone level": "Ketone status not available",
    "ph": "pH not available to fully assess severity of acidosis",
    "bicarbonate": "Bicarbonate level not available",
    "anion gap": "Anion gap not available",
    "serum osmolality": "Serum osmolality not available",
    "response to treatment documentation": "Response to treatment not yet documented",
    "post-treatment reassessment": "Post-treatment reassessment pending",
    "glucose": "Glucose value not available",
}

POTENTIAL_ISSUE_WARNING_MAP = {
    "chief complaint is not clearly stated.": "Chief complaint may not be clearly defined.",
    "revised hpi may not be fully factually consistent.": "Revised HPI should be reviewed for factual consistency.",
    "revised hpi may not align with the stated disposition.": "Revised HPI should be reviewed for consistency with the stated disposition.",
    "revised hpi may need regeneration.": "Revised HPI should be reviewed for consistency.",
    "structured output is sparse and may need clinician review.": "Structured output is limited and should be reviewed.",
}

CRITICAL_MISSING_DATA_TOKENS = [
    "pH",
    "bicarbonate",
    "anion gap",
    "serum osmolality",
    "ketone",
    "ketones",
    "ketone level",
]

GENERAL_MISSING_DATA_TOKENS = [
    "response to treatment",
    "response to prior treatment",
    "treatment response",
    "vitals",
    "vital signs",
    "duration",
    "reassessment",
    "follow-up status",
    "laboratory severity markers",
]


def _structured_data_is_sparse(structured):
    populated_core_fields = 0
    if structured["chief_complaint_generated"]:
        populated_core_fields += 1
    if structured["hpi_summary_generated"]:
        populated_core_fields += 1
    if structured["key_findings_generated"]:
        populated_core_fields += 1

    return populated_core_fields <= 1


def _build_general_missing_search_text(
    source_text: str | None,
    structured_output: dict,
) -> str:
    normalized = normalize_generated_structured_input(structured_output)
    return " ".join(
        [
            safe_text(source_text),
            normalized["chief_complaint_generated"],
            normalized["hpi_summary_generated"],
            " ".join(normalized["key_findings_generated"]),
            " ".join(normalized["suspected_conditions_generated"]),
            " ".join(normalized["source_support"]),
        ]
    ).lower()


def _structured_search_text(structured: dict) -> str:
    normalized = normalize_generated_structured_input(structured)
    return " ".join(
        [
            normalized["chief_complaint_generated"],
            normalized["hpi_summary_generated"],
            " ".join(normalized["key_findings_generated"]),
            " ".join(normalized["suspected_conditions_generated"]),
            " ".join(normalized["source_support"]),
        ]
    ).lower()


def _refine_suspected_conditions(structured: dict) -> list[str]:
    conditions = safe_string_list(structured.get("suspected_conditions_generated"))
    if not conditions:
        return []

    search_text = _structured_search_text(structured)
    refined_conditions: list[str] = []

    def add_condition(label: str):
        cleaned_label = safe_text(label)
        if cleaned_label and cleaned_label not in refined_conditions:
            refined_conditions.append(cleaned_label)

    for condition in conditions:
        normalized_condition = condition.lower()
        if normalized_condition != "diabetes-related complications":
            add_condition(condition)
            continue

        if any(token in search_text for token in ["dka", "ketoacidosis", "ketonemia", "ketonuria"]):
            add_condition("Diabetic ketoacidosis")
        if "hyperglycemia" in search_text or "glucose" in search_text:
            add_condition("Hyperglycemia")
        if "dehydration" in search_text:
            add_condition("Dehydration")
        if any(
            token in search_text
            for token in [
                "persistent hyperglycemia despite insulin",
                "glucose remains elevated after treatment",
                "failed initial management",
                "continued monitoring",
                "continued inpatient management",
            ]
        ):
            add_condition("Failure of outpatient management")

    return refined_conditions or conditions


def validate_generated_structured_output(structured: dict) -> dict:
    structured = structured or {}

    normalized = {key: structured.get(key) for key in EXPECTED_STRUCTURED_KEYS}
    normalized["chief_complaint_generated"] = safe_text(
        normalized.get("chief_complaint_generated")
    )
    normalized["hpi_summary_generated"] = safe_text(
        normalized.get("hpi_summary_generated")
    )

    for field_name in LIST_FIELDS:
        normalized[field_name] = safe_string_list(normalized.get(field_name))
    normalized["suspected_conditions_generated"] = _refine_suspected_conditions(normalized)

    disposition = safe_text(normalized.get("disposition_generated"))
    normalized["disposition_generated"] = (
        disposition if disposition in VALID_DISPOSITIONS else "Unknown"
    )

    if _structured_data_is_sparse(normalized) and not normalized["uncertainties_generated"]:
        normalized["uncertainties_generated"] = [
            "Limited structured detail is available from the source note."
        ]

    return normalized


def collect_structured_validation_warnings(
    raw_structured: dict, validated_structured: dict
) -> list[str]:
    warnings = []
    raw_structured = raw_structured or {}

    for key in EXPECTED_STRUCTURED_KEYS:
        if key not in raw_structured:
            warnings.append(f"Structured output was missing expected field '{key}'.")

    for field_name in LIST_FIELDS:
        if field_name in raw_structured and not isinstance(raw_structured.get(field_name), list):
            warnings.append(f"Structured field '{field_name}' was coerced to an empty list.")

    raw_disposition = safe_text(raw_structured.get("disposition_generated"))
    if raw_disposition and raw_disposition not in VALID_DISPOSITIONS:
        warnings.append("Structured disposition was invalid and normalized to Unknown.")

    if _structured_data_is_sparse(validated_structured):
        warnings.append("Structured output is sparse and may need clinician review.")

    return warnings


def _normalized_uncertainty_key(value: str) -> str:
    return safe_text(value).lower()


def _map_uncertainty_candidate(candidate: str) -> str:
    cleaned_candidate = safe_text(candidate)
    if not cleaned_candidate:
        return ""

    normalized_candidate = cleaned_candidate.lower()
    for token, mapped_text in UNCERTAINTY_TEXT_MAP.items():
        if normalized_candidate == token or token in normalized_candidate:
            return mapped_text

    return ""


def _expand_uncertainty_candidate(candidate: str) -> list[str]:
    cleaned_candidate = safe_text(candidate)
    if not cleaned_candidate:
        return []

    normalized_candidate = cleaned_candidate.lower()
    if normalized_candidate in UNCERTAINTY_EXPANSIONS:
        return UNCERTAINTY_EXPANSIONS[normalized_candidate]

    mapped_candidate = _map_uncertainty_candidate(cleaned_candidate)
    if mapped_candidate:
        return [mapped_candidate]

    return [cleaned_candidate]


def _uncertainty_group(item: str) -> str:
    normalized_item = _normalized_uncertainty_key(item)
    return UNCERTAINTY_GROUPS.get(normalized_item, normalized_item)


def _uncertainty_priority(item: str) -> int:
    return UNCERTAINTY_PRIORITY.get(_normalized_uncertainty_key(item), 0)


def _is_clinical_uncertainty(item: str) -> bool:
    normalized_item = _normalized_uncertainty_key(item)
    return not any(phrase in normalized_item for phrase in NON_CLINICAL_UNCERTAINTY_PHRASES)


def _warning_label_from_missing_item(item: str) -> str:
    normalized_item = _normalized_uncertainty_key(item)
    return MISSING_DATA_WARNING_LABELS.get(normalized_item, safe_text(item))


def _warning_to_uncertainty_candidate(item: str) -> str:
    cleaned_item = safe_text(item)
    if not cleaned_item:
        return ""

    normalized_item = cleaned_item.lower()
    if normalized_item.startswith("missing data:"):
        normalized_item = normalized_item.replace("missing data:", "", 1).strip()
        return WARNING_TO_UNCERTAINTY_TEXT_MAP.get(normalized_item, cleaned_item.split(":", 1)[1].strip())

    return ""


def _normalize_potential_issue(item: str) -> str:
    cleaned_item = safe_text(item)
    if not cleaned_item:
        return ""

    normalized_item = cleaned_item.lower()
    if normalized_item in POTENTIAL_ISSUE_WARNING_MAP:
        return POTENTIAL_ISSUE_WARNING_MAP[normalized_item]

    if normalized_item.startswith("structured output was missing expected field"):
        return "Structured output was incomplete and some fields were reconstructed."
    if normalized_item.startswith("structured field '") and "was coerced to an empty list" in normalized_item:
        return "Some structured list fields were incomplete and were normalized."

    return cleaned_item


def build_general_missing_information(
    source_text: str | None,
    structured_output: dict,
) -> list[str]:
    normalized_source_text = safe_text(source_text)
    if len(normalized_source_text.split()) < 12:
        return []

    search_text = _build_general_missing_search_text(source_text, structured_output)
    if not search_text.strip():
        return []

    missing_items = []

    def add_missing(label: str):
        if label not in missing_items:
            missing_items.append(label)

    vitals_present = any(
        token in search_text
        for token in [
            "bp ",
            "blood pressure",
            "hr ",
            "heart rate",
            "rr ",
            "respiratory rate",
            "temp ",
            "temperature",
            "o2 sat",
            "oxygen saturation",
            "spo2",
            "pulse ",
        ]
    )
    if not vitals_present:
        add_missing("Vital signs not documented")

    severity_markers_present = any(
        token in search_text
        for token in [
            "wbc",
            "white blood cell",
            "white count",
            "leukocytosis",
            "lactate",
            "creatinine",
            "crp",
            "c-reactive protein",
        ]
    )
    if not severity_markers_present:
        add_missing("Key laboratory severity markers not available")

    duration_present = any(
        token in search_text
        for token in [
            " hour",
            " hours",
            " day",
            " days",
            " week",
            " weeks",
            " since yesterday",
            " earlier today",
            " today",
            " overnight",
        ]
    )
    if not duration_present:
        add_missing("Duration of symptoms not specified")

    discusses_admission_or_treatment_need = any(
        token in search_text
        for token in [
            "admit",
            "admission",
            "need for iv antibiotics",
            "requires iv antibiotics",
            "continued monitoring",
            "continued treatment",
            "requires ongoing treatment",
            "inpatient",
            "observation",
        ]
    )
    prior_treatment_or_response_present = any(
        token in search_text
        for token in [
            "prior treatment",
            "after treatment",
            "after antibiotics",
            "after insulin",
            "after fluids",
            "failed outpatient",
            "failed initial management",
            "no improvement",
            "not improved",
            "improved",
            "worsening despite",
            "response to treatment",
        ]
    )
    if discusses_admission_or_treatment_need and not prior_treatment_or_response_present:
        add_missing("Response to prior treatment not documented")

    return missing_items


def build_uncertainties(
    structured_output: dict,
    generation_warnings: list[str] | None = None,
    mcg_result: dict | None = None,
    verification: dict | None = None,
    source_text: str | None = None,
) -> list[str]:
    structured_output = validate_generated_structured_output(structured_output)
    generation_warnings = safe_string_list(generation_warnings)
    mcg_result = mcg_result or {}
    verification = verification or {}

    uncertainty_items = []
    seen_items = set()
    group_positions = {}

    def add_uncertainty(item: str):
        cleaned_item = safe_text(item)
        if not cleaned_item:
            return
        if not _is_clinical_uncertainty(cleaned_item):
            return

        normalized_key = _normalized_uncertainty_key(cleaned_item)
        if normalized_key in seen_items:
            return

        group_key = _uncertainty_group(cleaned_item)
        if group_key in group_positions:
            current_index = group_positions[group_key]
            current_item = uncertainty_items[current_index]
            if _uncertainty_priority(cleaned_item) > _uncertainty_priority(current_item):
                seen_items.discard(_normalized_uncertainty_key(current_item))
                uncertainty_items[current_index] = cleaned_item
                seen_items.add(normalized_key)
            return

        group_positions[group_key] = len(uncertainty_items)
        seen_items.add(normalized_key)
        uncertainty_items.append(cleaned_item)

    for existing_item in structured_output["uncertainties_generated"]:
        for expanded_item in _expand_uncertainty_candidate(existing_item):
            add_uncertainty(expanded_item)

    for general_item in build_general_missing_information(source_text, structured_output):
        add_uncertainty(general_item)

    candidate_sources = [
        *[
            mapped_warning
            for warning in generation_warnings
            for mapped_warning in [_warning_to_uncertainty_candidate(warning)]
            if mapped_warning
        ],
        *safe_string_list(mcg_result.get("missing_data")),
        *safe_string_list(
            verification.get("missing_required_data_for_confident_interpretation")
        ),
    ]

    for candidate in candidate_sources:
        if has_numeric_or_text_evidence(structured_output, source_text, candidate):
            continue
        for expanded_item in _expand_uncertainty_candidate(candidate):
            add_uncertainty(expanded_item)

    return filter_missing_uncertainties_against_evidence(
        structured_output,
        uncertainty_items,
        source_text=source_text,
    )


def filter_missing_uncertainties_against_evidence(
    structured_output: dict,
    uncertainty_items: list[str] | None,
    source_text: str | None = None,
) -> list[str]:
    filtered_items = []
    for item in uncertainty_items or []:
        cleaned_item = safe_text(item)
        if not cleaned_item:
            continue
        if has_numeric_or_text_evidence(structured_output, source_text, cleaned_item):
            continue
        if cleaned_item not in filtered_items:
            filtered_items.append(cleaned_item)
    return filtered_items


def build_generation_warning_groups(
    validation_warnings: list[str] | None,
    verification: dict | None,
    mcg_result: dict | None = None,
    source_text: str | None = None,
    structured_output: dict | None = None,
) -> dict:
    validation_warnings = safe_string_list(validation_warnings)
    verification = verification or {}
    mcg_result = mcg_result or {}
    structured_output = structured_output or {}

    missing_data = []
    potential_issues = []

    for candidate in [
        *safe_string_list(mcg_result.get("missing_data")),
        *safe_string_list(
            verification.get("missing_required_data_for_confident_interpretation")
        ),
        *build_general_missing_information(source_text, structured_output),
    ]:
        label = _warning_label_from_missing_item(candidate)
        if label and label not in missing_data:
            missing_data.append(label)

    for candidate in [
        *validation_warnings,
        *safe_string_list(verification.get("unsupported_claims")),
        *safe_string_list(verification.get("missing_key_facts")),
        *safe_string_list(verification.get("disposition_inconsistencies")),
        *safe_string_list(verification.get("criteria_alignment_issues")),
    ]:
        normalized_issue = _normalize_potential_issue(candidate)
        if normalized_issue and normalized_issue not in potential_issues:
            potential_issues.append(normalized_issue)

    if verification.get("factual_consistency") == "fail":
        issue = "Revised HPI should be reviewed for factual consistency."
        if issue not in potential_issues:
            potential_issues.append(issue)

    if verification.get("disposition_consistency") == "fail":
        issue = "Revised HPI should be reviewed for consistency with the stated disposition."
        if issue not in potential_issues:
            potential_issues.append(issue)

    if verification.get("needs_regeneration"):
        issue = "Revised HPI should be reviewed for consistency."
        if issue not in potential_issues:
            potential_issues.append(issue)

    return {
        "missing_data": missing_data,
        "potential_issues": potential_issues,
    }


def flatten_generation_warning_groups(warning_groups: dict | None) -> list[str]:
    warning_groups = warning_groups or {}
    flattened = []

    for item in safe_string_list(warning_groups.get("missing_data")):
        flattened.append(f"Missing data: {item}")

    for item in safe_string_list(warning_groups.get("potential_issues")):
        flattened.append(f"Potential issue: {item}")

    return list(dict.fromkeys(flattened))


def _normalize_missing_item_label(item: str) -> str:
    cleaned_item = safe_text(item)
    if not cleaned_item:
        return ""

    normalized_item = cleaned_item.lower()
    if normalized_item.startswith("missing data:"):
        normalized_item = normalized_item.replace("missing data:", "", 1).strip()
        cleaned_item = cleaned_item.split(":", 1)[1].strip()

    return MISSING_DATA_WARNING_LABELS.get(normalized_item, cleaned_item)


def _collect_missing_data_items(
    verification_result: dict | None,
    mcg_result: dict | None,
    generation_warnings: list[str] | None,
) -> list[str]:
    verification_result = verification_result or {}
    mcg_result = mcg_result or {}
    generation_warnings = safe_string_list(generation_warnings)

    items = []
    for item in [
        *safe_string_list(verification_result.get("missing_required_data_for_confident_interpretation")),
        *safe_string_list(mcg_result.get("missing_data")),
    ]:
        normalized_item = _normalize_missing_item_label(item)
        if normalized_item and normalized_item not in items:
            items.append(normalized_item)

    for warning in generation_warnings:
        normalized_warning = _normalize_missing_item_label(warning)
        if warning.lower().startswith("missing data:") and normalized_warning and normalized_warning not in items:
            items.append(normalized_warning)

    return items


def _is_low_information_input(
    structured_output: dict | None,
    source_text: str | None = None,
) -> bool:
    structured_output = validate_generated_structured_output(structured_output or {})
    normalized_source_text = safe_text(source_text)
    if not normalized_source_text and not any(
        [
            safe_text(structured_output.get("chief_complaint_generated")),
            safe_text(structured_output.get("hpi_summary_generated")),
            safe_string_list(structured_output.get("key_findings_generated")),
            safe_string_list(structured_output.get("suspected_conditions_generated")),
        ]
    ):
        return False

    normalized_hpi_summary = safe_text(structured_output.get("hpi_summary_generated"))
    key_findings = safe_string_list(structured_output.get("key_findings_generated"))
    suspected_conditions = safe_string_list(
        structured_output.get("suspected_conditions_generated")
    )
    source_word_count = len(normalized_source_text.split())

    low_information_signals = 0
    if not normalized_hpi_summary or normalized_hpi_summary.lower() == "not available":
        low_information_signals += 1
    if len(key_findings) < 2:
        low_information_signals += 1
    if not suspected_conditions:
        low_information_signals += 1
    if source_word_count < 25:
        low_information_signals += 1

    return low_information_signals >= 3


def _is_critical_missing_item(item: str) -> bool:
    normalized_item = safe_text(item).lower()
    return any(token.lower() in normalized_item for token in CRITICAL_MISSING_DATA_TOKENS)


def _is_general_missing_item(item: str) -> bool:
    normalized_item = safe_text(item).lower()
    return any(token.lower() in normalized_item for token in GENERAL_MISSING_DATA_TOKENS)


def calculate_admission_support_confidence(
    verification_result: dict | None,
    mcg_result: dict | None,
    generation_warnings: list[str] | None,
    structured_output: dict | None = None,
    source_text: str | None = None,
) -> dict:
    verification_result = verification_result or {}
    mcg_result = mcg_result or {}
    generation_warnings = safe_string_list(generation_warnings)

    score = 0.75
    factors = []

    verification_passed = bool(verification_result.get("is_pass")) or (
        safe_text(verification_result.get("factual_consistency")).lower() == "pass"
        and safe_text(verification_result.get("disposition_consistency")).lower() == "pass"
    )
    if verification_passed:
        score += 0.10
        factors.append(
            {
                "type": "positive",
                "label": "Verifier passed",
                "impact": 0.10,
            }
        )

    support_level = safe_text(mcg_result.get("support_level")).lower()
    mcg_supported = bool(mcg_result.get("supported")) or support_level in {"high", "strong", "moderate", "weak"}
    support_bonus = 0.0
    if mcg_supported:
        if support_level in {"high", "strong"}:
            support_bonus = 0.10
        elif support_level == "moderate":
            support_bonus = 0.05
        elif support_level == "weak":
            support_bonus = 0.02

    if support_bonus:
        score += support_bonus
        factors.append(
            {
                "type": "positive",
                "label": "MCG criteria supported",
                "impact": round(support_bonus, 2),
            }
        )

    if _is_low_information_input(structured_output, source_text=source_text):
        score -= 0.20
        factors.append(
            {
                "type": "negative",
                "label": "Low information penalty",
                "impact": -0.20,
                "details": ["insufficient clinical detail"],
            }
        )

    missing_data_items = _collect_missing_data_items(
        verification_result,
        mcg_result,
        generation_warnings,
    )
    critical_missing = [item for item in missing_data_items if _is_critical_missing_item(item)]
    general_missing = [
        item
        for item in missing_data_items
        if item not in critical_missing and _is_general_missing_item(item)
    ]

    critical_penalty = min(len(critical_missing) * 0.03, 0.15)
    if critical_penalty:
        score -= critical_penalty
        factors.append(
            {
                "type": "negative",
                "label": "Critical missing data capped penalty",
                "impact": round(-critical_penalty, 2),
                "details": critical_missing,
            }
        )

    general_penalty = min(len(general_missing) * 0.01, 0.05)
    if general_penalty:
        score -= general_penalty
        factors.append(
            {
                "type": "negative",
                "label": "General missing information penalty",
                "impact": round(-general_penalty, 2),
                "details": general_missing,
            }
        )

    unsupported_claims = safe_string_list(verification_result.get("unsupported_claims"))
    unsupported_penalty = min(len(unsupported_claims) * 0.10, 0.30)
    if unsupported_penalty:
        score -= unsupported_penalty
        factors.append(
            {
                "type": "negative",
                "label": "Unsupported claims penalty",
                "impact": round(-unsupported_penalty, 2),
                "details": unsupported_claims,
            }
        )

    disposition_inconsistent = (
        safe_text(verification_result.get("disposition_consistency")).lower() not in {"", "pass"}
        or bool(safe_string_list(verification_result.get("disposition_inconsistencies")))
    )
    if disposition_inconsistent:
        score -= 0.20
        factors.append(
            {
                "type": "negative",
                "label": "Disposition inconsistency penalty",
                "impact": -0.20,
            }
        )

    score = round(max(0.0, min(1.0, score)), 2)
    if score >= 0.80:
        level = "High"
    elif score >= 0.60:
        level = "Medium"
    else:
        level = "Low"

    return {
        "score": score,
        "level": level,
        "label": "Admission Support Confidence",
        "factors": factors,
    }


def _default_verification_result():
    return {
        "is_pass": True,
        "factual_consistency": "pass",
        "requires_review": False,
        "unsupported_claims": [],
        "missing_key_facts": [],
        "disposition_consistency": "pass",
        "disposition_inconsistencies": [],
        "criteria_alignment_issues": [],
        "missing_required_data_for_confident_interpretation": [],
        "mcg_admission_check": {
            "applicable": False,
            "matched_criteria": [],
            "support_level": "low",
            "supported": False,
        },
        "needs_regeneration": False,
        "revision_instructions": [],
    }


def _chief_complaint_is_generic(chief_complaint: str) -> bool:
    normalized = safe_text(chief_complaint).lower()
    return normalized in {
        "diabetes issue",
        "diabetes/hyperglycemia",
        "ams, hyperglycemia",
    }


def _apply_verification_decision(normalized: dict) -> dict:
    hard_failures_present = bool(
        normalized["unsupported_claims"]
        or normalized["disposition_inconsistencies"]
        or normalized["criteria_alignment_issues"]
        or normalized["disposition_consistency"] == "fail"
    )
    review_needed = bool(
        normalized["missing_key_facts"]
        or normalized["missing_required_data_for_confident_interpretation"]
    )

    if hard_failures_present:
        normalized["is_pass"] = False
        normalized["requires_review"] = True
        normalized["factual_consistency"] = "fail"
        normalized["needs_regeneration"] = True
        return normalized

    if review_needed:
        normalized["is_pass"] = True
        normalized["requires_review"] = True
        normalized["factual_consistency"] = "pass_with_warnings"
        normalized["needs_regeneration"] = False
        return normalized

    normalized["is_pass"] = True
    normalized["requires_review"] = False
    normalized["factual_consistency"] = "pass"
    normalized["needs_regeneration"] = False
    return normalized


def _normalize_verification_result(verification):
    if not isinstance(verification, dict):
        verification = {}

    normalized = _default_verification_result()
    factual_consistency = safe_text(verification.get("factual_consistency")).lower()
    disposition_consistency = safe_text(
        verification.get("disposition_consistency")
    ).lower()

    normalized["factual_consistency"] = (
        factual_consistency if factual_consistency in {"pass", "pass_with_warnings", "fail"} else "pass"
    )
    normalized["disposition_consistency"] = (
        disposition_consistency
        if disposition_consistency in {"pass", "fail"}
        else "fail"
    )
    normalized["unsupported_claims"] = safe_string_list(
        verification.get("unsupported_claims")
    )
    normalized["missing_key_facts"] = safe_string_list(
        verification.get("missing_key_facts")
    )
    normalized["revision_instructions"] = safe_string_list(
        verification.get("revision_instructions")
    )
    normalized["needs_regeneration"] = bool(verification.get("needs_regeneration"))
    normalized["is_pass"] = bool(verification.get("is_pass", True))
    normalized["requires_review"] = bool(verification.get("requires_review"))
    normalized["disposition_inconsistencies"] = safe_string_list(
        verification.get("disposition_inconsistencies")
    )
    normalized["criteria_alignment_issues"] = safe_string_list(
        verification.get("criteria_alignment_issues")
    )
    normalized["missing_required_data_for_confident_interpretation"] = safe_string_list(
        verification.get("missing_required_data_for_confident_interpretation")
    )
    mcg_admission_check = verification.get("mcg_admission_check") or {}
    normalized["mcg_admission_check"] = {
        "applicable": bool(mcg_admission_check.get("applicable")),
        "matched_criteria": safe_string_list(mcg_admission_check.get("matched_criteria")),
        "support_level": safe_text(mcg_admission_check.get("support_level")) or "low",
        "supported": bool(mcg_admission_check.get("supported")),
    }

    if (
        normalized["factual_consistency"] == "fail"
        or normalized["disposition_consistency"] == "fail"
    ) and not normalized["revision_instructions"]:
        normalized["revision_instructions"] = [
            "Revise the HPI to align only with the structured facts and stated disposition."
        ]

    return _apply_verification_decision(normalized)


def _contains_phrase(text: str, phrases: list[str]) -> bool:
    normalized = text.lower()
    return any(phrase.lower() in normalized for phrase in phrases)


def verify_revised_hpi(revised_hpi: str, structured: dict, mcg_result: dict | None = None) -> dict:
    revised_hpi = safe_text(revised_hpi)
    structured = validate_generated_structured_output(structured)
    default_result = _default_verification_result()
    mcg_result = mcg_result or {
        "applicable": False,
        "matched_criteria": [],
        "support_level": "low",
        "supported": False,
        "missing_data": [],
    }
    mcg_applicable = bool(mcg_result.get("applicable"))
    disposition_context = mcg_result.get("disposition_context") or {}

    chief_complaint = structured["chief_complaint_generated"]
    if not revised_hpi:
        default_result["factual_consistency"] = "fail"
        default_result["is_pass"] = False
        default_result["needs_regeneration"] = True
        default_result["missing_key_facts"] = ["Revised HPI text is empty."]
        default_result["revision_instructions"] = [
            "Write a concise Revised HPI using only the structured facts."
        ]
        return default_result

    normalized = default_result
    normalized["mcg_admission_check"] = {
        "applicable": mcg_applicable,
        "matched_criteria": [item["id"] for item in mcg_result.get("matched_criteria", [])],
        "support_level": mcg_result.get("support_level", "low"),
        "supported": bool(mcg_result.get("supported")),
    }

    if chief_complaint and chief_complaint.lower() not in revised_hpi.lower():
        chief_complaint_review_message = (
            "Chief complaint is present but generic."
            if _chief_complaint_is_generic(chief_complaint)
            else "Chief complaint should be stated more explicitly."
        )
        normalized["missing_key_facts"] = list(
            dict.fromkeys(
                [*normalized["missing_key_facts"], chief_complaint_review_message]
            )
        )

    sparse_structured = _structured_data_is_sparse(structured)
    if sparse_structured and structured["disposition_generated"] != "Unknown":
        normalized["disposition_consistency"] = "fail"
        normalized["disposition_inconsistencies"] = list(
            dict.fromkeys(
                [
                    *normalized["disposition_inconsistencies"],
                    "Disposition is more specific than the sparse supporting evidence allows.",
                ]
            )
        )
        normalized["revision_instructions"] = list(
            dict.fromkeys(
                [
                    *normalized["revision_instructions"],
                    "Avoid overstating a specific disposition when supporting facts are sparse.",
                ]
            )
        )

    if sparse_structured and not structured["uncertainties_generated"]:
        normalized["missing_key_facts"] = list(
            dict.fromkeys(
                [
                    *normalized["missing_key_facts"],
                    "Structured output should acknowledge uncertainty when facts are sparse.",
                ]
            )
        )

    if len(revised_hpi) < 80:
        normalized["revision_instructions"] = list(
            dict.fromkeys(
                [
                    *normalized["revision_instructions"],
                    "Expand the Revised HPI slightly while remaining fact-bound and concise.",
                ]
            )
        )

    normalized_structured = normalize_generated_structured_input(structured)
    evidence_text = " ".join(
        [
            normalized_structured["chief_complaint_generated"],
            normalized_structured["hpi_summary_generated"],
            " ".join(normalized_structured["key_findings_generated"]),
            " ".join(normalized_structured["suspected_conditions_generated"]),
            " ".join(normalized_structured["uncertainties_generated"]),
        ]
    ).lower()
    revised_lower = revised_hpi.lower()

    unsupported_phrase_map = {
        "diabetic ketoacidosis": ["dka", "ketoacidosis"],
        "sepsis": ["sepsis"],
        "severe dehydration": ["persistent dehydration", "dehydration"],
        "stroke": ["stroke"],
        "pancreatitis": ["pancreatitis"],
        "myocardial infarction": ["myocardial infarction", "mi"],
    }
    for narrative_phrase, evidence_phrases in unsupported_phrase_map.items():
        if narrative_phrase in revised_lower and not _contains_phrase(evidence_text, evidence_phrases):
            normalized["unsupported_claims"] = list(
                dict.fromkeys(
                    [
                        *normalized["unsupported_claims"],
                        f"Narrative states {narrative_phrase}, but supporting evidence is not present.",
                    ]
                )
            )
            normalized["factual_consistency"] = "fail"

    for matched in mcg_result.get("matched_criteria", []):
        if mcg_applicable and matched["confidence"] in {"moderate", "high"}:
            mentioned = False
            for signal in matched.get("matched_signals", []):
                signal_tokens = [token for token in signal.lower().replace("/", " ").split() if len(token) > 3]
                if any(token in revised_lower for token in signal_tokens):
                    mentioned = True
                    break
            if not mentioned:
                normalized["criteria_alignment_issues"] = list(
                    dict.fromkeys(
                        [
                            *normalized["criteria_alignment_issues"],
                            f"Matched criterion '{matched['id']}' is not clearly reflected in the Revised HPI.",
                        ]
                    )
                )

    if mcg_applicable:
        normalized["missing_required_data_for_confident_interpretation"] = list(
            dict.fromkeys(
                [
                    *normalized["missing_required_data_for_confident_interpretation"],
                    *safe_string_list((mcg_result or {}).get("missing_data")),
                ]
            )
        )

    support_level = mcg_result.get("support_level", "low")
    disposition = structured["disposition_generated"]
    if mcg_applicable and support_level == "high" and disposition != "Admit":
        normalized["disposition_consistency"] = "fail"
        normalized["disposition_inconsistencies"] = list(
            dict.fromkeys(
                [
                    *normalized["disposition_inconsistencies"],
                    "Strong admission-supporting criteria are present, but disposition is not Admit.",
                ]
            )
        )
    if mcg_applicable and support_level == "low" and disposition == "Admit":
        if disposition_context.get("requires_admit_with_monitoring"):
            if not _contains_phrase(
                revised_lower,
                [
                    "monitoring",
                    "ongoing evaluation",
                    "reassessment",
                    "incomplete evaluation",
                    "pending",
                    "clarify severity",
                ],
            ):
                normalized["disposition_consistency"] = "fail"
                normalized["disposition_inconsistencies"] = list(
                    dict.fromkeys(
                        [
                            *normalized["disposition_inconsistencies"],
                            "Admission disposition should more clearly explain the need for ongoing monitoring or incomplete evaluation when condition-specific criteria support is limited.",
                        ]
                    )
                )
        else:
            normalized["disposition_consistency"] = "fail"
            normalized["disposition_inconsistencies"] = list(
                dict.fromkeys(
                    [
                        *normalized["disposition_inconsistencies"],
                        "Admission disposition should more clearly explain the need for ongoing monitoring or incomplete evaluation when condition-specific criteria support is limited.",
                    ]
                )
            )

    if mcg_applicable and mcg_result.get("supported") and not _contains_phrase(
        revised_lower,
        [
            "dehydration",
            "anion gap",
            "bicarbonate",
            "ketone",
            "uncontrolled glucose",
            "poor oral intake",
            "sepsis",
            "infection",
            "monitoring",
            "treatment",
        ],
    ):
        normalized["criteria_alignment_issues"] = list(
            dict.fromkeys(
                [
                    *normalized["criteria_alignment_issues"],
                    "Admission-supporting criteria are matched, but the narrative does not clearly reflect that evidence.",
                ]
            )
        )
    if mcg_applicable and support_level == "low" and disposition == "Admit":
        if not _contains_phrase(
            revised_lower,
            [
                "monitoring",
                "ongoing evaluation",
                "reassessment",
                "observation",
                "incomplete evaluation",
                "pending",
            ],
        ):
            normalized["missing_key_facts"] = list(
                dict.fromkeys(
                    [
                        *normalized["missing_key_facts"],
                        "Narrative should explain why admission is still needed despite limited condition-specific support.",
                    ]
                )
            )
            normalized["revision_instructions"] = list(
                dict.fromkeys(
                    [
                        *normalized["revision_instructions"],
                        "If admission remains appropriate with limited condition-specific support, explain the need for ongoing monitoring or incomplete evaluation without overstating severity.",
                    ]
                )
            )

    normalized["missing_key_facts"] = list(dict.fromkeys(normalized["missing_key_facts"]))
    normalized["unsupported_claims"] = list(dict.fromkeys(normalized["unsupported_claims"]))
    normalized["disposition_inconsistencies"] = list(
        dict.fromkeys(normalized["disposition_inconsistencies"])
    )
    normalized["criteria_alignment_issues"] = list(
        dict.fromkeys(normalized["criteria_alignment_issues"])
    )
    normalized["missing_required_data_for_confident_interpretation"] = list(
        dict.fromkeys(normalized["missing_required_data_for_confident_interpretation"])
    )

    if normalized["unsupported_claims"]:
        normalized["revision_instructions"] = list(
            dict.fromkeys(
                [
                    *normalized["revision_instructions"],
                    "Remove unsupported diagnoses or severity statements that are not grounded in the evidence.",
                ]
            )
        )
    if normalized["criteria_alignment_issues"]:
        normalized["revision_instructions"] = list(
            dict.fromkeys(
                [
                    *normalized["revision_instructions"],
                    "Explicitly reflect matched admission-supporting evidence when it is present.",
                ]
            )
        )
    if normalized["missing_required_data_for_confident_interpretation"]:
        normalized["revision_instructions"] = list(
            dict.fromkeys(
                [
                    *normalized["revision_instructions"],
                    "Preserve uncertainty where required data are missing instead of overcalling the diagnosis or admission need.",
                ]
            )
        )

    return _apply_verification_decision(normalized)


def verification_to_warnings(verification: dict) -> list[str]:
    verification = _normalize_verification_result(verification)
    warnings = []

    warnings.extend(verification["unsupported_claims"])
    warnings.extend(verification["missing_key_facts"])
    warnings.extend(verification["disposition_inconsistencies"])
    warnings.extend(verification["criteria_alignment_issues"])
    warnings.extend(verification["missing_required_data_for_confident_interpretation"])

    if verification["factual_consistency"] == "fail":
        warnings.append("Revised HPI may not be fully factually consistent.")

    if verification["disposition_consistency"] == "fail":
        warnings.append("Revised HPI may not align with the stated disposition.")

    if verification["needs_regeneration"]:
        warnings.append("Revised HPI may need regeneration.")

    return list(dict.fromkeys(warnings))
