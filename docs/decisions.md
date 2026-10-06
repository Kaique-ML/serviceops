# Decisions

- Python constraint is 3.12–3.14; compatibility was resolved on CPython 3.14.4 with the committed uv lock.
- FastAPI/SQLAlchemy/Pydantic/LangGraph versions come from `uv.lock`; source documentation is the official project documentation named in the execution brief.
- PostgreSQL 17.6 and n8n 1.113.3 image tags are explicit. n8n is optional; direct HTTP is the default.
- The database ledger is also the outbox to avoid Redis/Celery duplicating orchestration in v1.
- The synthetic return window is delivery date through day 30 inclusive, using an injected date in unit tests. Runtime business timezone is configurable; remaining runtime policy clock integration is tracked as incomplete.
- No license was selected on the owner's behalf.

