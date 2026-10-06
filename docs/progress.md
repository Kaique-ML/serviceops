# Progress log

## 2026-10-05

- Workspace was empty; no local `AGENTS.md` or Copilot instructions existed.
- Observed CPython 3.14.4, Git 2.53.0 at `C:\Program Files\Git\cmd\git.exe`, Docker CLI 29.2.1 / Compose 5.1.0, GitHub CLI 2.101.0, Node 24.19.0.
- Docker engine/config access was denied in the current sandbox; Ollama was not installed; no provider key flag was present.
- GitHub CLI identified account `Kaique-ML`, but its token was invalid and network was sandbox-blocked.
- Installed uv 0.8.22 with approval; generated its resolver lock against Python 3.14.4. Resolved versions include FastAPI 0.142.2, SQLAlchemy 2.1.3, Pydantic 2.13.5, LangGraph 1.2.13 and PostgreSQL checkpointer 3.1.2.
- Static verification: Ruff passed, strict mypy passed for domain/settings, and pytest passed 5/5 unit tests.
- Docker images built from locked dependencies. Alembic migration applied to PostgreSQL 17.6; repeatable seed created two workspaces and two customers in the same workspace.
- Real HTTP isolation probe: Ana read `AUR-1001` (`delivered`) while Bruno's `AUR-2001` returned the same 404 shape.
- Real support flow: proposal -> authenticated confirmation -> worker -> sandbox returned `CASE-F9F334D168`; destination count was 1.
- Real return flow: customer confirmation produced `awaiting_supervisor`; supervisor approval produced `RET-3087CA499C`; destination count for its idempotency key was 1.
- Lost-response probe: action `30149b63-a234-4a35-8245-e969bf7a5e0f` became `unknown` after the sandbox committed one resource. After API/worker recreation it reconciled to `succeeded|CASE-DED299729F`; destination count remained 1.
- LangGraph/PostgreSQL probe used two disposable processes: first printed `paused=true`, second resumed `restart-proof-001` and printed `resumed=true decision=authenticated-confirmed`.
- Generated 60 grouped evaluation scenarios (40 development, 20 holdout). No LLM was run; these are corpus counts, not quality metrics.
- UI bound to `127.0.0.1:18000` because port 8000 was already occupied by an unrelated local service. Automated browser inspection was not run.

