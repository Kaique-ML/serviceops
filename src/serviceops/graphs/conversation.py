from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


class ConversationState(TypedDict, total=False):
    intent: str
    phase: str
    proposal_id: str
    decision: str


def route(state: ConversationState) -> ConversationState:
    return {"phase": "consult" if state.get("intent") == "order_status" else "prepare"}


def choose(state: ConversationState) -> Literal["consult", "prepare"]:
    return "consult" if state["phase"] == "consult" else "prepare"


def consult(_: ConversationState) -> ConversationState:
    return {"phase": "completed"}


def prepare(state: ConversationState) -> ConversationState:
    decision = interrupt(
        {"kind": "authenticated_application_decision", "proposal_id": state.get("proposal_id")}
    )
    return {"phase": "resume", "decision": str(decision)}


def build_graph(checkpointer=None):
    graph = StateGraph(ConversationState)
    graph.add_node("route", route)
    graph.add_node("consult", consult)
    graph.add_node("prepare", prepare)
    graph.add_edge(START, "route")
    graph.add_conditional_edges("route", choose)
    graph.add_edge("consult", END)
    graph.add_edge("prepare", END)
    return graph.compile(checkpointer=checkpointer)
