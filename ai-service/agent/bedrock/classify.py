import os
from typing import Literal

from pydantic import BaseModel

from agent.bedrock.converse import converse

PROMPT = """Classify this document as exactly one of:
Identity Document
Claim Form
Policy Document
Customer Correspondence
Supporting Evidence
Respond with JSON only, no markdown:
{"document_type": "<one of the labels above>"}
Use Supporting Evidence when it is none of the other four."""

DocumentType = Literal[
    "Identity Document",
    "Claim Form",
    "Policy Document",
    "Customer Correspondence",
    "Supporting Evidence",
]


class DocumentKind(BaseModel):
    document_type: DocumentType


def classify_document(text: str) -> DocumentKind:
    reply = converse(
        os.environ["BEDROCK_CLASSIFY_MODEL_ID"],
        [{"text": PROMPT}, {"text": text}],
    )
    return DocumentKind.model_validate_json(reply)
