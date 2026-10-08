import json
import os

from agent.bedrock.classify import DocumentType
from agent.bedrock.converse import converse

PROMPT = """Write a short report of this document extraction.
Use only the fields given. Say which fields are missing. Do not invent values."""


def summarize(
    document_type: DocumentType,
    fields: dict[str, str | None],
    missing_fields: list[str],
) -> str:
    details = json.dumps(
        {
            "document_type": document_type,
            "fields": fields,
            "missing_fields": missing_fields,
        }
    )
    return converse(
        os.environ["BEDROCK_CLASSIFY_MODEL_ID"],
        [{"text": PROMPT}, {"text": details}],
    )
