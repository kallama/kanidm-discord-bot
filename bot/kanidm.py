from __future__ import annotations

import logging
from types import TracebackType
from typing import Any

import httpx

log = logging.getLogger(__name__)


class KanidmError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Kanidm {status_code}: {detail}")


class KanidmClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> KanidmClient:
        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | list[str] | None = None,
    ) -> httpx.Response:
        log.info("%s %s", method, path)
        resp = await self._client.request(method, path, json=json)
        if not resp.is_success:
            detail = resp.text or resp.reason_phrase
            raise KanidmError(resp.status_code, detail)
        return resp

    async def create_person(
        self,
        username: str,
        display_name: str,
        email: str,
    ) -> str:
        """Create a person and return their UUID."""
        await self._request(
            "POST",
            "/v1/person",
            json={
                "attrs": {
                    "name": [username],
                    "displayname": [display_name],
                    "mail": [email],
                }
            },
        )
        resp = await self._request("GET", f"/v1/person/{username}")
        return resp.json()["attrs"]["uuid"][0]

    async def posix_enable_person(self, uuid: str) -> None:
        await self._request("POST", f"/v1/person/{uuid}/_unix", json={})

    async def add_to_group(self, group: str, uuid: str) -> None:
        await self._request(
            "POST",
            f"/v1/group/{group}/_attr/member",
            json=[uuid],
        )

    async def create_credential_reset_token(self, uuid: str) -> str:
        resp = await self._request(
            "GET",
            f"/v1/person/{uuid}/_credential/_update_intent",
        )
        return resp.json()["token"]
