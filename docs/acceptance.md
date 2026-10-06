# Acceptance matrix

| Requirement | Implementation / evidence | Status |
|---|---|---|
| Reproducible locked install | uv sync and Docker build from `uv.lock` succeeded | PASS |
| Auth and same-workspace customer isolation | own order 200; other customer order 404 | PASS |
| Real sandbox HTTP / PostgreSQL | two PostgreSQL 17.6 databases and HTTP API exercised | PASS |
| Concrete revision-bound approvals | support confirmation and separate return approval exercised | PASS |
| Ledger/outbox/idempotency | worker lease and unique destination key; central flows exercised | PASS |
| Persistent LangGraph restart resume | paused and resumed same thread in separate processes | PASS |
| Lost response creates one resource | unknown -> restart -> succeeded; destination 1 -> 1 | PASS |
| Handoff blocks bot mutation | conversation guard implemented | NOT_RUN |
| Real LLM structured run | requires configured Ollama/model | BLOCKED |
| n8n workflow run | optional profile/workflow | NOT_RUN |
| Browser inspection/screenshots | responsive login UI implemented | NOT_RUN |
| 50-scenario evaluation | 60 scenarios generated; no model metrics | PASS (corpus only) |
| Public GitHub repo and CI | `Kaique-ML/serviceops`; run 37404052025 passed for SHA `8ba58cf` | PASS |

