# Security

Controls include scrypt password hashing, signed HttpOnly SameSite cookies, double-submit CSRF, active-membership revalidation, workspace/customer predicates, opaque UUIDs, typed inputs, output validation, no redirects, fixed integration base URL, server-held credentials, escaped UI rendering, request size limits in schemas and deduplicated input event IDs.

Untrusted chat/order text never changes tool names, identity, endpoints, approval or policy. The model receives no SQL, shell, credential, unrestricted network access or arbitrary resume interface. Logs should contain identifiers and sanitized codes, not passwords, tokens, full histories or private reasoning.

Residual risks include a basic custom session format, absent rate limiting/key rotation, development fallback secrets, unimplemented webhook endpoint, and incomplete automated browser/security coverage. This is not a claim of legal compliance or elimination of prompt injection.

