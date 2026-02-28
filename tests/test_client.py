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

    def queue_raw(self, status: int, body: bytes, headers: dict[str, str] | None = None) -> None:
        self.responses.append(
            HttpResponse(
                status=status,
                body=body,
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


def test_update_contact_uses_post_method() -> None:
    transport = StubTransport()
    transport.queue(200, {"success": True, "id": "cont_123"})
    client = LoopsClient("test_key", transport=transport)

    client.update_contact({"email": "a@example.com", "firstName": "Ada"})

    assert transport.requests[0].method == "POST"
    assert transport.requests[0].url.endswith("/contacts/update")


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


def test_default_user_agent_header_is_sent() -> None:
    transport = StubTransport()
    transport.queue(200, {"success": True, "id": "cont_123"})
    client = LoopsClient("test_key", transport=transport)

    client.create_contact({"email": "ua@example.com"})

    assert transport.requests[0].headers["User-Agent"] == "pyloops-so/0.1"


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


def test_list_mailing_lists_uses_lists_endpoint() -> None:
    transport = StubTransport()
    transport.queue(200, [])
    client = LoopsClient("test_key", transport=transport)

    client.list_mailing_lists()

    assert transport.requests[0].url.endswith("/lists")


def test_verify_api_key_response() -> None:
    transport = StubTransport()
    transport.queue(200, {"success": True, "teamName": "Acme"})
    client = LoopsClient("test_key", transport=transport)

    result = client.verify_api_key()

    assert result.team_name == "Acme"


def test_list_dedicated_sending_ips_returns_strings() -> None:
    transport = StubTransport()
    transport.queue(200, ["1.2.3.4", "5.6.7.8"])
    client = LoopsClient("test_key", transport=transport)

    result = client.list_dedicated_sending_ips()

    assert result == ["1.2.3.4", "5.6.7.8"]


def test_api_error_raises_exception() -> None:
    transport = StubTransport()
    transport.queue(404, {"message": "Contact not found"})
    client = LoopsClient("test_key", transport=transport)

    with pytest.raises(LoopsAPIError) as exc:
        client.find_contact({"email": "missing@example.com"})

    assert exc.value.status_code == 404
    assert "Contact not found" in str(exc.value)


def test_delete_contact_accepts_success_only_response() -> None:
    transport = StubTransport()
    transport.queue(200, {"success": True})
    client = LoopsClient("test_key", transport=transport)

    result = client.delete_contact({"email": "ok@example.com"})

    assert result.success is True


def test_empty_success_body_is_handled_for_write_requests() -> None:
    transport = StubTransport()
    transport.queue_raw(200, b"")
    client = LoopsClient("test_key", transport=transport)

    result = client.send_transactional_email(
        {
            "transactionalId": "cmm5c7m3w0hvs0j31wr0mqj1v",
            "email": "user@example.com",
            "dataVariables": {"code": "292929"},
        }
    )

    assert result.success is True


def test_non_json_success_body_is_handled_for_write_requests() -> None:
    transport = StubTransport()
    transport.queue_raw(200, b"ok")
    client = LoopsClient("test_key", transport=transport)

    result = client.send_transactional_email(
        {
            "transactionalId": "cmm5c7m3w0hvs0j31wr0mqj1v",
            "email": "user@example.com",
            "dataVariables": {"code": "292929"},
        },
        as_json=True,
    )

    assert result["success"] is True
    assert result["raw"] == "ok"


def test_non_json_error_body_raises_api_error() -> None:
    transport = StubTransport()
    transport.queue_raw(500, b"Internal Server Error")
    client = LoopsClient("test_key", transport=transport)

    with pytest.raises(LoopsAPIError) as exc:
        client.send_transactional_email(
            {
                "transactionalId": "cmm5c7m3w0hvs0j31wr0mqj1v",
                "email": "user@example.com",
                "dataVariables": {"code": "292929"},
            }
        )

    assert exc.value.status_code == 500
    assert "Internal Server Error" in exc.value.message


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
