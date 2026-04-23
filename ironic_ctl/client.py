"""
Thin wrapper around the OpenStack Ironic REST API.
Uses keystoneauth1 for token management when available,
falls back to direct token auth for standalone Ironic.
"""
import os
import httpx
from typing import Optional


class IronicClient:
    def __init__(self, endpoint: Optional[str] = None, token: Optional[str] = None):
        self.endpoint = (endpoint or os.environ["IRONIC_ENDPOINT"]).rstrip("/")
        self.token = token or os.environ.get("IRONIC_TOKEN", "")
        self._client = httpx.Client(
            base_url=self.endpoint,
            headers={"X-Auth-Token": self.token, "X-OpenStack-Ironic-API-Version": "1.82"},
            timeout=30,
        )

    def _get(self, path: str) -> dict:
        r = self._client.get(path)
        r.raise_for_status()
        return r.json()

    def _patch(self, path: str, ops: list[dict]) -> dict:
        r = self._client.patch(path, json=ops)
        r.raise_for_status()
        return r.json()

    def _put(self, path: str, **kwargs) -> httpx.Response:
        r = self._client.put(path, **kwargs)
        r.raise_for_status()
        return r

    def list_nodes(self, provision_state: Optional[str] = None) -> list[dict]:
        params = {"detail": "true"}
        if provision_state:
            params["provision_state"] = provision_state
        return self._get(f"/v1/nodes?{'&'.join(f'{k}={v}' for k,v in params.items())}")["nodes"]

    def get_node(self, node_id: str) -> dict:
        return self._get(f"/v1/nodes/{node_id}")

    def set_provision_state(self, node_id: str, target: str, clean_steps: Optional[list] = None):
        body: dict = {"target": target}
        if clean_steps:
            body["clean_steps"] = clean_steps
        r = self._client.put(f"/v1/nodes/{node_id}/states/provision", json=body)
        r.raise_for_status()

    def set_power_state(self, node_id: str, target: str):
        r = self._client.put(f"/v1/nodes/{node_id}/states/power", json={"target": target})
        r.raise_for_status()

    def update_node(self, node_id: str, ops: list[dict]) -> dict:
        return self._patch(f"/v1/nodes/{node_id}", ops)

    def get_node_bios(self, node_id: str) -> dict:
        return self._get(f"/v1/nodes/{node_id}/bios")
