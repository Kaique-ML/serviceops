# Demo script

1. Login as Ana and query `AUR-1001`; query Bruno's `AUR-2001` and observe indistinguishable 404.
2. Create a support proposal, inspect exact payload/effect, and confirm it. Observe one ledger action and destination reference.
3. Create a return proposal; confirm as Ana, approve as the supervisor, and observe one return request (not refund).
4. Enable the local failure injector, commit a support case while losing the response, restart the worker, and reconcile. Query both databases and verify one logical action and exactly one destination operation.
5. Request handoff, assume the conversation, and verify bot proposal creation is denied until control is explicitly returned.

