from typing import Literal, NotRequired, TypedDict

from agent.bedrock.classify import DocumentType


class State(TypedDict):
    document_id: str
    s3_key: str
    file_format: NotRequired[Literal["image", "pdf", "docx"]]
    content: NotRequired[str]
    # extracted, unreadable, or unsupported. The row the UI polls uses queued, a node name, retrying, completed, or failed.
    status: NotRequired[Literal["extracted", "unreadable", "unsupported"]]
    # Set with unsupported. Shown to the user as the reason.
    error: NotRequired[str]
    document_type: NotRequired[DocumentType]
    fields: NotRequired[dict[str, str | None]]
    missing_fields: NotRequired[list[str]]
    # A sentence when the file could not be read. An object after a normal summary.
    report: NotRequired[str | dict[str, str]]
