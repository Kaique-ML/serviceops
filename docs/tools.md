# Closed tool catalog

| Tool | Input | Output | Authorization / effect |
|---|---|---|---|
| `get_order` | Public order reference | Minimized status, dates, items, version | Customer-scoped server context; 5 s timeout; read-only |
| `get_applicable_policy` | Case facts | Version and reason codes | Backend-selected synthetic policy; read-only |
| `prepare_support_case` | Validated order/item/quantity/reason/details | Hashed proposal revision | Own conversation; internal write only |
| `prepare_return_request` | Same plus eligible facts | Hashed proposal + policy version | Own conversation; internal write only |
| `request_human_handoff` | Conversation event | Ownership state | Authorized conversation; internal write |

Schemas reject extra fields. The model cannot supply workspace/customer identity, approval, credentials, destination URL, SQL, shell, or arbitrary tools. `execute_approved_action` is worker-controlled and not a model tool. HTTP 200 with a malformed response is a contract failure.

