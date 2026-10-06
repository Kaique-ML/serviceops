# Decisions and approvals

Customer confirmation and supervisor approval are distinct authenticated events. A support case needs the first; a return request needs both. Each decision binds to proposal UUID, revision, canonical payload hash, policy version, order version and expiry. Duplicate clicks reuse the unique action. Editing must create a new revision and supersede the old one; the current v1 API exposes creation, not editing.

Execution revalidates the approved proposal/hash. Expired, rejected, superseded, revoked-role, wrong-workspace and wrong-customer decisions are denied. A chat message such as “yes” or model JSON containing `approved=true` has no authority.

