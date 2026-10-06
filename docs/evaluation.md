# Evaluation

`evals/datasets/scenarios.json` is generated deterministically and contains at least 50 grouped scenarios across lookup, clarification, support, returns, access denial, prompt injection, external failure, recovery and handoff. Expected/prohibited actions are kept in each oracle record and are not supplied to a model prompt.

The deterministic baseline routes explicit form fields through the same application services. Authorization/idempotency are scored from database/API state, never from generated text. Real-LLM scores must record model/digest, settings, commit, date, numerator/denominator, latency sample size and failures. No real-LLM evaluation has been run in the current environment unless acceptance says otherwise.

