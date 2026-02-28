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

    def queue(self, status: int, payload: object) -> None:
        self.responses.append(HttpResponse(status=status, body=json.dumps(payload).encode("utf-8")))

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
