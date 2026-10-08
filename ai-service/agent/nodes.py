from pathlib import Path

from agent.state import State

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff"}


def identify_file(state: State) -> dict:
    extension = Path(state["s3_key"]).suffix.lower()
    if extension in IMAGE_EXTENSIONS:
        file_format = "image"
    elif extension == ".pdf":
        file_format = "pdf"
    elif extension == ".docx":
        file_format = "docx"
    else:
        raise ValueError(f"unsupported file type: {extension}")
    return {"file_format": file_format}


def image_processing(state: State) -> dict:
    return {}


def document_processing(state: State) -> dict:
    return {}
