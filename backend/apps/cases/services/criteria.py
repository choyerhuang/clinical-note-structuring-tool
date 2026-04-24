import re

from apps.cases.services.mcg_rules import DIABETES_MCG
from apps.cases.services.note_generation import normalize_generated_structured_input, safe_text


def _build_search_text(structured_output: dict, source_text: str | None) -> str:
    normalized_structured = normalize_generated_structured_input(structured_output)
    segments = [
        safe_text(source_text),
        normalized_structured["chief_complaint_generated"],
        normalized_structured["hpi_summary_generated"],
        " ".join(normalized_structured["key_findings_generated"]),
        " ".join(normalized_structured["suspected_conditions_generated"]),
        " ".join(normalized_structured["uncertainties_generated"]),
        " ".join(normalized_structured["source_support"]),
    ]
    return "\n".join(part for part in segments if part).lower()


def _extract_numeric_value(text: str, patterns: list[str]) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (TypeError, ValueError):
                return None
    return None


def _find_glucose(text: str) -> float | None:
    return _extract_numeric_value(
        text,
        [
            r"glucose\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)",
            r"blood sugar\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)",
            r"bg\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)",
            r"fsbs\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)",
        ],
    )


def _find_anion_gap(text: str) -> float | None:
    return _extract_numeric_value(
        text,
        [
            r"anion gap\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)",
            r"ag\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)",
        ],
    )


def _find_bicarbonate(text: str) -> float | None:
    return _extract_numeric_value(
        text,
        [
            r"bicarbonate\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)",
            r"bicarb\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)",
            r"hco3\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)",
        ],
    )


def _find_ph(text: str) -> float | None:
    return _extract_numeric_value(
        text,
        [
            r"\bpH\s*(?:of|is|=|:)?\s*(7\.\d+)",
            r"\bvenous pH\s*(?:of|is|=|:)?\s*(7\.\d+)",
            r"\barterial pH\s*(?:of|is|=|:)?\s*(7\.\d+)",
        ],
    )


def _find_osmolality(text: str) -> float | None:
    return _extract_numeric_value(
        text,
        [
            r"osmolality\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)",
            r"serum osmolality\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)",
        ],
    )


def _contains_any(text: str, phrases: list[str]) -> str | None:
    for phrase in phrases:
        if phrase in text:
            return phrase
    return None


def _contains_non_negated_phrase(text: str, phrase: str) -> bool:
    normalized_text = f" {text.lower()} "
    normalized_phrase = phrase.lower()
    if f" {normalized_phrase} " not in normalized_text:
        return False

    negation_prefixes = [
        f" no {normalized_phrase} ",
        f" without {normalized_phrase} ",
        f" denies {normalized_phrase} ",
        f" not {normalized_phrase} ",
    ]
    return not any(prefix in normalized_text for prefix in negation_prefixes)


def _contains_any_non_negated(text: str, phrases: list[str]) -> str | None:
    for phrase in phrases:
        if _contains_non_negated_phrase(text, phrase):
            return phrase
    return None


def _diabetes_relevant(text: str) -> bool:
    negative_diabetes_phrases = [
        "without diabetes",
        "without diabetes history",
        "no diabetes",
        "no history of diabetes",
        "denies diabetes",
        "non-diabetic",
        "nondiabetic",
    ]
    if _contains_any(text, negative_diabetes_phrases):
        return False

    return bool(
        _contains_any(
            text,
            [
                "diabetes",
                "diabetic",
                "dka",
                "ketoacidosis",
                "hyperglycemia",
                "glucose",
                "ketone",
                "insulin",
                "hhs",
            ],
        )
    )


def is_diabetes_mcg_applicable(
    structured_output: dict,
    source_text: str | None = None,
    condition_hint: str | None = None,
) -> bool:
    search_text = _build_search_text(structured_output, source_text)
    normalized_condition_hint = safe_text(condition_hint).lower()
    return normalized_condition_hint == "diabetes" or _diabetes_relevant(search_text)


def _evidence_string(label: str, value: float | str) -> str:
    if isinstance(value, float):
        if value.is_integer():
            value = int(value)
    return f"{label} {value}"


def has_numeric_or_text_evidence(
    structured_output: dict,
    source_text: str | None,
    signal_name: str,
) -> bool:
    search_text = _build_search_text(structured_output, source_text)
    normalized_signal = safe_text(signal_name).lower()

    if "glucose" in normalized_signal or "blood sugar" in normalized_signal:
        return _find_glucose(search_text) is not None or _contains_any(
            search_text,
            [
                "hyperglycemia",
                "markedly elevated glucose",
                "markedly elevated blood sugar",
                "severely elevated glucose",
                "severely elevated blood sugar",
                "elevated glucose",
                "elevated blood sugar",
                "glucose remains elevated",
                "glucose remained uncontrolled",
                "persistent hyperglycemia",
                "blood sugar elevated",
            ],
        ) is not None
    if "bicarbonate" in normalized_signal or "bicarb" in normalized_signal or "hco3" in normalized_signal:
        return _find_bicarbonate(search_text) is not None
    if normalized_signal == "ph" or "ph" in normalized_signal:
        return _find_ph(search_text) is not None
    if "anion gap" in normalized_signal:
        return _find_anion_gap(search_text) is not None or _contains_any(
            search_text,
            [
                "elevated anion gap",
                "anion gap elevated",
                "wide anion gap",
            ],
        ) is not None
    if "osmolality" in normalized_signal:
        return _find_osmolality(search_text) is not None
    if "ketone" in normalized_signal:
        return _contains_any(
            search_text,
            [
                "ketonemia",
                "ketonuria",
                "ketones present",
                "ketone positive",
                "positive ketones",
                "beta-hydroxybutyrate",
            ],
        ) is not None
    if normalized_signal == "response to treatment":
        return _contains_any(
            search_text,
            [
                "despite insulin",
                "after treatment",
                "after fluids",
                "after iv fluids",
                "after initial management",
                "not improved after treatment",
                "symptoms not improved significantly",
                "glucose remains elevated after treatment",
                "persistent hyperglycemia despite insulin",
            ],
        ) is not None
    if normalized_signal == "post-treatment reassessment":
        return _contains_any(
            search_text,
            [
                "after treatment",
                "after initial management",
                "after insulin",
                "after iv fluids",
                "post-treatment",
                "reassessment",
                "remained uncontrolled after treatment",
            ],
        ) is not None
    return False


def _has_any_phrases(text: str, phrases: list[str]) -> bool:
    return _contains_any(text, phrases) is not None


def _has_ongoing_diabetes_symptoms(text: str) -> bool:
    return _has_any_phrases(
        text,
        [
            "persistent symptoms",
            "weakness",
            "persistent weakness",
            "fatigue",
            "persistent fatigue",
            "poor oral intake",
            "cannot tolerate oral intake",
            "persistent polyuria",
            "ongoing polyuria",
            "polyuria",
            "persistent hyperglycemia",
            "hyperglycemia",
            "glucose remains elevated",
            "glucose remained uncontrolled",
            "persistent dehydration",
            "dehydration persists",
            "dehydration despite fluids",
        ],
    )


def filter_missing_data_against_evidence(
    structured_output: dict,
    missing_data: list[str] | None,
    source_text: str | None = None,
) -> list[str]:
    filtered_items = []
    for item in missing_data or []:
        cleaned_item = safe_text(item)
        if not cleaned_item:
            continue
        if has_numeric_or_text_evidence(structured_output, source_text, cleaned_item):
            continue
        if cleaned_item not in filtered_items:
            filtered_items.append(cleaned_item)
    return filtered_items


def _match_diabetic_ketoacidosis(text: str) -> tuple[list[str], list[str], str]:
    matches: list[str] = []
    missing_data: list[str] = []

    glucose = _find_glucose(text)
    if glucose is not None and glucose >= 200:
        matches.append(_evidence_string("glucose", glucose) + " mg/dL")
    elif glucose is None:
        missing_data.append("glucose")

    ketone_phrase = _contains_any(text, ["ketonemia", "ketonuria", "ketones present", "ketone positive", "positive ketones"])
    if ketone_phrase:
        matches.append(ketone_phrase)
    else:
        missing_data.append("ketone level")

    acid_base_matches = 0
    ph_value = _find_ph(text)
    if ph_value is not None and ph_value < 7.30:
        acid_base_matches += 1
        matches.append(_evidence_string("pH", ph_value))
    elif ph_value is None:
        missing_data.append("pH")

    bicarbonate = _find_bicarbonate(text)
    if bicarbonate is not None and bicarbonate <= 18:
        acid_base_matches += 1
        matches.append(_evidence_string("bicarbonate", bicarbonate))
    elif bicarbonate is None:
        missing_data.append("bicarbonate")

    anion_gap = _find_anion_gap(text)
    if anion_gap is not None and anion_gap > 12:
        acid_base_matches += 1
        matches.append(_evidence_string("anion gap", anion_gap))
    elif anion_gap is None:
        missing_data.append("anion gap")

    if glucose is not None and glucose >= 200 and ketone_phrase and acid_base_matches >= 1:
        confidence = "high" if acid_base_matches >= 2 else "moderate"
        return matches, list(dict.fromkeys(missing_data)), confidence

    return [], list(dict.fromkeys(missing_data)), "low"


def _match_severe_dka_or_instability(text: str) -> tuple[list[str], list[str], str]:
    matches: list[str] = []
    missing_data: list[str] = []

    ph_value = _find_ph(text)
    if ph_value is not None and ph_value <= 7.25:
        matches.append(_evidence_string("pH", ph_value))
    elif ph_value is None:
        missing_data.append("pH")

    bicarbonate = _find_bicarbonate(text)
    if bicarbonate is not None and bicarbonate < 15:
        matches.append(_evidence_string("bicarbonate", bicarbonate))
    elif bicarbonate is None:
        missing_data.append("bicarbonate")

    for phrase in [
        "hypotension",
        "altered mental status",
        "confused",
        "persistent dehydration",
        "electrolyte abnormality",
        "cannot tolerate oral intake",
        "poor oral intake",
        "acute kidney injury",
    ]:
        if phrase in text:
            matches.append(phrase)

    unique_matches = list(dict.fromkeys(matches))
    if len(unique_matches) >= 2:
        confidence = "high" if len(unique_matches) >= 3 else "moderate"
        return unique_matches, list(dict.fromkeys(missing_data)), confidence

    return [], list(dict.fromkeys(missing_data)), "low"


def _match_hhs(text: str) -> tuple[list[str], list[str], str]:
    matches: list[str] = []
    missing_data: list[str] = []

    glucose = _find_glucose(text)
    if glucose is not None and glucose > 600:
        matches.append(_evidence_string("glucose", glucose) + " mg/dL")
    elif glucose is None:
        missing_data.append("glucose")

    osmolality = _find_osmolality(text)
    if osmolality is not None and osmolality > 320:
        matches.append(_evidence_string("serum osmolality", osmolality) + " mOsm/kg")
    elif osmolality is None:
        missing_data.append("serum osmolality")

    if len(matches) == 2:
        return matches, list(dict.fromkeys(missing_data)), "high"
    return [], list(dict.fromkeys(missing_data)), "low"


def _match_by_keywords(
    text: str,
    phrases: list[str],
    minimum_matches: int,
    missing_data: list[str] | None = None,
) -> tuple[list[str], list[str], str]:
    matches = []
    for phrase in phrases:
        if _contains_non_negated_phrase(text, phrase):
            matches.append(phrase)

    unique_matches = list(dict.fromkeys(matches))
    if len(unique_matches) >= minimum_matches:
        confidence = "high" if len(unique_matches) >= minimum_matches + 1 else "moderate"
        return unique_matches, missing_data or [], confidence
    return [], missing_data or [], "low"


def _match_severe_hyperglycemia(text: str) -> tuple[list[str], list[str], str]:
    matched_signals, _, confidence = _match_by_keywords(
        text,
        [
            "hemodynamic instability",
            "altered mental status",
            "persistent dehydration",
            "dehydration",
            "electrolyte abnormality",
            "cannot maintain oral hydration",
            "poor oral intake",
            "glucose not controlled despite observation",
            "glucose remained uncontrolled",
            "glucose remains elevated after treatment",
            "persistent hyperglycemia despite insulin",
            "persistent hyperglycemia after treatment",
            "persistent hyperglycemia after insulin",
            "dehydration despite fluids",
            "symptoms unchanged after ed treatment",
            "symptoms unchanged after treatment",
            "no significant improvement after ed treatment",
            "no significant improvement after treatment",
            "persistent symptoms after treatment",
            "persistent symptoms despite treatment",
            "poor oral intake despite treatment",
            "persistent polyuria after treatment",
            "need for continued monitoring",
            "requires continued monitoring",
            "continued inpatient management",
            "requires ongoing treatment",
            "needs continued treatment",
        ],
        minimum_matches=2,
    )
    missing_data = []
    if not _contains_any(
        text,
        [
            "despite insulin",
            "after treatment",
            "after fluids",
            "after iv fluids",
            "after observation",
            "after initial management",
        ],
    ):
        missing_data.append("response to treatment")

    return matched_signals, missing_data, confidence


def _match_failed_observation_or_outpatient(text: str) -> tuple[list[str], list[str], str]:
    phrase_groups = {
        "persistent acidosis despite observation": [
            "persistent acidosis despite observation",
            "acidosis persists despite observation",
        ],
        "persistent dehydration": [
            "persistent dehydration",
            "dehydration persists",
            "dehydration despite fluids",
        ],
        "persistent electrolyte abnormality": [
            "persistent electrolyte abnormality",
            "electrolyte abnormality persists",
        ],
        "glucose not stabilized after treatment": [
            "glucose not stabilized after treatment",
            "glucose remained uncontrolled after treatment",
            "glucose remains elevated after treatment",
            "persistent hyperglycemia despite insulin",
            "persistent hyperglycemia after treatment",
            "persistent hyperglycemia after insulin",
        ],
        "failed initial management": [
            "persistent symptoms",
            "persistent symptoms after treatment",
            "persistent symptoms despite treatment",
            "not improved after treatment",
            "no improvement after prior treatment",
            "no improvement after earlier treatment",
            "no improvement after insulin",
            "no improvement after earlier insulin",
            "symptoms not improved significantly",
            "symptoms unchanged after ed treatment",
            "symptoms unchanged after treatment",
            "no significant improvement after ed treatment",
            "no significant improvement after treatment",
            "failed initial management",
            "persistent instability after ed treatment",
            "persistent instability after treatment",
        ],
        "ongoing symptom burden after treatment": [
            "poor oral intake despite treatment",
            "persistent weakness after treatment",
            "weakness persists after treatment",
            "persistent polyuria after treatment",
            "ongoing hyperglycemia after treatment",
            "dehydration persists after treatment",
        ],
        "continued monitoring or treatment required": [
            "need for continued monitoring",
            "requires continued monitoring",
            "continued inpatient management",
            "needs continued treatment",
            "requires ongoing treatment",
        ],
    }

    matches = []
    for label, phrases in phrase_groups.items():
        if _contains_any_non_negated(text, phrases):
            matches.append(label)

    unique_matches = list(dict.fromkeys(matches))
    missing_data = []
    if not any("after treatment" in match or "failed initial management" in match for match in unique_matches):
        missing_data.append("post-treatment reassessment")

    if unique_matches:
        confidence = "high" if len(unique_matches) >= 2 else "moderate"
        return unique_matches, missing_data, confidence

    return [], missing_data, "low"


def _has_explicit_treatment_failure_signal(matched_criteria: list[dict]) -> bool:
    explicit_signals = {
        "glucose not stabilized after treatment",
        "failed initial management",
        "continued monitoring or treatment required",
        "ongoing symptom burden after treatment",
        "persistent hyperglycemia despite insulin",
        "persistent hyperglycemia after treatment",
        "persistent hyperglycemia after insulin",
        "glucose remains elevated after treatment",
        "glucose remained uncontrolled after treatment",
        "no improvement after prior treatment",
        "no improvement after earlier treatment",
        "no improvement after insulin",
        "no improvement after earlier insulin",
        "symptoms unchanged after ed treatment",
        "symptoms unchanged after treatment",
        "no significant improvement after ed treatment",
        "no significant improvement after treatment",
    }
    for criterion in matched_criteria:
        for signal in criterion.get("matched_signals", []):
            if safe_text(signal).lower() in explicit_signals:
                return True
    return False


def _support_level_from_matches(matched_criteria: list[dict]) -> str:
    if not matched_criteria:
        return "low"
    if any(item["confidence"] == "high" for item in matched_criteria) or len(matched_criteria) >= 2:
        return "high"
    return "moderate"


def _criteria_summary(matched_criteria: list[dict], support_level: str, missing_data: list[str]) -> str:
    if not matched_criteria:
        if missing_data:
            return (
                "Diabetes-specific high-acuity admission support remains limited because "
                "key metabolic data are unavailable."
            )
        return "No diabetes-related admission criteria were matched from the available evidence."

    matched_ids = {item["id"] for item in matched_criteria}
    if matched_ids & {"failed_observation_or_outpatient", "severe_hyperglycemia"} and not (
        matched_ids & {"diabetic_ketoacidosis", "hyperosmolar_hyperglycemic_state"}
    ):
        if support_level == "high":
            return (
                "Admission is supported by persistent hyperglycemia, dehydration or ongoing "
                "instability after initial treatment, and the need for continued inpatient "
                "monitoring or management."
            )
        return (
            "Admission support is present based on persistent hyperglycemia, treatment "
            "failure, dehydration, or the need for continued monitoring and management."
        )

    descriptions = ", ".join(item["description"] for item in matched_criteria)
    if support_level == "high":
        return f"Admission is supported by {descriptions}."
    return f"Admission support is present but incomplete, based on {descriptions}."


def _has_explicit_inpatient_need(text: str) -> bool:
    return _contains_any(
        text,
        [
            "need for continued monitoring",
            "requires continued monitoring",
            "continued inpatient management",
            "needs continued treatment",
            "requires ongoing treatment",
            "ongoing monitoring",
            "incomplete evaluation",
            "workup remains incomplete",
            "pending reassessment",
            "need to clarify severity",
            "unable to manage outpatient",
            "cannot be managed outpatient",
            "failed outpatient management",
            "failed observation",
        ],
    ) is not None


def _is_mild_stable_hyperglycemia_case(text: str) -> bool:
    has_hyperglycemia = _contains_any(
        text,
        [
            "mild hyperglycemia",
            "glucose",
            "blood sugar",
            "hyperglycemia",
        ],
    ) is not None
    has_stability_markers = all(
        _contains_any(
            text,
            [phrase],
        )
        is not None
        for phrase in [
            "stable vital signs",
            "normal mental status",
            "no dehydration",
        ]
    )
    lacks_concerning_features = not any(
        _contains_non_negated_phrase(text, phrase)
        for phrase in [
            "persistent dehydration",
            "dehydration",
            "poor oral intake",
            "altered mental status",
            "hypotension",
            "persistent hyperglycemia despite insulin",
            "not improved after treatment",
            "symptoms not improved significantly",
            "continued monitoring",
            "continued inpatient management",
        ]
    )
    return has_hyperglycemia and has_stability_markers and lacks_concerning_features


def reconcile_diabetes_disposition(
    structured_output: dict,
    mcg_result: dict,
    source_text: str | None = None,
) -> tuple[dict, dict]:
    reconciled_structured = dict(structured_output or {})
    reconciled_mcg = dict(mcg_result or {})

    if not reconciled_mcg.get("applicable"):
        return reconciled_structured, reconciled_mcg

    disposition = safe_text(reconciled_structured.get("disposition_generated"))
    matched_ids = {item.get("id", "") for item in reconciled_mcg.get("matched_criteria", [])}
    treatment_failure_supported = bool(
        matched_ids & {"failed_observation_or_outpatient", "severe_hyperglycemia"}
    )
    explicit_treatment_failure = _has_explicit_treatment_failure_signal(
        reconciled_mcg.get("matched_criteria", [])
    )
    search_text = _build_search_text(reconciled_structured, source_text)

    if _is_mild_stable_hyperglycemia_case(search_text):
        reconciled_structured["disposition_generated"] = "Discharge"
        reconciled_mcg["mild_stable_outpatient_candidate"] = True
        reconciled_mcg["support_level"] = "low"
        reconciled_mcg["supported"] = False
        reconciled_mcg["criteria_summary"] = (
            "Admission support is low. The available evidence suggests mild hyperglycemia "
            "without instability or metabolic derangement, so inpatient-level care is not required."
        )
        reconciled_mcg["disposition_context"] = {
            "inpatient_level_care_not_required": True,
            "guidance": (
                "The available evidence suggests mild hyperglycemia without instability, "
                "metabolic derangement, dehydration, or concerning symptoms, so inpatient-level "
                "care is not required and discharge with outpatient follow-up is appropriate."
            ),
        }
        return reconciled_structured, reconciled_mcg

    if (
        disposition in {"Unknown", "Observe"}
        and treatment_failure_supported
        and explicit_treatment_failure
        and (
            safe_text(reconciled_mcg.get("support_level")) in {"moderate", "high"}
            or _has_ongoing_diabetes_symptoms(search_text)
        )
    ):
        reconciled_structured["disposition_generated"] = "Admit"
        reconciled_mcg["disposition_inferred_from_treatment_failure"] = True
        if safe_text(reconciled_mcg.get("support_level")) == "low":
            reconciled_mcg["support_level"] = "moderate"
            reconciled_mcg["supported"] = True
        reconciled_mcg["criteria_summary"] = (
            "Admission is indicated due to failure of lower-level care, persistent "
            "symptoms, and the need for continued inpatient monitoring and treatment."
        )
        reconciled_mcg["disposition_context"] = {
            "requires_admit_with_monitoring": True,
            "guidance": (
                "Admission is appropriate because symptoms and hyperglycemia have not "
                "improved after prior treatment, and the patient requires continued "
                "inpatient monitoring, glucose-directed management, hydration support, "
                "and reassessment."
            ),
        }
        return reconciled_structured, reconciled_mcg

    if disposition != "Admit":
        return reconciled_structured, reconciled_mcg

    if safe_text(reconciled_mcg.get("support_level")) != "low":
        return reconciled_structured, reconciled_mcg

    if _has_explicit_inpatient_need(search_text):
        reconciled_mcg["disposition_context"] = {
            "requires_admit_with_monitoring": True,
            "guidance": (
                "Admission remains appropriate because the workup is incomplete or still "
                "concerning, and the patient requires ongoing monitoring, reassessment, "
                "or treatment that cannot yet be stepped down."
            ),
        }
        return reconciled_structured, reconciled_mcg

    reconciled_structured["disposition_generated"] = "Observe"
    reconciled_mcg["disposition_adjusted_to_observe"] = True
    return reconciled_structured, reconciled_mcg


def match_mcg_criteria(
    structured_output: dict,
    source_text: str | None = None,
    condition_hint: str | None = None,
) -> dict:
    search_text = _build_search_text(structured_output, source_text)
    is_diabetes_context = is_diabetes_mcg_applicable(
        structured_output,
        source_text=source_text,
        condition_hint=condition_hint,
    )

    result = {
        "condition": DIABETES_MCG["condition"],
        "applicable": is_diabetes_context,
        "matched_criteria": [],
        "support_level": "low",
        "missing_data": [],
        "criteria_summary": "",
        "supported": False,
    }

    if not is_diabetes_context:
        return result

    matched_criteria = []
    missing_data: list[str] = []

    matcher_map = {
        "diabetic_ketoacidosis": _match_diabetic_ketoacidosis,
        "severe_dka_or_instability": _match_severe_dka_or_instability,
        "hyperosmolar_hyperglycemic_state": _match_hhs,
        "severe_hyperglycemia": _match_severe_hyperglycemia,
        "failed_observation_or_outpatient": lambda text: _match_by_keywords(
            text,
            [],
            minimum_matches=99,
        ),
        "underlying_condition_requires_inpatient": lambda text: _match_by_keywords(
            text,
            [
                "infection requiring iv treatment",
                "sepsis",
                "pancreatitis",
                "myocardial infarction",
                "stroke",
            ],
            minimum_matches=1,
        ),
        "diagnostic_or_management_uncertainty": lambda text: _match_by_keywords(
            text,
            [
                "unclear cause of dka",
                "newly diagnosed diabetes",
                "no established insulin regimen",
            ],
            minimum_matches=1,
        ),
        "special_population_risk": lambda text: _match_by_keywords(
            text,
            [
                "pregnancy",
                "chronic liver disease",
                "chronic kidney disease",
                "sglt2 inhibitor",
                "prolonged starvation",
                "alcohol use",
            ],
            minimum_matches=1,
        ),
    }

    for criterion in DIABETES_MCG["admission_criteria"]:
        if criterion["id"] == "failed_observation_or_outpatient":
            matched_signals, criterion_missing_data, confidence = _match_failed_observation_or_outpatient(search_text)
        else:
            matched_signals, criterion_missing_data, confidence = matcher_map[criterion["id"]](search_text)
        missing_data.extend(criterion_missing_data)
        if matched_signals:
            matched_criteria.append(
                {
                    "id": criterion["id"],
                    "description": criterion["description"],
                    "category": criterion["category"],
                    "matched_signals": matched_signals,
                    "confidence": confidence,
                }
            )

    support_level = _support_level_from_matches(matched_criteria)
    unique_missing_data = filter_missing_data_against_evidence(
        structured_output,
        list(dict.fromkeys(item for item in missing_data if item)),
        source_text=source_text,
    )
    result.update(
        {
            "matched_criteria": matched_criteria,
            "support_level": support_level,
            "missing_data": unique_missing_data,
            "criteria_summary": _criteria_summary(
                matched_criteria,
                support_level,
                unique_missing_data,
            ),
            "supported": support_level in {"moderate", "high"},
        }
    )

    return result
