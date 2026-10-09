# Terraform structure and ECS deployment

Terraform describes the AWS layout. It is validated locally. It has not been applied for this submission. There is no remote state until `terraform/bootstrap` is applied once by a person.

## Main stack files

| File | Creates |
| --- | --- |
| `versions.tf` | Terraform and AWS provider |
| `variables.tf` | Region, public domain, name prefix, Bedrock model ids, `allowed_cidrs` |
| `backend.tf` | Partial S3 backend. Bucket and lock table passed at init |
| `network.tf` | VPC, public and private subnets, one NAT, routes |
| `security.tf` | Security groups for ALBs, three services, RDS |
| `loadbalancers.tf` | Public and internal ALBs, listeners, PATCH 403 |
| `dns.tf` | Public zone for `app.` and `api.`; private zone `backend.internal` |
| `storage.tf` | Private S3 bucket; SQS queue and dead-letter queue |
| `database.tf` | RDS Postgres 16, Secrets Manager `DATABASE_URL` |
| `iam.tf` | Task and execution roles |
| `ecs.tf` | ECR repos, cluster, task definitions, three services |
| `autoscaling.tf` | Backend CPU scaling and worker queue scaling |
| `outputs.tf` | Domains, `public_alb_dns_name`, queue, bucket, ECR URLs, ECS names |

## Bootstrap stack (`terraform/bootstrap/`)

| File | Creates |
| --- | --- |
| `main.tf` | State bucket, DynamoDB lock table, GitHub OIDC provider, plan and deploy roles |
| `variables.tf` | Region, prefix, GitHub org and repo |
| `outputs.tf` | Values for the four GitHub Actions settings |
| `versions.tf` | Providers |

Bootstrap uses local state. GitHub cannot assume a role that does not exist, and the main stack cannot keep state in a bucket that does not exist, so those resources cannot be created by the same apply that needs them.

GitHub roles are named `gha-cda-plan` and `gha-cda-deploy`. The deploy role may edit IAM roles named `cda-*` (the main stack task and execution roles). The GitHub roles sit outside that pattern so a deploy cannot rewrite its own trust policy.

## What Terraform does not create

RDS creates an empty Postgres database named `documents`. The `documents` table is created by the backend on startup (`CREATE TABLE IF NOT EXISTS` in `backend/main.py`). Schema stays with the app. Terraform stays infrastructure.

## ECS services

One Fargate cluster. Three services. Separate task roles.

| Service | CPU | Memory | Tasks | Port |
| --- | --- | --- | --- | --- |
| Frontend | 256 (0.25 vCPU) | 512 MB | 1, fixed | 80 |
| Backend | 256 (0.25 vCPU) | 512 MB | 1 to 3 | 8000 |
| AI worker | 512 (0.5 vCPU) | 1024 MB | 1 to 5 | none |

The frontend serves static files, so it has no scaling rule. The backend target is 70% CPU. The worker target is one visible SQS message per running task. Each service has its own count: web traffic does not add worker tasks, and a long queue does not add frontend tasks.

The worker holds one file in memory, so it has more memory. The 300-second visibility timeout is still longer than one graph run, including Bedrock retries, and it shortens the wait when a task is stopped mid-document during scale-in or a deploy. A stopped task does not lose the message. It becomes visible again and another task picks it up.

## Task role versus execution role

| Role | Used by | Purpose |
| --- | --- | --- |
| Task role | The process (`boto3`) | S3, SQS, Bedrock permissions |
| Execution role | The ECS agent | Pull from ECR, write logs, inject secrets |

Frontend task role has no AWS permissions. Backend task role can PutObject and SendMessage. AI task role can GetObject, receive and delete messages, change message visibility, and call Bedrock through `bedrock:InvokeModel`. Only the backend execution role can read the `DATABASE_URL` secret. The AI service never receives that secret.

Bedrock model ids default to `amazon.nova-lite-v1:0` and `amazon.nova-micro-v1:0`. Override them with the same variable names. `allowed_cidrs` defaults to `0.0.0.0/0` and should be narrowed for a real internal deployment.

## Environment variables

| Service | Variables |
| --- | --- |
| Frontend | none at runtime. `VITE_API_URL` is a Docker build arg. |
| Backend | `S3_BUCKET`, `SQS_QUEUE_URL`, `CORS_ORIGIN`, `DATABASE_URL` (from Secrets Manager) |
| AI worker | `S3_BUCKET`, `SQS_QUEUE_URL`, `BACKEND_URL`, `BEDROCK_MODEL_ID`, `BEDROCK_CLASSIFY_MODEL_ID` |

## Images and `:latest`

ECR repositories: `cda-frontend`, `cda-backend`, `cda-ai-service`. Task definitions reference `:latest`. Tags are mutable so the deploy workflow can push a new `:latest` without rewriting the task definition on every application commit. The workflow also tags each image with the commit SHA so an old image can be named later.

Services would fail to start until those images exist. That is expected before the first successful deploy workflow run.

## Storage and queue

- S3: private, public access blocked, SSE-S3.
- SQS: visibility timeout 300 seconds, still longer than one graph run with retries. Dead-letter queue after 3 receives. Long poll 20 seconds, matching the worker. On a failed attempt the worker sets the next visibility to 30 seconds.

## Database

Postgres 16, `db.t4g.micro`, single-AZ, encrypted, not public, private subnets only. `skip_final_snapshot` is true because this database is part of a design, not a long-lived production instance. Password is random and stored only as the full `DATABASE_URL` in Secrets Manager.
