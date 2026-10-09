FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

# Listen on all interfaces so a load balancer can reach the process.
# DATABASE_URL, S3_BUCKET, and SQS_QUEUE_URL are supplied when the container starts.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
