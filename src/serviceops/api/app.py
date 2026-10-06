import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from serviceops.auth.security import (
    make_session,
    principal_from,
    public_user,
    require_csrf,
    verify_password,
)
from serviceops.domain.models import (
    Action,
    AuditEvent,
    Conversation,
    Membership,
    Message,
    Proposal,
    ProposalState,
    Role,
    User,
    canonical_hash,
)
from serviceops.domain.policy import evaluate_return
from serviceops.domain.schemas import LoginRequest, MessageCreate, ProposalCreate
from serviceops.integrations.operations import OperationsClient
from serviceops.persistence.database import db_session
from serviceops.settings import get_settings

app = FastAPI(title="ServiceOps", version="0.1.0", docs_url="/api/docs")


def principal(request: Request, db: Session = Depends(db_session)):
    return principal_from(request, db)


def audit(
    db: Session, workspace_id: str, actor: str | None, event: str, subject: str, **details: object
) -> None:
    db.add(
        AuditEvent(
            workspace_id=workspace_id,
            actor_user_id=actor,
            event_type=event,
            subject_id=subject,
            details=details,
        )
    )


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def ready(db: Session = Depends(db_session)) -> dict[str, str]:
    db.execute(select(1))
    return {"status": "ready"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    badge = "DEMO — MODELO SIMULADO" if get_settings().demo_mode else "LLM REAL"
    return f"""<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>ServiceOps</title><link rel='stylesheet' href='/static/app.css'></head><body><header><b>ServiceOps</b><span class='badge'>{badge}</span></header>
<main><section class='hero'><p class='eyebrow'>OPERAÇÕES PÓS-VENDA</p><h1>Ajuda rastreável, com decisões humanas no controle.</h1>
<p>Consulte pedidos, prepare chamados e acompanhe solicitações sem confundir proposta com execução.</p></section>
<section class='panel'><h2>Entrar na demonstração</h2><p>Use uma conta sintética criada pelo seed local.</p>
<form id='login'><label>E-mail<input id='email' type='email' autocomplete='username' required></label><label>Senha<input id='password' type='password' autocomplete='current-password' required></label><button>Entrar</button></form><p id='result' aria-live='polite'></p></section></main>
<script src='/static/app.js'></script></body></html>"""


@app.post("/api/v1/login")
def login(
    body: LoginRequest, response: Response, db: Session = Depends(db_session)
) -> dict[str, object]:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_credentials")
    membership = db.scalar(
        select(Membership).where(Membership.user_id == user.id, Membership.active.is_(True))
    )
    if not membership:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no_active_membership")
    csrf = secrets.token_urlsafe(24)
    response.set_cookie(
        "serviceops_session",
        make_session(user.id, membership.workspace_id),
        httponly=True,
        secure=get_settings().env != "development",
        samesite="strict",
    )
    response.set_cookie(
        "serviceops_csrf",
        csrf,
        httponly=False,
        secure=get_settings().env != "development",
        samesite="strict",
    )
    return {"user": public_user(user, membership), "csrf_token": csrf}


@app.get("/api/v1/me")
def me(p=Depends(principal), db: Session = Depends(db_session)) -> dict[str, object]:
    return public_user(
        db.get(User, p.user_id),
        db.scalar(
            select(Membership).where(
                Membership.user_id == p.user_id, Membership.workspace_id == p.workspace_id
            )
        ),
    )


def scoped_conversation(db: Session, p, conversation_id: str) -> Conversation:
    query = select(Conversation).where(
        Conversation.id == conversation_id, Conversation.workspace_id == p.workspace_id
    )
    if p.role == Role.customer:
        query = query.where(Conversation.customer_id == p.customer_id)
    conversation = db.scalar(query)
    if not conversation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not_found")
    return conversation


@app.get("/api/v1/orders/{reference}")
def get_order(reference: str, p=Depends(principal)) -> dict[str, object]:
    if p.role != Role.customer or not p.customer_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "customer_required")
    order = OperationsClient().get_order(p.workspace_id, p.customer_id, reference)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not_found")
    return {
        "order": order,
        "evidence": {"source": "operations_sandbox", "observed_at": datetime.now(UTC)},
    }


@app.post("/api/v1/conversations/{conversation_id}/messages")
def add_message(
    conversation_id: str,
    body: MessageCreate,
    request: Request,
    p=Depends(principal),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    require_csrf(request)
    conversation = scoped_conversation(db, p, conversation_id)
    if conversation.state == "human_active" and p.role == Role.customer:
        actor = "customer"
    elif p.role == Role.customer:
        actor = "customer"
    else:
        actor = "human_operator"
    message = Message(
        conversation_id=conversation.id,
        client_event_id=body.client_event_id,
        actor=actor,
        body=body.body,
    )
    db.add(message)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        message = db.scalar(
            select(Message).where(
                Message.conversation_id == conversation.id,
                Message.client_event_id == body.client_event_id,
            )
        )
    return {"id": message.id, "deduplicated": message.body == body.body}


@app.post("/api/v1/proposals")
def create_proposal(
    body: ProposalCreate, request: Request, p=Depends(principal), db: Session = Depends(db_session)
) -> dict[str, object]:
    require_csrf(request)
    if p.role != Role.customer or not p.customer_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "customer_required")
    conversation = scoped_conversation(db, p, body.conversation_id)
    if conversation.state == "human_active":
        raise HTTPException(status.HTTP_409_CONFLICT, "human_controls_conversation")
    order = OperationsClient().get_order(p.workspace_id, p.customer_id, body.order_reference)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not_found")
    item = next((x for x in order["items"] if x["reference"] == body.item_reference), None)
    if not item:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "item_not_found")
    policy_version = "demo-support-v1"
    if body.kind == "return_request":
        delivered = (
            datetime.fromisoformat(order["delivered_at"]).date()
            if order.get("delivered_at")
            else None
        )
        result = evaluate_return(
            delivered_on=delivered,
            today=datetime.now(UTC).date(),
            ordered_quantity=item["quantity"],
            requested_quantity=body.quantity,
            reason=body.reason,
        )
        if not result.eligible:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                {"code": "ineligible", "reasons": result.codes},
            )
        policy_version = result.policy_version
    payload = body.model_dump(exclude={"conversation_id", "kind"}) | {
        "workspace_id": p.workspace_id,
        "customer_id": p.customer_id,
    }
    proposal = Proposal(
        workspace_id=p.workspace_id,
        conversation_id=conversation.id,
        customer_id=p.customer_id,
        kind=body.kind,
        payload=payload,
        payload_hash=canonical_hash(payload),
        policy_version=policy_version,
        order_version=order["version"],
        state=ProposalState.awaiting_customer,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db.add(proposal)
    db.flush()
    audit(db, p.workspace_id, p.user_id, "proposal.created", proposal.id, revision=1)
    db.commit()
    return {
        "id": proposal.id,
        "revision": proposal.revision,
        "state": proposal.state,
        "payload": proposal.payload,
        "effect": "Creates a support case"
        if body.kind == "support_case"
        else "Creates a return request for analysis",
    }


def scoped_proposal(db: Session, p, proposal_id: str) -> Proposal:
    query = select(Proposal).where(
        Proposal.id == proposal_id, Proposal.workspace_id == p.workspace_id
    )
    if p.role == Role.customer:
        query = query.where(Proposal.customer_id == p.customer_id)
    result = db.scalar(query)
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not_found")
    return result


def queue_action(db: Session, proposal: Proposal, actor_id: str) -> Action:
    existing = db.scalar(
        select(Action).where(
            Action.proposal_id == proposal.id, Action.proposal_revision == proposal.revision
        )
    )
    if existing:
        return existing
    action = Action(
        workspace_id=proposal.workspace_id,
        proposal_id=proposal.id,
        proposal_revision=proposal.revision,
        kind=proposal.kind,
        payload=proposal.payload,
        payload_hash=proposal.payload_hash,
        idempotency_key=f"serviceops:{proposal.id}:{proposal.revision}",
    )
    db.add(action)
    db.flush()
    audit(db, proposal.workspace_id, actor_id, "action.queued", action.id, proposal_id=proposal.id)
    return action


@app.post("/api/v1/proposals/{proposal_id}/confirm")
def confirm(
    proposal_id: str, request: Request, p=Depends(principal), db: Session = Depends(db_session)
) -> dict[str, object]:
    require_csrf(request)
    if p.role != Role.customer:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "customer_required")
    proposal = scoped_proposal(db, p, proposal_id)
    if proposal.expires_at <= datetime.now(UTC):
        proposal.state = ProposalState.expired
        db.commit()
        raise HTTPException(status.HTTP_409_CONFLICT, "proposal_expired")
    if proposal.state not in {
        ProposalState.awaiting_customer,
        ProposalState.awaiting_supervisor,
        ProposalState.approved,
    }:
        raise HTTPException(status.HTTP_409_CONFLICT, "invalid_state")
    proposal.customer_confirmed_by = p.user_id
    proposal.state = (
        ProposalState.awaiting_supervisor
        if proposal.kind == "return_request"
        else ProposalState.approved
    )
    action = (
        queue_action(db, proposal, p.user_id) if proposal.state == ProposalState.approved else None
    )
    audit(
        db,
        p.workspace_id,
        p.user_id,
        "proposal.customer_confirmed",
        proposal.id,
        revision=proposal.revision,
    )
    db.commit()
    return {"state": proposal.state, "action_id": action.id if action else None}


@app.post("/api/v1/proposals/{proposal_id}/approve")
def approve(
    proposal_id: str, request: Request, p=Depends(principal), db: Session = Depends(db_session)
) -> dict[str, object]:
    require_csrf(request)
    if p.role != Role.supervisor:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "supervisor_required")
    proposal = scoped_proposal(db, p, proposal_id)
    if proposal.kind != "return_request" or proposal.state not in {
        ProposalState.awaiting_supervisor,
        ProposalState.approved,
    }:
        raise HTTPException(status.HTTP_409_CONFLICT, "invalid_state")
    if not proposal.customer_confirmed_by or proposal.expires_at <= datetime.now(UTC):
        raise HTTPException(status.HTTP_409_CONFLICT, "confirmation_invalid")
    proposal.supervisor_approved_by = p.user_id
    proposal.state = ProposalState.approved
    action = queue_action(db, proposal, p.user_id)
    audit(
        db,
        p.workspace_id,
        p.user_id,
        "proposal.supervisor_approved",
        proposal.id,
        revision=proposal.revision,
    )
    db.commit()
    return {"state": proposal.state, "action_id": action.id}


@app.post("/api/v1/conversations/{conversation_id}/handoff")
def handoff(
    conversation_id: str, request: Request, p=Depends(principal), db: Session = Depends(db_session)
) -> dict[str, str]:
    require_csrf(request)
    conversation = scoped_conversation(db, p, conversation_id)
    conversation.state = "human_active"
    conversation.owner_user_id = p.user_id if p.role in {Role.operator, Role.supervisor} else None
    audit(db, p.workspace_id, p.user_id, "conversation.handoff", conversation.id)
    db.commit()
    return {"state": conversation.state}


@app.get("/api/v1/actions/{action_id}")
def get_action(
    action_id: str, p=Depends(principal), db: Session = Depends(db_session)
) -> dict[str, object]:
    action = db.scalar(
        select(Action).where(Action.id == action_id, Action.workspace_id == p.workspace_id)
    )
    if not action:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not_found")
    proposal = scoped_proposal(db, p, action.proposal_id)
    return {
        "id": action.id,
        "state": action.state,
        "external_reference": action.external_reference,
        "attempts": action.attempts,
        "proposal_id": proposal.id,
    }


app.mount(
    "/static",
    __import__("fastapi.staticfiles", fromlist=["StaticFiles"]).StaticFiles(
        directory="src/serviceops/web/static"
    ),
    name="static",
)
