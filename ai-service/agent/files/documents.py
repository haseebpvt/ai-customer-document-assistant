from io import BytesIO

from docx import Document
from pypdf import PdfReader


def pdf_text(body: bytes) -> str:
    reader = PdfReader(BytesIO(body))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def docx_text(body: bytes) -> str:
    document = Document(BytesIO(body))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)
