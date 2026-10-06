import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    create_engine,
    insert,
    select,
)

DATABASE_URL = os.getenv(
    "OPERATIONS_DATABASE_URL",
    "postgresql+psycopg://operations:operations@localhost:5433/operations",
)
TOKEN = os.getenv("OPERATIONS_TOKEN", "local-sandbox-token")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
metadata = MetaData()
orders = Table(
    "orders",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("workspace_id", String(36), index=True),
    Column("customer_id", String(36), index=True),
    Column("reference", String(40), index=True),
    Column("data", JSON),
    Column("version", String(40)),
)
operations = Table(
    "operations",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("idempotency_key", String(100), unique=True),
    Column("payload_hash", String(64)),
    Column("kind", String(32)),
    Column("reference", String(100)),
    Column("payload", JSON),
    Column("created_at", DateTime(timezone=True)),
)
app = FastAPI(title="ServiceOps Operations Sandbox", version="0.1.0")


class OperationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_reference: str
    item_reference: str
    quantity: int
    reason: str
    details: str
    workspace_id: str
    customer_id: str


def authorize(authorization: str | None) -> None:
    import hmac

    if not authorization or not hmac.compare_digest(authorization, f"Bearer {TOKEN}"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_integration_credential")


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/v1/orders/{reference}")
def get_order(
    reference: str,
    workspace_id: str = Query(),
    customer_id: str = Query(),
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    authorize(authorization)
    with engine.begin() as conn:
        row = (
            conn.execute(
                select(orders).where(
                    orders.c.reference == reference,
                    orders.c.workspace_id == workspace_id,
                    orders.c.customer_id == customer_id,
                )
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not_found")
    return row["data"] | {"reference": row["reference"], "version": row["version"]}


def create_operation(
    kind: str, body: OperationInput, key: str | None, request: Request
) -> dict[str, Any]:
    if not key or len(key) > 100:
        raise HTTPException(400, "invalid_idempotency_key")
    payload = body.model_dump()
    payload_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with engine.begin() as conn:
        existing = (
            conn.execute(select(operations).where(operations.c.idempotency_key == key))
            .mappings()
            .first()
        )
        if existing:
            if existing["payload_hash"] != payload_hash:
                raise HTTPException(409, "idempotency_payload_conflict")
            return {"reference": existing["reference"], "status": "created", "deduplicated": True}
        order = (
            conn.execute(
                select(orders).where(
                    orders.c.reference == body.order_reference,
                    orders.c.workspace_id == body.workspace_id,
                    orders.c.customer_id == body.customer_id,
                )
            )
            .mappings()
            .first()
        )
        if not order:
            raise HTTPException(404, "not_found")
        prefix = "CASE" if kind == "support_case" else "RET"
        reference = f"{prefix}-{uuid.uuid4().hex[:10].upper()}"
        conn.execute(
            insert(operations).values(
                id=str(uuid.uuid4()),
                idempotency_key=key,
                payload_hash=payload_hash,
                kind=kind,
                reference=reference,
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )
    # Test-only local fault: commit is complete, then connection response is deliberately lost.
    if (
        request.headers.get("X-Demo-Failure") == "drop-after-commit"
        and os.getenv("OPERATIONS_ALLOW_FAILURE_INJECTION") == "true"
    ):
        raise HTTPException(599, "demo_response_lost_after_commit")
    return {"reference": reference, "status": "created", "deduplicated": False}


@app.post("/v1/cases")
def create_case(
    body: OperationInput,
    request: Request,
    authorization: str | None = Header(None),
    idempotency_key: str | None = Header(None),
) -> dict[str, Any]:
    authorize(authorization)
    return create_operation("support_case", body, idempotency_key, request)


@app.post("/v1/return-requests")
def create_return(
    body: OperationInput,
    request: Request,
    authorization: str | None = Header(None),
    idempotency_key: str | None = Header(None),
) -> dict[str, Any]:
    authorize(authorization)
    return create_operation("return_request", body, idempotency_key, request)


@app.get("/v1/operations/{key}")
def operation(key: str, authorization: str | None = Header(None)) -> dict[str, Any]:
    authorize(authorization)
    with engine.begin() as conn:
        row = (
            conn.execute(select(operations).where(operations.c.idempotency_key == key))
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(404, "not_found")
    return {"reference": row["reference"], "status": "created", "kind": row["kind"]}
