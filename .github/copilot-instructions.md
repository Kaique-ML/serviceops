# ServiceOps invariants

- The model proposes; authenticated backend code authorizes; the worker executes.
- Never derive workspace, customer, role, approval, endpoint or credential from chat/model output.
- Checkpoints are conversation progress, not the business action ledger.
- Preserve proposal revision/hash binding and destination idempotency on every mutation.
- Unknown external outcomes must reconcile; do not describe them as success.
- Use synthetic data only and describe return operations as requests, never refunds.

