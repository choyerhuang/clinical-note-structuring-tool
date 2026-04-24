from apps.cases.services.llm_client import get_llm_provider
from apps.cases.services.note_generation import (
    STRUCTURED_OUTPUT_SCHEMA,
    extract_response_json,
    normalize_extracted_structured_output,
)
from apps.cases.services.prompts import STRUCTURED_OUTPUT_PROMPT_TEMPLATE
from apps.cases.services.validators import validate_note_for_generation


def extract_structured_output(note: str) -> dict:
    validated_note = validate_note_for_generation(note)
    provider, model = get_llm_provider()
    response = provider.generate_structured_json(
        model=model,
        system_prompt=STRUCTURED_OUTPUT_PROMPT_TEMPLATE,
        user_prompt=(
            "Extract structured clinical note data from the following note:\n\n"
            f"{validated_note}"
        ),
        schema=STRUCTURED_OUTPUT_SCHEMA,
    )

    raw_output = extract_response_json(response, "structured extraction output")
    return normalize_extracted_structured_output(raw_output)
