import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID, uuid4

import boto3
import psycopg
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    s3_key TEXT NOT NULL,
    status TEXT NOT NULL,
    document_type TEXT,
    extracted_fields JSONB,
    missing_fields JSONB,
    report JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

JSON_COLUMNS = {"extracted_fields", "missing_fields", "report"}

# The worker can read these. Anything else is refused at upload, not after queueing.
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png", ".gif", ".webp"}


def connect():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def as_document(row):
    row["id"] = str(row["id"])
    return row


@asynccontextmanager
async def lifespan(app):
    # The table belongs to the app. Infrastructure creates the database, not this schema.
    with connect() as conn:
        conn.execute(SCHEMA)
        conn.commit()
    yield


app = FastAPI(lifespan=lifespan)

# Local Vite plus the deployed app hostname from CORS_ORIGIN.
_cors_origins = ["http://127.0.0.1:5173", "http://localhost:5173"]
if os.environ.get("CORS_ORIGIN"):
    _cors_origins.append(os.environ["CORS_ORIGIN"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DocumentUpdate(BaseModel):
    status: str | None = None
    document_type: str | None = None
    extracted_fields: dict | None = None
    missing_fields: list | None = None
    report: dict | list | str | None = None
    error_message: str | None = None


@app.get("/documents")
def list_documents():
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY created_at DESC"
        ).fetchall()
    return [as_document(row) for row in rows]


@app.get("/documents/{document_id}")
def get_document(document_id: UUID):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = %s",
            (document_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="document not found")
    return as_document(row)


@app.post("/documents", status_code=201)
def create_document(file: UploadFile):
    filename = Path(file.filename or "").name
    if not filename:
        raise HTTPException(status_code=400, detail="filename is required")

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported file type: {extension or 'none'}. Use PDF, DOCX, JPG, PNG, GIF, or WEBP.",
        )

    document_id = str(uuid4())
    content_type = file.content_type or "application/octet-stream"
    s3_key = f"uploads/{document_id}/{filename}"
    body = file.file.read()

    boto3.client("s3").put_object(
        Bucket=os.environ["S3_BUCKET"],
        Key=s3_key,
        Body=body,
        ContentType=content_type,
    )

    # The row exists before the queue message, so the client can poll immediately.
    with connect() as conn:
        row = conn.execute(
            """
            INSERT INTO documents (id, filename, content_type, s3_key, status)
            VALUES (%s, %s, %s, %s, 'queued')
            RETURNING *
            """,
            (document_id, filename, content_type, s3_key),
        ).fetchone()
        conn.commit()

    boto3.client("sqs").send_message(
        QueueUrl=os.environ["SQS_QUEUE_URL"],
        MessageBody=json.dumps(
            {
                "document_id": document_id,
                "s3_key": s3_key,
                "content_type": content_type,
            }
        ),
    )
    return as_document(row)


@app.patch("/documents/{document_id}")
def update_document(document_id: UUID, update: DocumentUpdate):
    # Worker progress. This route stays off the public load balancer.
    changes = update.model_dump(exclude_unset=True)
    if not changes:
        return get_document(document_id)

    assignments = []
    values = []
    for column, value in changes.items():
        if column in JSON_COLUMNS:
            value = Jsonb(value)
        assignments.append(f"{column} = %s")
        values.append(value)
    assignments.append("updated_at = now()")
    values.append(document_id)

    with connect() as conn:
        row = conn.execute(
            f"""
            UPDATE documents
            SET {", ".join(assignments)}
            WHERE id = %s
            RETURNING *
            """,
            values,
        ).fetchone()
        conn.commit()
    if row is None:
        raise HTTPException(status_code=404, detail="document not found")
    return as_document(row)
