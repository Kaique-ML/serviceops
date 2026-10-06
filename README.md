# ServiceOps

ServiceOps is an auditable post-sales operations assistant for a fictional distributor. It separates language interpretation from authorization: the model may propose, but authenticated application events and deterministic policy decide, and a recoverable worker performs external effects through an idempotent sandbox API.

> This repository is a portfolio demonstration. Its policies and data are synthetic. Creating a return **request** does not issue a refund, cancel an invoice, or change inventory.

## What is implemented

- FastAPI portal/API with signed cookie sessions, CSRF checks, workspace/customer isolation and four roles.
- Typed order lookup against a separately persisted operations sandbox.
- Concrete, hashed proposal revisions; customer confirmation; separate supervisor approval for returns.
- PostgreSQL ledger/outbox with unique logical actions, leases, fencing checks, retry and reconciliation.
- Destination-side idempotency: same key/payload returns the same resource; different payload conflicts.
- Explicit LangGraph interrupt flow and PostgreSQL checkpointer dependency (the graph is not a business ledger).
- Human handoff that prevents bot-side proposal creation.
- Responsive Portuguese UI and a visible deterministic-mode label.
- Optional, isolated n8n profile. Direct HTTP is the exercised default.

## Quickstart (deterministic demo)

Requirements: Docker Desktop with Compose. Copy `.env.example` to `.env` and replace local secrets, then:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

Open <http://127.0.0.1:18000>. Seed users use the password provided via `SERVICEOPS_DEMO_PASSWORD` (the local fallback is documented in `scripts/seed.py` and must never be enabled for deployment).

## Real LLM mode

Install and start Ollama separately, pull a model that supports structured output, set `SERVICEOPS_DEMO_MODE=false`, `SERVICEOPS_LLM_BASE_URL`, and `SERVICEOPS_LLM_MODEL`, then restart `web`. A real-LLM adapter is intentionally not claimed as verified unless `docs/acceptance.md` records a run. There is no silent scripted fallback.

## Optional n8n route

```powershell
docker compose --profile n8n up -d n8n
```

Import `integrations/n8n/serviceops-action.json`, configure its credential/URL locally, and set `SERVICEOPS_INTEGRATION_ROUTE=n8n`. Starting or importing the workflow is not proof of an end-to-end run; see acceptance status.

## Development

```powershell
python -m uv sync --all-extras
python -m uv run ruff check .
python -m uv run mypy
python -m uv run pytest
```

Architecture, threat boundaries, test levels, known limitations, and evidence are in [`docs/`](docs/). No distribution license has been selected; that decision remains with the repository owner.

## Current limitations

The v1 core API and reliability paths are executable, but the browser UI currently covers login/identity presentation rather than the complete customer and operator consoles. Automated browser E2E, handoff lifecycle verification, proposal editing/revocation, a real LLM run, and an n8n execution remain explicitly unverified in the acceptance matrix. Do not treat the deterministic demo as a production deployment or commercial ERP integration.

