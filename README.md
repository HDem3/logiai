# LogiAI

An auditable logistics document assistant aligned with FERCAM's AI Application Analyst internship: evaluating AI tools, prototyping solutions, testing platforms, documenting usage and collecting user feedback.

## Working MVP

- Upload PDF or text procedures
- Extract, chunk and index content
- Retrieve relevant passages and return citations
- Safe no-context guardrail instead of a fabricated answer
- LLM integration seam that defaults to a deterministic offline stub
- Feedback storage and evaluation metrics
- PostgreSQL/pgvector-ready Docker stack

## Run

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost:8000/docs. Upload a procedure with `POST /documents`, ask with `POST /ask`, then submit feedback. No API key is needed in stub mode.

## LLM and vector integration

The local embedding and answer generator make the project reproducible and inexpensive. For production, implement an adapter in `app/rag.py`, store vectors with `pgvector.sqlalchemy.Vector(128)` (or the provider dimension), create an HNSW index, and replace the in-process cosine ranking with a database distance query. Set `LLM_PROVIDER` only after the adapter is configured; keep API keys in the cloud secret manager.

## Evaluation

`evaluation/golden_set.json` is the initial reviewed question set. Track retrieval hit rate, grounded/no-answer correctness, answer quality from human review, helpful rate and latency. `/evaluations` returns the current operational baseline.

## Cloud deployment

### Render blueprint

Push this directory to GitHub and create a Render Blueprint from `render.yaml`. The API and managed PostgreSQL are provisioned automatically. The included code runs on standard PostgreSQL; enable the `vector` extension and pgvector column/index when promoting the retrieval layer.

### Azure/AWS

Push the Docker image to ACR/ECR, deploy to Container Apps/ECS, attach managed PostgreSQL with pgvector support, inject `DATABASE_URL`, `LLM_PROVIDER` and the provider API key as secrets, and configure `/health` as a probe. Restrict uploads, add authentication, malware scanning, encryption and a document retention policy before real company data is used.

## Privacy and limitations

This portfolio MVP must use synthetic/non-confidential documents. The stub is not a factual LLM and deliberately echoes the best retrieved passage. Production requires access control, tenant isolation, prompt-injection defenses, migrations, observability and human-reviewed evaluations.

