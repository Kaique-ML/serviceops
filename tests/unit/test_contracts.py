import pytest
from pydantic import ValidationError

from serviceops.domain.models import canonical_hash
from serviceops.domain.schemas import AgentDecision


def test_canonical_hash_is_order_independent_and_changes_with_payload():
    assert canonical_hash({"a": 1, "b": 2}) == canonical_hash({"b": 2, "a": 1})
    assert canonical_hash({"a": 1}) != canonical_hash({"a": 2})


def test_agent_output_rejects_unknown_tool_and_approval_field():
    with pytest.raises(ValidationError):
        AgentDecision.model_validate(
            {
                "intent": "support_case",
                "proposed_tool": "run_shell",
                "missing_fields": [],
                "tool_arguments": {},
                "reply_kind": "proposal",
            }
        )
    with pytest.raises(ValidationError):
        AgentDecision.model_validate(
            {
                "intent": "support_case",
                "proposed_tool": None,
                "missing_fields": [],
                "tool_arguments": {},
                "reply_kind": "proposal",
                "approved": True,
            }
        )
