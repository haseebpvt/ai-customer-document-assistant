from pathlib import Path
from zipfile import BadZipFile

from pypdf.errors import PdfReadError

from agent.bedrock.classify import classify_document
from agent.bedrock.extract import extract_image
from agent.bedrock.fields import SCHEMAS, extract_fields
from agent.bedrock.summary import summarize
from agent.files.documents import docx_text, pdf_text
from agent.files.s3 import download
from agent.progress import update_document
from agent.state import State

BEDROCK_FORMATS = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif", ".webp": "webp"}


def identify_file_node(state: State) -> dict:
    extension = Path(state["s3_key"]).suffix.lower()
    if extension in BEDROCK_FORMATS:
        file_format = "image"
    elif extension == ".pdf":
        file_format = "pdf"
    elif extension == ".docx":
        file_format = "docx"
    else:
        # A retry cannot fix this, so it is a result, not an exception.
        update_document(state["document_id"], status="identify_file_node")
        return {"status": "unsupported", "error": f"unsupported file type: {extension}"}
    update_document(state["document_id"], status="identify_file_node")
    return {"file_format": file_format}


def image_processing_node(state: State) -> dict:
    extension = Path(state["s3_key"]).suffix.lower()
    # Bedrock takes jpeg, png, gif, and webp. Anything else fails the run.
    media_type = BEDROCK_FORMATS.get(extension)
    if media_type is None:
        raise ValueError(f"unsupported image type: {extension}")

    body = download(state["s3_key"])
    result = extract_image(body, media_type)
    update_document(state["document_id"], status="image_processing_node")
    if result.readable:
        return {"content": result.content, "status": "extracted"}
    return {"content": "", "status": "unreadable"}


def document_processing_node(state: State) -> dict:
    # Read the text from the file. A scan with no text layer is unreadable, not sent to the vision model.
    body = download(state["s3_key"])
    try:
        if state["file_format"] == "pdf":
            text = pdf_text(body)
        else:
            text = docx_text(body)
    except (PdfReadError, BadZipFile, ValueError):
        text = ""
    update_document(state["document_id"], status="document_processing_node")
    if text.strip():
        return {"content": text, "status": "extracted"}
    return {"content": "", "status": "unreadable"}


def identify_document_node(state: State) -> dict:
    kind = classify_document(state["content"])
    update_document(
        state["document_id"],
        status="identify_document_node",
        document_type=kind.document_type,
    )
    return {"document_type": kind.document_type}


def extract_fields_node(state: State) -> dict:
    fields = extract_fields(state["content"], state["document_type"]).model_dump()
    update_document(
        state["document_id"],
        status="extract_fields_node",
        extracted_fields=fields,
    )
    return {"fields": fields}


def missing_fields_node(state: State) -> dict:
    model = SCHEMAS[state["document_type"]]
    values = state.get("fields") or {}
    missing = [
        name
        for name in model.model_fields
        if not (values.get(name) or "").strip()
    ]
    update_document(
        state["document_id"],
        status="missing_fields_node",
        missing_fields=missing,
    )
    return {"missing_fields": missing}


def summary_node(state: State) -> dict:
    report = summarize(
        state["document_type"],
        state.get("fields") or {},
        state.get("missing_fields") or [],
    )
    update_document(state["document_id"], status="summary_node", report=report)
    return {"report": report}


def finalize_node(state: State) -> dict:
    # completed means the graph finished. A crash never gets here.
    if state.get("status") == "unsupported":
        update_document(state["document_id"], status="failed", error_message=state["error"])
        return {}
    if state.get("status") == "unreadable":
        report = "The document could not be read."
        update_document(state["document_id"], status="completed", report=report, error_message=None)
        return {"report": report}
    # Clear the message a failed earlier attempt left on the row.
    update_document(state["document_id"], status="completed", error_message=None)
    return {}
