import json
import os

from pydantic import BaseModel

from agent.bedrock.classify import DocumentType
from agent.bedrock.converse import converse, json_object

PROMPT = """Write a short report of this document extraction.
Respond with JSON only, no markdown:
{"summary": "<one or two sentences>", "next_action": "<one recommendation>"}
Use only the fields given. Do not invent values.
The next action should say what to do about the missing fields.
If nothing is missing, set next_action to "Ready for review."
"""


class Report(BaseModel):
    summary: str
    next_action: str


def _text(names: list[str]) -> str:
    words = [name.replace("_", " ") for name in names]
    return ", ".join(words) if words else "None"


def _fields(fields: dict[str, str | None]) -> str:
    parts = [
        f"{name.replace('_', ' ')}: {value}"
        for name, value in fields.items()
        if (value or "").strip()
    ]
    return ", ".join(parts) if parts else "None"


def summarize(
    document_type: DocumentType,
    fields: dict[str, str | None],
    missing_fields: list[str],
) -> dict[str, str]:
    details = json.dumps(
        {
            "document_type": document_type,
            "fields": fields,
            "missing_fields": missing_fields,
        }
    )
    reply = converse(
        os.environ["BEDROCK_CLASSIFY_MODEL_ID"],
        [{"text": PROMPT}, {"text": details}],
    )
    text = Report.model_validate_json(json_object(reply))
    # Copy the fields here. The model only writes the two sentences, so it cannot invent a value.
    return {
        "summary": text.summary,
        "extracted_information": _fields(fields),
        "missing_information": _text(missing_fields),
        "next_action": text.next_action,
    }
