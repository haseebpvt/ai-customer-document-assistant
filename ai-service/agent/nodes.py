from pathlib import Path
from zipfile import BadZipFile

from pypdf.errors import PdfReadError

from agent.bedrock.classify import classify_document
from agent.bedrock.extract import extract_image
from agent.bedrock.fields import SCHEMAS, extract_fields
from agent.bedrock.summary import summarize
from agent.files.documents import docx_text, pdf_text
from agent.files.s3 import download
from agent.state import State

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff"}
BEDROCK_FORMATS = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif", ".webp": "webp"}


def identify_file_node(state: State) -> dict:
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


def image_processing_node(state: State) -> dict:
    extension = Path(state["s3_key"]).suffix.lower()
    media_type = BEDROCK_FORMATS.get(extension)
    if media_type is None:
        raise ValueError(f"unsupported image type: {extension}")

    body = download(state["s3_key"])
    result = extract_image(body, media_type)
    if result.readable:
        return {"content": result.content, "status": "extracted"}
    return {"content": "", "status": "unreadable"}


def document_processing_node(state: State) -> dict:
    body = download(state["s3_key"])
    try:
        if state["file_format"] == "pdf":
            text = pdf_text(body)
        else:
            text = docx_text(body)
    except (PdfReadError, BadZipFile, ValueError):
        return {"content": "", "status": "unreadable"}
    if text.strip():
        return {"content": text, "status": "extracted"}
    return {"content": "", "status": "unreadable"}


def identify_document_node(state: State) -> dict:
    kind = classify_document(state["content"])
    return {"document_type": kind.document_type}


def extract_fields_node(state: State) -> dict:
    result = extract_fields(state["content"], state["document_type"])
    return {"fields": result.model_dump()}


def missing_fields_node(state: State) -> dict:
    model = SCHEMAS[state["document_type"]]
    values = state.get("fields") or {}
    missing = [
        name
        for name in model.model_fields
        if not (values.get(name) or "").strip()
    ]
    return {"missing_fields": missing}


def summary_node(state: State) -> dict:
    report = summarize(
        state["document_type"],
        state.get("fields") or {},
        state.get("missing_fields") or [],
    )
    return {"report": report}


def finalize_node(state: State) -> dict:
    return {}
