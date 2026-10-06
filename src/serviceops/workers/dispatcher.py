import os
import socket
import time
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import or_, select

from serviceops.domain.models import Action, ActionState, Proposal, ProposalState
from serviceops.integrations.operations import OperationsClient
from serviceops.persistence.database import SessionLocal

WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"


def claim_one() -> str | None:
    now = datetime.now(UTC)
    with SessionLocal.begin() as db:
        action = db.scalar(
            select(Action)
            .where(
                Action.state.in_(
                    [ActionState.queued, ActionState.unknown, ActionState.reconciling]
                ),
                Action.available_at <= now,
                or_(Action.lease_until.is_(None), Action.lease_until < now),
            )
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if not action:
            return None
        action.state = ActionState.in_flight
        action.lease_owner = WORKER_ID
        action.lease_until = now + timedelta(seconds=30)
        action.attempts += 1
        return action.id


def process(action_id: str) -> None:
    client = OperationsClient()
    with SessionLocal() as db:
        action = db.get(Action, action_id)
        if not action or action.lease_owner != WORKER_ID:
            return
        proposal = db.get(Proposal, action.proposal_id)
        if (
            not proposal
            or proposal.state != ProposalState.approved
            or proposal.payload_hash != action.payload_hash
        ):
            action.state = ActionState.failed
            action.error_code = "proposal_no_longer_valid"
            db.commit()
            return
        key, kind, payload, fence = (
            action.idempotency_key,
            action.kind,
            action.payload,
            action.lease_until,
        )
    try:
        existing = client.reconcile(key)
        result = existing or client.execute(kind, payload, key)
        state, error = ActionState.succeeded, None
    except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError):
        state, error, result = ActionState.unknown, "external_result_unknown", None
    with SessionLocal.begin() as db:
        action = db.scalar(select(Action).where(Action.id == action_id).with_for_update())
        if not action or action.lease_owner != WORKER_ID or action.lease_until != fence:
            return
        action.state = state
        action.error_code = error
        action.lease_owner = None
        action.lease_until = None
        action.updated_at = datetime.now(UTC)
        if result:
            action.external_reference = result["reference"]
        if state == ActionState.unknown:
            action.available_at = datetime.now(UTC) + timedelta(seconds=2)


def run() -> None:
    while True:
        action_id = claim_one()
        if action_id:
            process(action_id)
        else:
            time.sleep(1)


if __name__ == "__main__":
    run()
