import asyncio
import json
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI


@dataclass
class ASGIResponse:
    status_code: int
    headers: list[tuple[str, str]]
    body: bytes

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8"))


class ASGITestClient:
    def __init__(self, app: FastAPI) -> None:
        self._app = app

    def post(self, path: str, json_body: Any) -> ASGIResponse:
        return asyncio.run(self._request("POST", path, json_body))

    async def _request(self, method: str, path: str, json_body: Any) -> ASGIResponse:
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

        async def receive() -> dict[str, Any]:
            if request_messages:
                return request_messages.pop(0)
            await asyncio.sleep(0)
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict[str, Any]) -> None:
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
