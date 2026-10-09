# AI Customer Document Assistant

An internal tool for customer operations. Users upload a PDF, DOCX, or image. A LangGraph worker classifies it, extracts fields, checks what is missing, and writes a short report. The browser uploads once, then polls for progress. Processing runs asynchronously on a queue.

This repository contains the frontend, backend API, AI worker, Terraform, CI/CD workflows, and documentation. Nothing has been applied, built, or pushed to AWS for this submission. The files describe how a later `terraform apply` and the deploy workflow would stand the system up.

## Repository layout

| Path | Role |
| --- | --- |
| `frontend/` | React app. Upload, history, and document detail with 5-second polling. |
| `backend/` | FastAPI. Upload to S3, insert a row, send SQS, serve status, accept worker PATCH. |
| `ai-service/` | SQS worker and LangGraph graph. No database access. |
| `terraform/` | Main AWS stack: network, ECS, S3, SQS, RDS, load balancers, DNS. |
| `terraform/bootstrap/` | One-time stack: state bucket, lock table, OIDC provider, plan and deploy roles. |
| `.github/workflows/` | Pull-request checks and plan. Main apply, image push, and ECS rollout. |
| `docs/` | Architecture, LangGraph, networking, infrastructure, CI/CD, and decisions. |

## Documentation map

| Assignment topic | File |
| --- | --- |
| Solution architecture | [docs/architecture.md](docs/architecture.md) |
| AWS architecture | [docs/architecture.md](docs/architecture.md) |
| LangGraph design | [docs/langgraph.md](docs/langgraph.md) |
| Networking design | [docs/networking.md](docs/networking.md) |
| Terraform structure | [docs/infrastructure.md](docs/infrastructure.md) |
| ECS deployment design | [docs/infrastructure.md](docs/infrastructure.md) |
| CI/CD design | [docs/cicd.md](docs/cicd.md) |
| Assumptions, tradeoffs, future improvements | [docs/decisions.md](docs/decisions.md) |

## Run locally

Local runs need Postgres plus an S3 bucket, an SQS queue, and Bedrock access. boto3 reads `AWS_ENDPOINT_URL`, so S3 and SQS can point at a local emulator (for example one listening on `http://localhost:4566`, with dummy credentials). Bedrock still needs real access unless the emulator provides it.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/documents
export S3_BUCKET=your-bucket
export SQS_QUEUE_URL=https://sqs..../your-queue
# optional, for a non-localhost frontend origin
# export CORS_ORIGIN=http://localhost:5173
uvicorn main:app --reload --port 8000
```

The backend creates the `documents` table on startup. Env vars: `DATABASE_URL`, `S3_BUCKET`, `SQS_QUEUE_URL`, optional `CORS_ORIGIN`.

### AI worker

```bash
cd ai-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SQS_QUEUE_URL=https://sqs..../your-queue
export S3_BUCKET=your-bucket
export BACKEND_URL=http://127.0.0.1:8000
export BEDROCK_MODEL_ID=your-vision-model-id
export BEDROCK_CLASSIFY_MODEL_ID=your-text-model-id
python worker.py
```

The worker has no `DATABASE_URL`. Progress goes through `PATCH` on the backend.

```bash
cd ai-service && python -m pytest -q
```

### Frontend

```bash
cd frontend
npm ci
# optional; defaults to http://localhost:8000
# export VITE_API_URL=http://localhost:8000
npm run dev
```

Open the Vite URL (usually `http://localhost:5173`). In Docker, `VITE_API_URL` is a build arg, not a runtime variable.

## Deploy (not done for this submission)

1. Apply `terraform/bootstrap` once from a machine with AWS credentials. It uses local state.
2. Set GitHub secrets `AWS_PLAN_ROLE_ARN` and `AWS_DEPLOY_ROLE_ARN`, and variables `TF_STATE_BUCKET` and `TF_LOCK_TABLE`, from the bootstrap outputs.
3. Bedrock model ids default to Nova Lite and Nova Micro. Override `bedrock_model_id` and `bedrock_classify_model_id` to use different models.
4. Push to `main`. Once the bootstrap variables are set, the deploy workflow applies the main stack, builds and pushes the three images, and force-rolls the ECS services.

Details: [docs/cicd.md](docs/cicd.md) and [docs/infrastructure.md](docs/infrastructure.md).
