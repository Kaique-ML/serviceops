# Reliability

The action row doubles as a transactional outbox. Short database transactions claim work; network calls occur outside transactions. Leases and a fence comparison reject stale completion. Unknown HTTP outcomes are scheduled for reconciliation. The destination stores the idempotency key with a canonical payload hash: same payload returns the original reference, while changed payload is HTTP 409.

The local failure switch `OPERATIONS_ALLOW_FAILURE_INJECTION=true` permits a request header to make the sandbox commit and then report a synthetic lost response. It is off by default and belongs only in isolated tests. Retention/archival and multi-region fencing are not implemented.

