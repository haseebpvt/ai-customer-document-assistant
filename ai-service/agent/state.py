from typing import Literal, NotRequired, TypedDict

from agent.bedrock.classify import DocumentType


class State(TypedDict):
    s3_key: str
    file_format: NotRequired[Literal["image", "pdf", "docx"]]
    content: NotRequired[str]
    status: NotRequired[Literal["extracted", "unreadable"]]
    document_type: NotRequired[DocumentType]
