import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import insert, select

from sandbox.operations_api.app import engine as operations_engine
from sandbox.operations_api.app import metadata, orders
from serviceops.auth.security import hash_password
from serviceops.domain.models import Base, Conversation, Membership, Role, User, Workspace
from serviceops.persistence.database import SessionLocal, engine

WS_A = "10000000-0000-0000-0000-000000000001"
WS_B = "20000000-0000-0000-0000-000000000001"
CUST_A = "10000000-0000-0000-0000-000000000101"
CUST_B = "10000000-0000-0000-0000-000000000102"


def seed_app() -> None:
    Base.metadata.create_all(engine)
    password = os.getenv("SERVICEOPS_DEMO_PASSWORD", "Demo-Only-Change-Me")
    with SessionLocal.begin() as db:
        if db.get(Workspace, WS_A):
            return
        db.add_all(
            [
                Workspace(id=WS_A, name="Distribuidora Aurora (fictícia)"),
                Workspace(id=WS_B, name="Comercial Horizonte (fictícia)"),
            ]
        )
        db.flush()
        specs = [
            ("ana@demo.invalid", "Ana Cliente", Role.customer, CUST_A, WS_A),
            ("bruno@demo.invalid", "Bruno Cliente", Role.customer, CUST_B, WS_A),
            ("operador@demo.invalid", "Olívia Operações", Role.operator, None, WS_A),
            ("supervisor@demo.invalid", "Sérgio Supervisor", Role.supervisor, None, WS_A),
            (
                "cliente@horizonte.invalid",
                "Helena Cliente",
                Role.customer,
                "20000000-0000-0000-0000-000000000101",
                WS_B,
            ),
        ]
        for i, (email, name, role, customer, workspace) in enumerate(specs, 1):
            uid = f"30000000-0000-0000-0000-{i:012d}"
            db.add(
                User(id=uid, email=email, password_hash=hash_password(password), display_name=name)
            )
            db.flush()
            db.add(Membership(workspace_id=workspace, user_id=uid, role=role, customer_id=customer))
            if customer:
                db.add(Conversation(workspace_id=workspace, customer_id=customer))


def seed_operations() -> None:
    metadata.create_all(operations_engine)
    delivered = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    fixtures = [
        (
            WS_A,
            CUST_A,
            "AUR-1001",
            {
                "status": "delivered",
                "delivered_at": delivered,
                "estimated_delivery": None,
                "currency": "BRL",
                "total": "249.90",
                "items": [{"reference": "ITEM-1", "name": "Cafeteira Demo", "quantity": 2}],
            },
            "v1",
        ),
        (
            WS_A,
            CUST_B,
            "AUR-2001",
            {
                "status": "in_transit",
                "delivered_at": None,
                "estimated_delivery": (datetime.now(UTC) + timedelta(days=2)).date().isoformat(),
                "currency": "BRL",
                "total": "89.50",
                "items": [{"reference": "ITEM-9", "name": "Luminária Demo", "quantity": 1}],
            },
            "v3",
        ),
    ]
    with operations_engine.begin() as conn:
        for i, (workspace, customer, reference, data, version) in enumerate(fixtures, 1):
            if not conn.execute(select(orders.c.id).where(orders.c.reference == reference)).first():
                conn.execute(
                    insert(orders).values(
                        id=f"40000000-0000-0000-0000-{i:012d}",
                        workspace_id=workspace,
                        customer_id=customer,
                        reference=reference,
                        data=data,
                        version=version,
                    )
                )


if __name__ == "__main__":
    seed_app()
    seed_operations()
    print("Synthetic demo data ready")
