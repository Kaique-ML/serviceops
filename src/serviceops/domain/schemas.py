from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentDecision(StrictModel):
    intent: Literal["order_status", "support_case", "return_request", "handoff", "unsupported"]
    missing_fields: list[str] = Field(default_factory=list, max_length=8)
    proposed_tool: (
        Literal[
            "get_order",
            "get_applicable_policy",
            "prepare_support_case",
            "prepare_return_request",
            "request_human_handoff",
        ]
        | None
    ) = None
    tool_arguments: dict[str, Any] = Field(default_factory=dict)
    reply_kind: Literal["clarification", "factual_answer", "proposal", "status_update", "handoff"]


class ProposalCreate(StrictModel):
    conversation_id: str
    kind: Literal["support_case", "return_request"]
    order_reference: str = Field(min_length=3, max_length=40)
    item_reference: str = Field(min_length=1, max_length=80)
    quantity: int = Field(gt=0, le=1000)
    reason: Literal["wrong_product", "damaged", "late", "quality_issue"]
    details: str = Field(min_length=3, max_length=1000)


class MessageCreate(StrictModel):
    client_event_id: str = Field(min_length=8, max_length=100)
    body: str = Field(min_length=1, max_length=4000)


class LoginRequest(StrictModel):
    email: str
    password: str
