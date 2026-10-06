from typing import Any

import httpx

from serviceops.settings import get_settings


class OperationsClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.operations_url
        self.headers = {"Authorization": f"Bearer {settings.operations_token}"}

    def get_order(
        self, workspace_id: str, customer_id: str, reference: str
    ) -> dict[str, Any] | None:
        with httpx.Client(timeout=5, follow_redirects=False) as client:
            response = client.get(
                f"{self.base_url}/v1/orders/{reference}",
                headers=self.headers,
                params={"workspace_id": workspace_id, "customer_id": customer_id},
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        required = {"reference", "status", "version", "items"}
        if not required.issubset(data):
            raise ValueError("invalid_operations_response")
        return data

    def execute(self, kind: str, payload: dict[str, Any], key: str) -> dict[str, Any]:
        endpoint = "cases" if kind == "support_case" else "return-requests"
        headers = {**self.headers, "Idempotency-Key": key}
        if get_settings().inject_drop_after_commit:
            headers["X-Demo-Failure"] = "drop-after-commit"
        with httpx.Client(timeout=5, follow_redirects=False) as client:
            response = client.post(
                f"{self.base_url}/v1/{endpoint}",
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        if not isinstance(data.get("reference"), str):
            raise ValueError("invalid_operations_response")
        return data

    def reconcile(self, key: str) -> dict[str, Any] | None:
        with httpx.Client(timeout=5, follow_redirects=False) as client:
            response = client.get(f"{self.base_url}/v1/operations/{key}", headers=self.headers)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
