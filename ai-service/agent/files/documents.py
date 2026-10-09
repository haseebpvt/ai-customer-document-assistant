from io import BytesIO

from docx import Document
from docx.table import Table
from pypdf import PdfReader


def pdf_text(body: bytes) -> str:
    reader = PdfReader(BytesIO(body))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def docx_text(body: bytes) -> str:
    # Forms are often laid out as tables. Paragraphs alone would miss them.
    document = Document(BytesIO(body))
    lines = []
    for block in document.iter_inner_content():
        if isinstance(block, Table):
            for row in block.rows:
                lines.append(" | ".join(cell.text for cell in row.cells))
        else:
            lines.append(block.text)
    return "\n".join(lines)
