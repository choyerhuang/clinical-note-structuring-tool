import re


_REDACTION_LABELS = {
    "SSN": "[REDACTED_SSN]",
    "PHONE": "[REDACTED_PHONE]",
    "EMAIL": "[REDACTED_EMAIL]",
    "DOB": "[REDACTED_DOB]",
    "MRN": "[REDACTED_MRN]",
    "PATIENT_ID": "[REDACTED_PATIENT_ID]",
    "NAME": "[REDACTED_NAME]",
    "ADDRESS": "[REDACTED_ADDRESS]",
}

_LABELED_DOB_PATTERN = re.compile(
    r"(?im)\b((?:dob|date\s+of\s+birth|born\s+on)\s*:\s*)([^\n]+)"
)
_INLINE_BORN_ON_PATTERN = re.compile(
    r"(?im)\b(born\s+on\s+)(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b"
)
_EMAIL_PATTERN = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_PHONE_PATTERN = re.compile(
    r"(?x)"
    r"(?<!\w)"
    r"(?:\+?1[\s.-]?)?"
    r"(?:\(\d{3}\)|\d{3})"
    r"[\s.-]?\d{3}[\s.-]?\d{4}"
    r"(?!\w)"
)
_SSN_PATTERN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
_LABELED_SSN_DIGITS_PATTERN = re.compile(
    r"(?im)\b(ssn\s*:\s*)(\d{9})(?!\d)"
)
_LABELED_NAME_PATTERN = re.compile(
    r"(?im)\b((?:patient\s+name|pt\s+name|name)\s*:\s*)([^\n]+)"
)
_LABELED_ADDRESS_PATTERN = re.compile(
    r"(?im)\b((?:home\s+address|address)\s*:\s*)([^\n]+)"
)
_LABELED_MRN_PATTERN = re.compile(
    r"(?im)\b((?:mrn|medical\s+record\s+number)\s*:\s*)([A-Z0-9-]+)\b"
)
_LABELED_PATIENT_ID_PATTERN = re.compile(
    r"(?im)\b((?:patient\s+id)\s*:\s*)([A-Z0-9-]+)\b"
)
_LABELED_PHONE_PATTERN = re.compile(
    r"(?im)\b((?:phone|phone\s+number|mobile|cell|contact\s+number)\s*:\s*)([^\n]+)"
)


def redact_phi(text: str) -> str:
    normalized_text = text if isinstance(text, str) else ""
    if not normalized_text:
        return normalized_text

    redacted_text = normalized_text

    redacted_text = _LABELED_NAME_PATTERN.sub(
        lambda match: f"{match.group(1)}{_REDACTION_LABELS['NAME']}",
        redacted_text,
    )
    redacted_text = _LABELED_ADDRESS_PATTERN.sub(
        lambda match: f"{match.group(1)}{_REDACTION_LABELS['ADDRESS']}",
        redacted_text,
    )
    redacted_text = _LABELED_DOB_PATTERN.sub(
        lambda match: f"{match.group(1)}{_REDACTION_LABELS['DOB']}",
        redacted_text,
    )
    redacted_text = _INLINE_BORN_ON_PATTERN.sub(
        lambda match: f"{match.group(1)}{_REDACTION_LABELS['DOB']}",
        redacted_text,
    )
    redacted_text = _LABELED_MRN_PATTERN.sub(
        lambda match: f"{match.group(1)}{_REDACTION_LABELS['MRN']}",
        redacted_text,
    )
    redacted_text = _LABELED_PATIENT_ID_PATTERN.sub(
        lambda match: f"{match.group(1)}{_REDACTION_LABELS['PATIENT_ID']}",
        redacted_text,
    )
    redacted_text = _LABELED_PHONE_PATTERN.sub(
        lambda match: f"{match.group(1)}{_REDACTION_LABELS['PHONE']}",
        redacted_text,
    )
    redacted_text = _LABELED_SSN_DIGITS_PATTERN.sub(
        lambda match: f"{match.group(1)}{_REDACTION_LABELS['SSN']}",
        redacted_text,
    )

    redacted_text = _EMAIL_PATTERN.sub(_REDACTION_LABELS["EMAIL"], redacted_text)
    redacted_text = _PHONE_PATTERN.sub(_REDACTION_LABELS["PHONE"], redacted_text)
    redacted_text = _SSN_PATTERN.sub(_REDACTION_LABELS["SSN"], redacted_text)

    return redacted_text
