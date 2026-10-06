# Architecture

The browser sends application events, never arbitrary LangGraph commands. FastAPI derives user, workspace, customer, and role from the signed session and active membership. Read tools call the operations sandbox with a server-held credential. Mutations create an immutable proposal revision. Authenticated confirmation/approval changes its state and atomically inserts one ledger/outbox action.

The worker claims queued or uncertain actions using `FOR UPDATE SKIP LOCKED`, a lease owner and expiry. It reconciles by idempotency key before sending. The sandbox independently validates tenant/customer ownership and persists idempotency key + canonical payload hash. A stale worker cannot publish after its lease fence changes.

LangGraph checkpoints conversational progress and interrupts; the action ledger is authoritative for business intent and results. A checkpoint can replay node code, so no external mutation occurs inside a pre-interrupt node.

| Object | Representative states | Guard |
|---|---|---|
| Conversation | `bot_active`, `human_active` | Bot proposals blocked while human owns it |
| Proposal | `awaiting_customer`, `awaiting_supervisor`, `approved`, terminal rejection/expiry | Exact revision, current role, validity |
| Action | `queued`, `in_flight`, `unknown`, `reconciling`, `succeeded`, `failed` | Unique proposal revision and key |

There is no distributed transaction. Unknown outcomes are reconciled against destination state. The demonstrated property is one resource under the tested failure, not universal exactly-once delivery.

