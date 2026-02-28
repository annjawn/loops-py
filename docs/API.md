# API Guide

This document explains how each Loops API area maps to `loops-py`, with links to the official Loops docs.

Official base reference: [https://loops.so/docs/api-reference](https://loops.so/docs/api-reference)

## Client configuration

```python
from loops_py import LoopsClient

client = LoopsClient(
    api_key="loops_api_key",
    timeout=30.0,
    response_mode="model",  # or "json"
    max_retries=3,
    retry_backoff_base=0.25,
    retry_backoff_max=4.0,
    retry_jitter=0.1,
)
```

`response_mode="model"` returns typed Pydantic models.
`response_mode="json"` returns raw dict/list payloads.

Retry/backoff notes:

- `429` responses are retried automatically with exponential backoff.
- `Retry-After` response header is used when provided.
- Set `max_retries=0` to disable retries.

## Contacts

Loops docs:

- [Create Contact](https://loops.so/docs/api-reference/create-contact)
- [Update Contact](https://loops.so/docs/api-reference/update-contact)
- [Find Contact](https://loops.so/docs/api-reference/find-contact)
- [Delete Contact](https://loops.so/docs/api-reference/delete-contact)

Library methods:

- `client.contacts.create_contact(...)`
- `client.contacts.update_contact(...)`
- `client.contacts.find_contact(...)`
- `client.contacts.delete_contact(...)`

Notes:

- `find_contact` requires exactly one identifier: `email` or `userId`.
- `update_contact` and `delete_contact` require at least one identifier.
- You can pass either Pydantic models or plain dict payloads.

Example:

```python
from loops_py import ContactRequest, DeleteContactRequest, FindContactQuery, UpdateContactRequest

created = client.contacts.create_contact(
    ContactRequest(email="user@example.com", first_name="User", user_id="usr_123")
)

updated = client.contacts.update_contact(
    UpdateContactRequest(email="user@example.com", subscribed=True)
)

found = client.contacts.find_contact(FindContactQuery(email="user@example.com"))

deleted = client.contacts.delete_contact(DeleteContactRequest(email="user@example.com"))
```

## Contact properties

Loops docs:

- [Create Contact Property](https://loops.so/docs/api-reference/create-contact-property)
- [List Contact Properties](https://loops.so/docs/api-reference/list-contact-properties)

Library methods:

- `client.contacts.create_contact_property(...)`
- `client.contacts.list_contact_properties(...)`

Example:

```python
from loops_py import CreateContactPropertyRequest

client.contacts.create_contact_property(
    CreateContactPropertyRequest(name="plan", type="string")
)

properties = client.contacts.list_contact_properties(list_type="custom")
```

## Mailing lists

Loops docs:

- [List Mailing Lists](https://loops.so/docs/api-reference/list-mailing-lists)

Library method:

- `client.mailing_lists.list_mailing_lists()`

Example:

```python
lists = client.mailing_lists.list_mailing_lists()
```

## Events

Loops docs:

- [Send Event](https://loops.so/docs/api-reference/send-event)

Library method:

- `client.events.send_event(...)`

Notes:

- Supports `idempotency_key` for safe retries.
- Event payload can include `eventProperties` and optional `mailingLists` map.

Example:

```python
from loops_py import SendEventRequest

client.events.send_event(
    SendEventRequest(
        email="user@example.com",
        event_name="signup",
        event_properties={"source": "ads", "campaign": "spring"},
    ),
    idempotency_key="evt-user@example.com-signup-2026-02-28",
)
```

## Transactional emails

Loops docs:

- [Send Transactional Email](https://loops.so/docs/api-reference/send-transactional-email)
- [List Transactional Emails](https://loops.so/docs/api-reference/list-transactional-emails)

Library methods:

- `client.transactional.send_transactional_email(...)`
- `client.transactional.list_transactional_emails(...)`

Notes:

- `send_transactional_email` supports attachments and `idempotency_key`.
- `list_transactional_emails` supports pagination via `per_page` and `cursor`.

Example:

```python
from loops_py import SendTransactionalEmailRequest

client.transactional.send_transactional_email(
    SendTransactionalEmailRequest(
        transactional_id="cm0asdf123",
        email="user@example.com",
        data_variables={"name": "User"},
    ),
    idempotency_key="txn-user@example.com-cm0asdf123-2026-02-28",
)

result = client.transactional.list_transactional_emails(per_page=50)
next_cursor = result.pagination.next_cursor
```

## Account and infrastructure

Loops docs:

- [API Key](https://loops.so/docs/api-reference/api-key)
- [Dedicated Sending IPs](https://loops.so/docs/api-reference/dedicated-sending-ips)

Library methods:

- `client.account.verify_api_key()`
- `client.account.list_dedicated_sending_ips()`

Example:

```python
api_key_status = client.account.verify_api_key()
ips = client.account.list_dedicated_sending_ips()
```

## JSON response mode

Set JSON mode globally:

```python
client = LoopsClient(api_key="loops_api_key", response_mode="json")
raw_lists = client.mailing_lists.list_mailing_lists()
```

Or per call:

```python
raw_lists = client.mailing_lists.list_mailing_lists(as_json=True)
typed_lists = client.mailing_lists.list_mailing_lists(as_json=False)
```

## Error handling

`loops-py` raises `LoopsAPIError` for non-2xx responses.

```python
from loops_py import LoopsAPIError

try:
    client.contacts.find_contact({"email": "missing@example.com"})
except LoopsAPIError as exc:
    print(exc.status_code)
    print(exc.message)
    print(exc.response)
```
