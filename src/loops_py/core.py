from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from json import JSONDecodeError
from typing import Any, Callable, Dict, List, Literal, Mapping, Sequence, Type, TypeVar, Union
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pydantic import BaseModel

from .exceptions import LoopsAPIError, LoopsError

TModel = TypeVar("TModel", bound=BaseModel)
ResponseMode = Literal["model", "json"]


@dataclass
class HttpRequest:
    method: str
    url: str
    headers: Dict[str, str]
    body: bytes | None
    timeout: float


@dataclass
class HttpResponse:
    status: int
    body: bytes
    headers: Dict[str, str]


Transport = Callable[[HttpRequest], HttpResponse]


def urllib_transport(req: HttpRequest) -> HttpResponse:
    request = Request(url=req.url, method=req.method, headers=req.headers, data=req.body)
    try:
        with urlopen(request, timeout=req.timeout) as response:
            return HttpResponse(
                status=response.status,
                body=response.read(),
                headers={k.lower(): v for k, v in response.headers.items()},
            )
    except HTTPError as exc:
        return HttpResponse(
            status=exc.code,
            body=exc.read(),
            headers={k.lower(): v for k, v in exc.headers.items()},
        )
    except URLError as exc:
        raise LoopsError(f"Network error calling Loops API: {exc.reason}") from exc


class LoopsCore:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str,
        timeout: float,
        response_mode: ResponseMode,
        transport: Transport | None,
        max_retries: int,
        retry_backoff_base: float,
        retry_backoff_max: float,
        retry_jitter: float,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.response_mode = response_mode
        self.transport = transport or urllib_transport
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.retry_backoff_max = retry_backoff_max
        self.retry_jitter = retry_jitter

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        payload: Mapping[str, Any] | BaseModel | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        query_str = ""
        if query:
            cleaned_query = {k: v for k, v in query.items() if v is not None}
            if cleaned_query:
                query_str = "?" + urlencode(cleaned_query)

        url = f"{self.base_url}{path}{query_str}"
        merged_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        if payload is not None:
            merged_headers["Content-Type"] = "application/json"
        if headers:
            merged_headers.update(headers)

        body: bytes | None = None
        if payload is not None:
            body = json.dumps(self.to_payload(payload)).encode("utf-8")

        attempt = 0
        while True:
            response = self.transport(
                HttpRequest(
                    method=method,
                    url=url,
                    headers=merged_headers,
                    body=body,
                    timeout=self.timeout,
                )
            )

            if response.status == 429 and attempt < self.max_retries:
                delay_seconds = self._retry_delay_seconds(attempt, response.headers)
                time.sleep(delay_seconds)
                attempt += 1
                continue

            parsed, raw_text = self.parse_json_best_effort(response.body)
            if response.status >= 400:
                message = "Unknown error"
                if isinstance(parsed, dict):
                    message = str(parsed.get("message") or parsed.get("error") or message)
                elif raw_text:
                    message = raw_text[:300]
                raise LoopsAPIError(
                    status_code=response.status,
                    message=message,
                    response=parsed if parsed is not None else raw_text,
                    headers=response.headers,
                )

            # Some successful write operations can return empty or non-JSON bodies.
            if parsed is None and method in ("POST", "PUT", "PATCH", "DELETE"):
                result: dict[str, Any] = {"success": True}
                if raw_text:
                    result["raw"] = raw_text
                return result

            # Be lenient if the upstream responds with non-JSON text on success.
            if parsed is None and raw_text:
                return {"raw": raw_text}

            return parsed

    @staticmethod
    def to_payload(data: Mapping[str, Any] | BaseModel) -> Dict[str, Any]:
        if isinstance(data, BaseModel):
            return data.model_dump(by_alias=True, exclude_unset=True)
        if isinstance(data, Mapping):
            return dict(data)
        raise TypeError("request payload must be a pydantic model or mapping")

    @staticmethod
    def validate_request(
        data: Mapping[str, Any] | BaseModel,
        model_type: Type[TModel],
    ) -> TModel:
        if isinstance(data, model_type):
            return data
        if isinstance(data, Mapping):
            return model_type.model_validate(data)
        raise TypeError("request payload must be a pydantic model or mapping")

    @staticmethod
    def parse_json(raw: bytes) -> Any:
        if not raw:
            return None
        text = raw.decode("utf-8").strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LoopsError("Loops API returned invalid JSON") from exc

    @staticmethod
    def parse_json_best_effort(raw: bytes) -> tuple[Any, str]:
        if not raw:
            return None, ""
        text = raw.decode("utf-8", errors="replace").strip()
        if not text:
            return None, ""
        try:
            return json.loads(text), text
        except JSONDecodeError:
            return None, text

    def marshal_single(
        self,
        payload: Any,
        model_type: Type[TModel],
        as_json: bool | None,
    ) -> Union[TModel, Dict[str, Any]]:
        if self.is_json_mode(as_json):
            return payload
        return model_type.model_validate(payload)

    def marshal_list(
        self,
        payload: Any,
        item_type: Type[TModel],
        as_json: bool | None,
    ) -> Union[List[TModel], List[Dict[str, Any]]]:
        if self.is_json_mode(as_json):
            return payload
        if not isinstance(payload, Sequence):
            raise LoopsError("Expected list response from Loops API")
        return [item_type.model_validate(item) for item in payload]

    def is_json_mode(self, as_json: bool | None) -> bool:
        if as_json is not None:
            return as_json
        return self.response_mode == "json"

    def _retry_delay_seconds(
        self,
        attempt: int,
        response_headers: Mapping[str, str],
    ) -> float:
        retry_after = self._parse_retry_after(response_headers.get("retry-after"))
        if retry_after is not None:
            return retry_after

        delay = min(self.retry_backoff_max, self.retry_backoff_base * (2**attempt))
        if self.retry_jitter > 0:
            delay += random.uniform(0, delay * self.retry_jitter)
        return delay

    @staticmethod
    def _parse_retry_after(value: str | None) -> float | None:
        if not value:
            return None

        value = value.strip()
        try:
            seconds = float(value)
            return max(0.0, seconds)
        except ValueError:
            pass

        try:
            retry_time = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None

        now = datetime.now(timezone.utc)
        if retry_time.tzinfo is None:
            retry_time = retry_time.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_time - now).total_seconds())
