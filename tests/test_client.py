from __future__ import annotations

import json

import pytest

from loops_py.client import HttpRequest, HttpResponse, LoopsClient
from loops_py.exceptions import LoopsAPIError
from loops_py.models import ContactRequest, FindContactQuery, SendEventRequest


class StubTransport:
    def __init__(self) -> None:
        self.requests: list[HttpRequest] = []
        self.responses: list[HttpResponse] = []

    def queue(self, status: int, payload: object, headers: dict[str, str] | None = None) -> None:
        self.responses.append(
            HttpResponse(
                status=status,
                body=json.dumps(payload).encode("utf-8"),
                headers={k.lower(): v for k, v in (headers or {}).items()},
            )
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return self.responses.pop(0)


def test_create_contact_with_model_payload() -> None:
    transport = StubTransport()
    transport.queue(200, {"success": True, "id": "cont_123"})
    client = LoopsClient("test_key", transport=transport)

    result = client.create_contact(
        ContactRequest(email="a@example.com", first_name="Ada", user_id="usr_1")
    )

    request_body = json.loads(transport.requests[0].body.decode("utf-8"))
    assert request_body["firstName"] == "Ada"
    assert request_body["userId"] == "usr_1"
    assert result.id == "cont_123"


def test_create_contact_json_mode() -> None:
    transport = StubTransport()
    transport.queue(200, {"success": True, "id": "cont_456"})
    client = LoopsClient("test_key", transport=transport, response_mode="json")

    result = client.create_contact({"email": "b@example.com"})

    assert result["id"] == "cont_456"


def test_find_contact_requires_one_identifier() -> None:
    transport = StubTransport()
    client = LoopsClient("test_key", transport=transport)

    with pytest.raises(ValueError):
        client.find_contact(FindContactQuery(email="a@example.com", user_id="usr_1"))


def test_send_event_supports_idempotency_header() -> None:
    transport = StubTransport()
    transport.queue(200, {"success": True})
    client = LoopsClient("test_key", transport=transport)

    client.send_event(
        SendEventRequest(email="x@example.com", event_name="signup"),
        idempotency_key="event-1",
    )

    assert transport.requests[0].headers["Idempotency-Key"] == "event-1"


def test_list_transactional_emails_query() -> None:
    transport = StubTransport()
    transport.queue(
        200,
        {
            "pagination": {"nextCursor": "nxt_1"},
            "data": [
                {
                    "id": "tr_1",
                    "name": "Welcome",
                    "lastUpdated": "2026-01-01",
                    "dataVariables": [],
                }
            ],
        },
    )
    client = LoopsClient("test_key", transport=transport)

    result = client.list_transactional_emails(per_page=50, cursor="abc")

    assert "perPage=50" in transport.requests[0].url
    assert "cursor=abc" in transport.requests[0].url
    assert result.pagination.next_cursor == "nxt_1"


def test_verify_api_key_response() -> None:
    transport = StubTransport()
    transport.queue(200, {"success": True, "teamName": "Acme"})
    client = LoopsClient("test_key", transport=transport)

    result = client.verify_api_key()

    assert result.team_name == "Acme"


def test_api_error_raises_exception() -> None:
    transport = StubTransport()
    transport.queue(404, {"message": "Contact not found"})
    client = LoopsClient("test_key", transport=transport)

    with pytest.raises(LoopsAPIError) as exc:
        client.find_contact({"email": "missing@example.com"})

    assert exc.value.status_code == 404
    assert "Contact not found" in str(exc.value)


def test_rate_limit_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr("loops_py.core.time.sleep", sleep_calls.append)

    transport = StubTransport()
    transport.queue(429, {"message": "Rate limit exceeded"})
    transport.queue(200, {"success": True, "id": "cont_789"})
    client = LoopsClient("test_key", transport=transport, retry_jitter=0)

    result = client.create_contact({"email": "retry@example.com"})

    assert result.id == "cont_789"
    assert len(transport.requests) == 2
    assert sleep_calls == [0.25]


def test_rate_limit_retries_respect_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr("loops_py.core.time.sleep", sleep_calls.append)

    transport = StubTransport()
    transport.queue(
        429,
        {"message": "Rate limit exceeded"},
        headers={"Retry-After": "1.5"},
    )
    transport.queue(200, {"success": True, "id": "cont_999"})
    client = LoopsClient("test_key", transport=transport, retry_jitter=0)

    result = client.create_contact({"email": "retry-after@example.com"})

    assert result.id == "cont_999"
    assert sleep_calls == [1.5]


def test_rate_limit_exhausts_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr("loops_py.core.time.sleep", sleep_calls.append)

    transport = StubTransport()
    transport.queue(429, {"message": "Rate limit exceeded"})
    transport.queue(429, {"message": "Rate limit exceeded"})
    transport.queue(429, {"message": "Rate limit exceeded"})
    client = LoopsClient("test_key", transport=transport, max_retries=2, retry_jitter=0)

    with pytest.raises(LoopsAPIError) as exc:
        client.create_contact({"email": "still-rate-limited@example.com"})

    assert exc.value.status_code == 429
    assert len(transport.requests) == 3
    assert sleep_calls == [0.25, 0.5]
