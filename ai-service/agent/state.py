from typing import Literal, NotRequired, TypedDict

from agent.bedrock.classify import DocumentType


class State(TypedDict):
    document_id: str
    s3_key: str
    file_format: NotRequired[Literal["image", "pdf", "docx"]]
    content: NotRequired[str]
    status: NotRequired[Literal["extracted", "unreadable"]]
    document_type: NotRequired[DocumentType]
    fields: NotRequired[dict[str, str | None]]
    missing_fields: NotRequired[list[str]]
    report: NotRequired[str]
