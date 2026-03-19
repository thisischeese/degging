import asyncio
import json
import unittest
from dataclasses import dataclass

from fastapi import FastAPI

from app.routers import ai_router


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


class QueryPreprocessAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = FastAPI()
        app.include_router(ai_router)
        cls.client = ASGITestClient(app)

    def test_query_preprocess_success_response(self) -> None:
        response = self.client.post(
            "/ai/cafe/query-preprocess",
            {
                "query": "  햇살 좋은 두준국과 커피 맛집  ",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "data": {
                    "original_query": "햇살 좋은 두준국과 커피 맛집",
                    "vector": [],
                    "dimensions": 0,
                    "extracted_menus": [],
                    "menu_count": 0,
                },
            },
        )

    def test_query_preprocess_rejects_blank_query(self) -> None:
        response = self.client.post(
            "/ai/cafe/query-preprocess",
            {
                "query": "   ",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
            },
        )

        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail[0]["loc"], ["body", "query"])

    def test_query_preprocess_rejects_invalid_uuid(self) -> None:
        response = self.client.post(
            "/ai/cafe/query-preprocess",
            {
                "query": "커피",
                "user_id": "not-a-uuid",
            },
        )

        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail[0]["loc"], ["body", "user_id"])
