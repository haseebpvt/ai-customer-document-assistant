FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py .
COPY agent ./agent

# No port. This process only polls the queue and calls the backend.
# SQS_QUEUE_URL, S3_BUCKET, BACKEND_URL, and the two Bedrock model ids
# are supplied when the container starts. It does not get DATABASE_URL.
CMD ["python", "worker.py"]
