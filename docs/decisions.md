# Assumptions, tradeoffs, and future improvements

## Assumptions

- One private S3 bucket for uploads
- Two Bedrock model ids: vision for images (`amazon.nova-lite-v1:0`), smaller text model for classify, extract, and summary (`amazon.nova-micro-v1:0`). Both can be overridden
- There is no login because this is an internal tool. Network access is limited with `allowed_cidrs`, which defaults to open and should be narrowed in a real deployment
- Progress is one Postgres row per upload
- Each document is processed on its own, one file per upload request. The brief does not mention batches or comparing documents with each other
- The brief names ECS, Terraform, Docker and LangGraph. SQS, Postgres on RDS, FastAPI, React and Bedrock are design choices made for this solution
- Public domain defaults to `cda.example.com` and does not resolve until name servers are delegated
- This submission does not apply Terraform, push images, or run the deploy workflow

## Tradeoffs

| Decision | Chose | Instead of | Why |
| --- | --- | --- | --- |
| PDF and DOCX text | Local `pypdf` / `python-docx` | Sending every document to the vision model | Cheaper and faster for files with a text layer. Scanned PDFs with no text are unreadable. |
| Progress updates | Poll every 5 seconds | WebSockets or SSE | Simple for the brief. No sticky sessions or extra protocol. |
| Table schema | Backend creates the table on startup | Terraform or a migration tool | Schema stays with the app. Terraform stays infrastructure. |
| Worker data access | PATCH through private backend | Direct Postgres from the worker | One writer, one security group rule to RDS. |
| Public routing | Two hostnames (`app.` and `api.`) | Path rules on one host | React and API both use `/documents/...`. |
| Private discovery | Internal ALB + Route 53 | ECS Service Connect / Cloud Map | Stable name, health checks, one backend behind both doors. |
| Outbound AWS | One NAT | VPC endpoints per service | Fewer resources for a design that is not applied. |
| TLS | HTTP on port 80 | ACM + HTTPS listeners | Assignment requires domain names, not certificates. |
| Images | `:latest` plus commit SHA | New task definition per commit | App deploys do not rewrite infrastructure. |
| Scaling | Backend 1–3 on 70% CPU. Worker 1–5 on one waiting message per task. Frontend fixed at 1. | One shared count, or scaling the static frontend | Each service scales on its own load. |
| Worker concurrency | One message per task | Several documents at once inside one task | Scaling follows queue depth directly and a crash affects one document. Less efficient, since most time is spent waiting on Bedrock. |
| Unsupported files | Refused at upload, and a route inside the graph | Raising an exception | A retry cannot fix a file type, so it should not be retried. |
| Failures | Node retry (3 attempts), then SQS redelivery (3 receives), then dead-letter queue | A single retry layer | Short problems are absorbed inside the graph. Longer ones wait in the queue. |

## Limits an interviewer may ask about

**Backend health check is `GET /documents`.** It returns 200 and touches the database, so it proves the process and Postgres are up. It also returns every row. A dedicated `/health` route would be lighter.

**Unreadable report is a string; a normal report is an object.** The UI and the JSON column accept both. A single report shape for every path would be cleaner.

**If the backend is down when the worker records `failed`.** The PATCH raises, the worker process exits, ECS restarts it, and the SQS message reappears after the visibility timeout. The row may stay at the last successful node status until a later attempt.

**GitHub roles sit outside `cda-*`.** Named `gha-cda-plan` and `gha-cda-deploy` so the deploy role's IAM name filter cannot rewrite those trust policies.

## Future improvements

- Send scanned PDFs with no text layer through the vision path instead of marking them unreadable
- CloudWatch alarm on the dead-letter queue depth
- HTTPS listeners and a real delegated domain
- Second NAT for multi-AZ outbound resilience
- Dedicated `/health` route that does not list documents
- Stronger next-action suggestions if the report prompt stays thin
- Process several documents concurrently inside one worker task, since most of the time is spent waiting on Bedrock
- A status history table with a timestamp per change, for a timeline on each document
- Cross-document checks: group one customer's documents into a case and compare names, dates and references
- Push updates over WebSockets or server-sent events instead of polling, with Redis pub/sub only if push is adopted
- Single sign-on at the load balancer (Cognito or a corporate identity provider) and per-user history
- Scale the worker to zero when the queue is empty: cheaper, with a startup delay on the first document
- At least two tasks per service across two availability zones, and Multi-AZ for RDS
