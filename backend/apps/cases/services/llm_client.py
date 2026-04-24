import os
from abc import ABC, abstractmethod


class LLMServiceError(Exception):
    pass


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_structured_json(self, *, model, system_prompt, user_prompt, schema):
        raise NotImplementedError

    @abstractmethod
    def generate_text(self, *, model, system_prompt, user_prompt):
        raise NotImplementedError


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMServiceError(
                "The openai package is not installed. Add it to the backend environment first."
            ) from exc

        self.client = OpenAI(api_key=api_key)

    def generate_structured_json(self, *, model, system_prompt, user_prompt, schema):
        try:
            return self.client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema["name"],
                        "strict": schema["strict"],
                        "schema": schema["schema"],
                    }
                },
            )
        except Exception as exc:
            raise LLMServiceError(f"OpenAI structured extraction failed: {exc}") from exc

    def generate_text(self, *, model, system_prompt, user_prompt):
        try:
            return self.client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:
            raise LLMServiceError(f"OpenAI text generation failed: {exc}") from exc


def get_llm_settings():
    provider_name = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    model = os.getenv("OPENAI_MODEL")

    if not model:
        raise LLMServiceError("OPENAI_MODEL is not configured.")

    return {
        "provider": provider_name,
        "model": model,
    }


def get_llm_provider():
    settings = get_llm_settings()
    provider_name = settings["provider"]

    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMServiceError("OPENAI_API_KEY is not configured.")
        return OpenAIProvider(api_key), settings["model"]

    raise LLMServiceError(
        f"Unsupported LLM provider '{provider_name}'. "
        "Configure LLM_PROVIDER=openai for the current demo."
    )
