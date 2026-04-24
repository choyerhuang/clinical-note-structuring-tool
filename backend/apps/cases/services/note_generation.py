import json

from apps.cases.models import Disposition
from apps.cases.services.llm_client import LLMServiceError

STRUCTURED_OUTPUT_SCHEMA = {
    "name": "clinical_note_structured_output",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "chief_complaint": {"type": "string"},
            "hpi_summary": {"type": "string"},
            "key_findings": {
                "type": "array",
                "items": {"type": "string"},
            },
            "suspected_conditions": {
                "type": "array",
                "items": {"type": "string"},
            },
            "disposition_recommendation": {
                "type": "string",
                "enum": [
                    Disposition.ADMIT.value,
                    Disposition.OBSERVE.value,
                    Disposition.DISCHARGE.value,
                    Disposition.UNKNOWN.value,
                ],
            },
            "uncertainties": {
                "type": "array",
                "items": {"type": "string"},
            },
            "source_support": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "chief_complaint",
            "hpi_summary",
            "key_findings",
            "suspected_conditions",
            "disposition_recommendation",
            "uncertainties",
            "source_support",
        ],
        "additionalProperties": False,
    },
}

REVISED_HPI_VERIFICATION_SCHEMA = {
    "name": "revised_hpi_verification",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "factual_consistency": {
                "type": "string",
                "enum": ["pass", "fail"],
            },
            "unsupported_claims": {
                "type": "array",
                "items": {"type": "string"},
            },
            "missing_key_facts": {
                "type": "array",
                "items": {"type": "string"},
            },
            "disposition_consistency": {
                "type": "string",
                "enum": ["pass", "fail"],
            },
            "needs_regeneration": {"type": "boolean"},
            "revision_instructions": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "factual_consistency",
            "unsupported_claims",
            "missing_key_facts",
            "disposition_consistency",
            "needs_regeneration",
            "revision_instructions",
        ],
        "additionalProperties": False,
    },
}

VALID_DISPOSITIONS = {
    Disposition.ADMIT.value,
    Disposition.OBSERVE.value,
    Disposition.DISCHARGE.value,
    Disposition.UNKNOWN.value,
}


def safe_text(value):
    if isinstance(value, str):
        return value.strip()
    return ""


def safe_string_list(value):
    if not isinstance(value, list):
        return []

    normalized_items = []
    for item in value:
        if isinstance(item, str):
            cleaned_item = item.strip()
            if cleaned_item:
                normalized_items.append(cleaned_item)

    return normalized_items


def normalize_disposition(value):
    normalized_value = safe_text(value)
    if normalized_value in VALID_DISPOSITIONS:
        return normalized_value
    return Disposition.UNKNOWN.value


def truncate_for_error(raw_value, limit=200):
    if raw_value is None:
        return "<empty>"

    raw_text = str(raw_value).strip()
    if not raw_text:
        return "<empty>"

    if len(raw_text) <= limit:
        return raw_text
    return f"{raw_text[:limit]}..."


def parse_json_string(raw_text, context_label):
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        snippet = truncate_for_error(raw_text)
        raise LLMServiceError(
            f"LLM returned {context_label} that was not valid JSON. "
            f"Raw response snippet: {snippet}"
        ) from exc


def extract_json_from_output_items(response, context_label):
    output_items = getattr(response, "output", None) or []

    for item in output_items:
        content_items = getattr(item, "content", None) or []
        for content in content_items:
            parsed = getattr(content, "parsed", None)
            if parsed is not None:
                if isinstance(parsed, dict):
                    return parsed
                if isinstance(parsed, str):
                    return parse_json_string(parsed, context_label)

            text_value = getattr(content, "text", None)
            if text_value:
                return parse_json_string(text_value, context_label)

            for attr_name in ("json", "arguments"):
                attr_value = getattr(content, attr_name, None)
                if attr_value:
                    if isinstance(attr_value, dict):
                        return attr_value
                    if isinstance(attr_value, str):
                        return parse_json_string(attr_value, context_label)

        for attr_name in ("parsed", "text"):
            attr_value = getattr(item, attr_name, None)
            if attr_value:
                if isinstance(attr_value, dict):
                    return attr_value
                if isinstance(attr_value, str):
                    return parse_json_string(attr_value, context_label)

    return None


def extract_response_json(response, context_label):
    parsed_output = extract_json_from_output_items(response, context_label)
    if parsed_output is not None:
        return parsed_output

    output_text = getattr(response, "output_text", None)
    if output_text:
        return parse_json_string(output_text, context_label)

    raise LLMServiceError(f"LLM returned no {context_label}.")


def extract_text_response(response):
    output_text = getattr(response, "output_text", None)
    if output_text:
        cleaned_text = output_text.strip()
        if cleaned_text:
            return cleaned_text

    output_items = getattr(response, "output", None) or []
    for item in output_items:
        content_items = getattr(item, "content", None) or []
        for content in content_items:
            text_value = getattr(content, "text", None)
            if isinstance(text_value, str) and text_value.strip():
                return text_value.strip()

        text_value = getattr(item, "text", None)
        if isinstance(text_value, str) and text_value.strip():
            return text_value.strip()

    raise LLMServiceError("LLM returned no revised HPI text output.")


def normalize_extracted_structured_output(raw_output):
    if not isinstance(raw_output, dict):
        raw_output = {}

    return {
        "chief_complaint_generated": safe_text(raw_output.get("chief_complaint")),
        "hpi_summary_generated": safe_text(raw_output.get("hpi_summary")),
        "key_findings_generated": safe_string_list(raw_output.get("key_findings")),
        "suspected_conditions_generated": safe_string_list(
            raw_output.get("suspected_conditions")
        ),
        "disposition_generated": normalize_disposition(
            raw_output.get("disposition_recommendation")
        ),
        "uncertainties_generated": safe_string_list(raw_output.get("uncertainties")),
        "source_support": safe_string_list(raw_output.get("source_support")),
    }


def normalize_generated_structured_input(structured):
    return {
        "chief_complaint_generated": safe_text(
            (structured or {}).get("chief_complaint_generated")
        ),
        "hpi_summary_generated": safe_text(
            (structured or {}).get("hpi_summary_generated")
        ),
        "key_findings_generated": safe_string_list(
            (structured or {}).get("key_findings_generated")
        ),
        "suspected_conditions_generated": safe_string_list(
            (structured or {}).get("suspected_conditions_generated")
        ),
        "disposition_generated": normalize_disposition(
            (structured or {}).get("disposition_generated")
        ),
        "uncertainties_generated": safe_string_list(
            (structured or {}).get("uncertainties_generated")
        ),
        "source_support": safe_string_list((structured or {}).get("source_support")),
    }
