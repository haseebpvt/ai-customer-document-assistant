from typing import Literal, NotRequired, TypedDict


class State(TypedDict):
    message: str
    s3_key: str
    file_format: NotRequired[Literal["image", "pdf", "docx"]]
