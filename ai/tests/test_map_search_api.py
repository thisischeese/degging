import asyncio
import json
import unittest
from dataclasses import dataclass
from uuid import UUID

from fastapi import FastAPI

from app.models.map_search import MapSearchResponse
from app.routers import ai_router
from app.routers.map import get_map_search_service
from app.services.preference_vector import UserPreferenceNotFoundError


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

    def post(self, path: str, json_body: dict) -> ASGIResponse:
        return asyncio.run(self._request("POST", path, json_body))

    async def _request(self, method: str, path: str, json_body: dict) -> ASGIResponse:
        body = json.dumps(json_body).encode("utf-8")
        headers = [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
        ]
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


class FakeMapSearchService:
    def __init__(
        self,
        response: MapSearchResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self._response = response or MapSearchResponse()
        self._error = error
        self.last_keyword: str | None = None

    async def search(self, request) -> MapSearchResponse:
        self.last_keyword = request.keyword
        if self._error is not None:
            raise self._error
        return self._response


class MapSearchAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(ai_router)
        self.client = ASGITestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_map_search_success_response(self) -> None:
        fake_service = FakeMapSearchService(
            response=MapSearchResponse(
                cafes={
                    "123e4567-e89b-12d3-a456-426614174001": 1,
                    "123e4567-e89b-12d3-a456-426614174002": 2,
                },
                extracted_menus={"2394": 1, "10209": 3},
            )
        )
        self.app.dependency_overrides[get_map_search_service] = lambda: fake_service

        response = self.client.post(
            "/ai/map/search",
            {
                "mood": [0, 1, 2],
                "userId": "123e4567-e89b-12d3-a456-426614174000",
                "keyword": "  ",
                "latitude": 37.5665,
                "longitude": 126.978,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "cafes": {
                    "123e4567-e89b-12d3-a456-426614174001": 1,
                    "123e4567-e89b-12d3-a456-426614174002": 2,
                },
                "extracted_menus": {"2394": 1, "10209": 3},
            },
        )
        self.assertEqual(fake_service.last_keyword, "")

    def test_map_search_returns_404_when_preference_missing(self) -> None:
        fake_service = FakeMapSearchService(
            error=UserPreferenceNotFoundError("missing preference vector")
        )
        self.app.dependency_overrides[get_map_search_service] = lambda: fake_service

        response = self.client.post(
            "/ai/map/search",
            {
                "mood": [],
                "userId": "123e4567-e89b-12d3-a456-426614174000",
                "keyword": "",
                "latitude": 37.5665,
                "longitude": 126.978,
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "missing preference vector"})

    def test_map_search_rejects_invalid_latitude(self) -> None:
        fake_service = FakeMapSearchService()
        self.app.dependency_overrides[get_map_search_service] = lambda: fake_service

        response = self.client.post(
            "/ai/map/search",
            {
                "mood": [],
                "userId": str(UUID("123e4567-e89b-12d3-a456-426614174000")),
                "keyword": "",
                "latitude": 137.5665,
                "longitude": 126.978,
            },
        )

        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail[0]["loc"], ["body", "latitude"])
