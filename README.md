# Unofficial Loops.so Python Library (`loops-py`)

`loops-py` is a lightweight Python SDK for the [Loops API](https://loops.so/docs/api-reference), designed for production usage with minimal dependencies.

## Why this library

- Complete support for [Loops.so](https://loops.so) endpoints
- Typed request/response models via Pydantic
- Optional raw JSON mode when you want plain dictionaries
- Single runtime dependency (`pydantic`)
- Small, composable client structure (`contacts`, `events`, `transactional`, etc.)

## Loops API docs

Official Loops API reference: [https://loops.so/docs/api-reference](https://loops.so/docs/api-reference)

Endpoint docs covered by this SDK:

- [Create Contact](https://loops.so/docs/api-reference/create-contact)
- [Update Contact](https://loops.so/docs/api-reference/update-contact)
- [Find Contact](https://loops.so/docs/api-reference/find-contact)
- [Delete Contact](https://loops.so/docs/api-reference/delete-contact)
- [Create Contact Property](https://loops.so/docs/api-reference/create-contact-property)
- [List Contact Properties](https://loops.so/docs/api-reference/list-contact-properties)
- [List Mailing Lists](https://loops.so/docs/api-reference/list-mailing-lists)
- [Send Event](https://loops.so/docs/api-reference/send-event)
- [Send Transactional Email](https://loops.so/docs/api-reference/send-transactional-email)
- [List Transactional Emails](https://loops.so/docs/api-reference/list-transactional-emails)
- [API Key](https://loops.so/docs/api-reference/api-key)
- [Dedicated Sending IPs](https://loops.so/docs/api-reference/dedicated-sending-ips)

## Installation

Install from PyPI:

```bash
uv add loops-py
```

For local development:

```bash
uv sync --extra dev
```

## Authentication

Loops uses Bearer auth for all endpoints:

```http
Authorization: Bearer {api_key}
```

Create a client once and reuse it:

```python
from loops_py import LoopsClient

client = LoopsClient(api_key="loops_api_key")
```

## Usage model

The SDK supports two call styles:

1. Top-level convenience methods (`client.create_contact(...)`) for compatibility.
2. Grouped service methods (`client.contacts.create_contact(...)`) for clearer organization.

Both call styles use the same underlying implementation.

## Typed mode (default)

By default, responses are returned as Pydantic models.

```python
from loops_py import ContactRequest, LoopsClient

client = LoopsClient(api_key="loops_api_key")

created = client.contacts.create_contact(
    ContactRequest(
        email="ada@example.com",
        first_name="Ada",
        user_id="usr_123",
        mailing_lists={"cll2pyfrx0000mm080fwnwdg0": True},
    )
)

print(created.success)
print(created.id)
```

## JSON mode

If you prefer raw dict/list responses, use `response_mode="json"`.

```python
from loops_py import LoopsClient

client = LoopsClient(api_key="loops_api_key", response_mode="json")
raw = client.account.verify_api_key()
print(raw["teamName"])
```

You can override per call:

```python
typed = client.account.verify_api_key(as_json=False)
raw = client.account.verify_api_key(as_json=True)
```

## Error handling

HTTP errors from Loops raise `LoopsAPIError` with status code and parsed response payload.

```python
from loops_py import LoopsAPIError

try:
    client.contacts.find_contact({"email": "missing@example.com"})
except LoopsAPIError as exc:
    print(exc.status_code)
    print(exc.response)
```

## Rate limit handling and retries

Loops applies request rate limits (baseline 10 requests/second/team) and can return `429`.
This SDK retries `429` responses automatically with exponential backoff.

Default retry behavior:

- `max_retries=3` (up to 4 total attempts)
- `retry_backoff_base=0.25` seconds
- `retry_backoff_max=4.0` seconds
- `retry_jitter=0.1` (10% random jitter)
- `Retry-After` header is honored when present

Configure it:

```python
from loops_py import LoopsClient

client = LoopsClient(
    api_key="loops_api_key",
    max_retries=5,
    retry_backoff_base=0.2,
    retry_backoff_max=6.0,
    retry_jitter=0.2,
)
```

Disable retries by setting `max_retries=0`.

## Endpoint mapping

- `contacts`
  - `create_contact` -> `POST /contacts/create`
  - `update_contact` -> `PUT /contacts/update`
  - `find_contact` -> `GET /contacts/find`
  - `delete_contact` -> `POST /contacts/delete`
  - `create_contact_property` -> `POST /contacts/properties`
  - `list_contact_properties` -> `GET /contacts/properties`
- `mailing_lists`
  - `list_mailing_lists` -> `GET /mailing-lists`
- `events`
  - `send_event` -> `POST /events/send`
- `transactional`
  - `send_transactional_email` -> `POST /transactional`
  - `list_transactional_emails` -> `GET /transactional`
- `account`
  - `verify_api_key` -> `GET /api-key`
  - `list_dedicated_sending_ips` -> `GET /dedicated-sending-ips`

## Idempotency support

For endpoints that support idempotency, pass `idempotency_key`:

```python
client.events.send_event(
    {"email": "user@example.com", "eventName": "signup"},
    idempotency_key="signup-user@example.com-2026-02-28",
)
```

## Build and publish

Build sdist + wheel:

```bash
uv build
```

Artifacts:

- `dist/*.tar.gz`
- `dist/*.whl`

Publish (requires PyPI token):

```bash
export UV_PUBLISH_TOKEN="pypi-..."
uv publish
```

TestPyPI:

```bash
uv publish --publish-url https://test.pypi.org/legacy/
```

## Development

```bash
uv run ruff check .
uv run pytest
```

## License

MIT
