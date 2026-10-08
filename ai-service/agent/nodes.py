import os
from pathlib import Path

import boto3

from agent.extract import extract_image
from agent.state import State

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff"}
BEDROCK_FORMATS = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif", ".webp": "webp"}


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


def download(key: str) -> bytes:
    return boto3.client("s3").get_object(
        Bucket=os.environ["S3_BUCKET"],
        Key=key,
    )["Body"].read()


def image_processing(state: State) -> dict:
    extension = Path(state["s3_key"]).suffix.lower()
    media_type = BEDROCK_FORMATS.get(extension)
    if media_type is None:
        raise ValueError(f"unsupported image type: {extension}")

    body = download(state["s3_key"])
    result = extract_image(body, media_type)
    if result.readable:
        return {"content": result.content, "status": "extracted"}
    return {"content": "", "status": "unreadable"}


def document_processing(state: State) -> dict:
    return {}
