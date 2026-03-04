from __future__ import annotations

import httpx


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
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: object = None,
    ) -> httpx.Response:
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
