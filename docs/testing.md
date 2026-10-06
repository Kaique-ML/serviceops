# Testing

Unit tests cover inclusive date boundaries, quantities, hashes, password/session integrity and rejection of fabricated tools/approval fields. Integration tests require two real PostgreSQL databases and real HTTP services. Commands and observed counts belong in `progress.md`; missing Docker/LLM/browser execution is `BLOCKED` or `NOT_RUN`, never passed by mocks.

Observed on 2026-10-05: Ruff passed; strict mypy passed for the domain/settings scope; pytest passed 5/5. Real PostgreSQL/HTTP probes for isolation, support, return approval, restart checkpoint and lost-response reconciliation passed. These manually invoked probes should be promoted to automated integration tests; browser E2E was not run.

```powershell
python -m uv run ruff check .
python -m uv run mypy
python -m uv run pytest
docker compose build
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

