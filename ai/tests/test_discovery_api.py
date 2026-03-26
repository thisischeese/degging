import asyncio
import json
import unittest
from dataclasses import dataclass
from uuid import UUID

from fastapi import FastAPI

from app.routers import ai_router
from app.routers.discovery import get_discovery_service
from app.services.discovery_service import UserPreferenceNotFoundError


@dataclass
class ASGIResponse:
    status_code: int
    headers: list[tuple[str, str]]
    body: bytes

    def json(self) -> dict:
        return json.loads(self.body.decode("utf-8"))


class ASGITestClient:
    def __init__(self, app: FastAPI) -> None:
        self._app = app

    def get(self, path: str) -> ASGIResponse:
        return asyncio.run(self._request("GET", path))

    def post(self, path: str, json_body: dict) -> ASGIResponse:
        return asyncio.run(self._request("POST", path, json_body))

    async def _request(
        self,
        method: str,
        path: str,
        json_body: dict | None = None,
    ) -> ASGIResponse:
        body = (
            json.dumps(json_body).encode("utf-8")
            if json_body is not None
            else b""
        )
        headers = [(b"host", b"testserver")]
        if json_body is not None:
            headers.extend(
                [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ]
            )
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }

        request_messages = [{"type": "http.request", "body": body, "more_body": False}]
        response_status_code = 500
        response_headers: list[tuple[str, str]] = []
        response_body = bytearray()

        async def receive() -> dict:
            if request_messages:
                return request_messages.pop(0)
            await asyncio.sleep(0)
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict) -> None:
            nonlocal response_status_code, response_headers
            if message["type"] == "http.response.start":
                response_status_code = message["status"]
                response_headers = [
                    (key.decode("latin-1"), value.decode("latin-1"))
                    for key, value in message.get("headers", [])
                ]
            elif message["type"] == "http.response.body":
                response_body.extend(message.get("body", b""))

        await self._app(scope, receive, send)
        return ASGIResponse(
            status_code=response_status_code,
            headers=response_headers,
            body=bytes(response_body),
        )


class FakeDiscoveryService:
    def __init__(
        self,
        cafe_ids: list[UUID] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._cafe_ids = cafe_ids or []
        self._error = error
        self.last_user_id: UUID | None = None

    async def discover(self, user_id: UUID) -> list[UUID]:
        self.last_user_id = user_id
        if self._error is not None:
            raise self._error
        return self._cafe_ids


class DiscoveryAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(ai_router)
        self.client = ASGITestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_discovery_requires_post(self) -> None:
        response = self.client.get("/ai/discovery")

        self.assertEqual(response.status_code, 405)

    def test_discovery_returns_ranked_cafe_mapping(self) -> None:
        fake_service = FakeDiscoveryService(
            cafe_ids=[
                UUID("123e4567-e89b-12d3-a456-426614174001"),
                UUID("123e4567-e89b-12d3-a456-426614174002"),
            ]
        )
        self.app.dependency_overrides[get_discovery_service] = lambda: fake_service

        response = self.client.post(
            "/ai/discovery",
            {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "123e4567-e89b-12d3-a456-426614174001": 1,
                "123e4567-e89b-12d3-a456-426614174002": 2,
            },
        )
        self.assertEqual(
            fake_service.last_user_id,
            UUID("123e4567-e89b-12d3-a456-426614174000"),
        )

    def test_discovery_returns_404_when_preference_missing(self) -> None:
        fake_service = FakeDiscoveryService(
            error=UserPreferenceNotFoundError("missing preference vector")
        )
        self.app.dependency_overrides[get_discovery_service] = lambda: fake_service

        response = self.client.post(
            "/ai/discovery",
            {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "missing preference vector"})
