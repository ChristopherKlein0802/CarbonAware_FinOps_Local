"""Minimal httpx-compatible stub for environments without httpx."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class Timeout:
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout


class RequestError(Exception):
    pass


class TimeoutException(RequestError):
    pass


class HTTPStatusError(RequestError):
    def __init__(self, response: requests.Response) -> None:
        self.response = response
        super().__init__(f"HTTP {response.status_code}")


@dataclass
class _ResponseWrapper:
    status_code: int
    _json: Dict[str, Any]

    def json(self) -> Dict[str, Any]:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HTTPStatusError(type("R", (), {"status_code": self.status_code})())


class AsyncClient:
    def __init__(self, base_url: str = "", headers: Optional[Dict[str, str]] = None, timeout: Optional[Timeout] = None) -> None:
        self.base_url = base_url
        self.headers = headers or {}
        self.timeout = timeout.timeout if isinstance(timeout, Timeout) else timeout

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> _ResponseWrapper:
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> _ResponseWrapper:
        return await self._request("POST", endpoint, json=json, headers=headers)

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> _ResponseWrapper:
        def _do_request() -> _ResponseWrapper:
            try:
                response = requests.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    params=params,
                    json=json,
                    headers={**self.headers, **(headers or {})},
                    timeout=self.timeout,
                )
            except requests.Timeout as exc:
                raise TimeoutException(str(exc)) from exc
            except requests.RequestException as exc:  # pragma: no cover - network errors
                raise RequestError(str(exc)) from exc

            if response.status_code >= 400:
                err = HTTPStatusError(response)
                err.response = response
                raise err

            try:
                payload = response.json()
            except ValueError as exc:
                raise RequestError("Invalid JSON response") from exc

            return _ResponseWrapper(status_code=response.status_code, _json=payload)

        return await asyncio.to_thread(_do_request)


__all__ = [
    "AsyncClient",
    "Timeout",
    "RequestError",
    "TimeoutException",
    "HTTPStatusError",
]
