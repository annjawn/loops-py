from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from loops_py import LoopsAPIError, LoopsClient

mcp = FastMCP("loops-api")


def _get_client() -> LoopsClient:
    api_key = os.getenv("LOOPS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("LOOPS_API_KEY is required")

    base_url = os.getenv("LOOPS_BASE_URL", "https://app.loops.so/api/v1")
    timeout = float(os.getenv("LOOPS_TIMEOUT", "30"))
    max_retries = int(os.getenv("LOOPS_MAX_RETRIES", "3"))
    retry_backoff_base = float(os.getenv("LOOPS_RETRY_BACKOFF_BASE", "0.25"))
    retry_backoff_max = float(os.getenv("LOOPS_RETRY_BACKOFF_MAX", "4.0"))
    retry_jitter = float(os.getenv("LOOPS_RETRY_JITTER", "0.1"))
    user_agent = os.getenv("LOOPS_USER_AGENT", "loops-mcp/1.0")

    return LoopsClient(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        response_mode="json",
        max_retries=max_retries,
        retry_backoff_base=retry_backoff_base,
        retry_backoff_max=retry_backoff_max,
        retry_jitter=retry_jitter,
        user_agent=user_agent,
    )


def _strip_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if v is not None}


def _execute(callable_name: str, fn: Any) -> Any:
    try:
        return fn()
    except LoopsAPIError as exc:
        raise RuntimeError(
            f"{callable_name} failed with status {exc.status_code}: {exc.message}"
        ) from exc


@mcp.tool()
def create_contact(
    email: str,
    first_name: str | None = None,
    last_name: str | None = None,
    subscribed: bool | None = None,
    user_group: str | None = None,
    user_id: str | None = None,
    mailing_lists: dict[str, bool] | None = None,
    source: str | None = None,
    custom_properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a contact in Loops."""

    payload = _strip_none(
        {
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "subscribed": subscribed,
            "userGroup": user_group,
            "userId": user_id,
            "mailingLists": mailing_lists,
            "source": source,
        }
    )
    if custom_properties:
        payload.update(custom_properties)

    client = _get_client()
    return _execute("create_contact", lambda: client.create_contact(payload, as_json=True))


@mcp.tool()
def update_contact(
    email: str | None = None,
    user_id: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    subscribed: bool | None = None,
    user_group: str | None = None,
    mailing_lists: dict[str, bool] | None = None,
    source: str | None = None,
    custom_properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update an existing contact in Loops."""

    payload = _strip_none(
        {
            "email": email,
            "userId": user_id,
            "firstName": first_name,
            "lastName": last_name,
            "subscribed": subscribed,
            "userGroup": user_group,
            "mailingLists": mailing_lists,
            "source": source,
        }
    )
    if custom_properties:
        payload.update(custom_properties)

    client = _get_client()
    return _execute("update_contact", lambda: client.update_contact(payload, as_json=True))


@mcp.tool()
def find_contact(email: str | None = None, user_id: str | None = None) -> list[dict[str, Any]]:
    """Find a contact by email or userId."""

    payload = _strip_none({"email": email, "userId": user_id})
    client = _get_client()
    return _execute("find_contact", lambda: client.find_contact(payload, as_json=True))


@mcp.tool()
def delete_contact(email: str | None = None, user_id: str | None = None) -> dict[str, Any]:
    """Delete a contact by email or userId."""

    payload = _strip_none({"email": email, "userId": user_id})
    client = _get_client()
    return _execute("delete_contact", lambda: client.delete_contact(payload, as_json=True))


@mcp.tool()
def create_contact_property(
    name: str,
    property_type: str,
    label: str | None = None,
) -> dict[str, Any]:
    """Create a contact property in Loops."""

    payload = _strip_none({"name": name, "type": property_type, "label": label})
    client = _get_client()
    return _execute(
        "create_contact_property",
        lambda: client.create_contact_property(payload, as_json=True),
    )


@mcp.tool()
def list_contact_properties(list_type: str | None = None) -> list[dict[str, Any]]:
    """List contact properties."""

    client = _get_client()
    return _execute(
        "list_contact_properties",
        lambda: client.list_contact_properties(list_type=list_type, as_json=True),
    )


@mcp.tool()
def list_mailing_lists() -> list[dict[str, Any]]:
    """List mailing lists."""

    client = _get_client()
    return _execute("list_mailing_lists", lambda: client.list_mailing_lists(as_json=True))


@mcp.tool()
def send_event(
    event_name: str,
    email: str | None = None,
    user_id: str | None = None,
    event_properties: dict[str, Any] | None = None,
    mailing_lists: dict[str, bool] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Send an event to Loops."""

    payload = _strip_none(
        {
            "eventName": event_name,
            "email": email,
            "userId": user_id,
            "eventProperties": event_properties,
            "mailingLists": mailing_lists,
        }
    )
    client = _get_client()
    return _execute(
        "send_event",
        lambda: client.send_event(payload, idempotency_key=idempotency_key, as_json=True),
    )


@mcp.tool()
def send_transactional_email(
    transactional_id: str,
    email: str,
    data_variables: dict[str, Any] | None = None,
    add_to_audience: bool | None = None,
    attachments: list[dict[str, Any]] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Send a transactional email."""

    payload = _strip_none(
        {
            "transactionalId": transactional_id,
            "email": email,
            "dataVariables": data_variables,
            "addToAudience": add_to_audience,
            "attachments": attachments,
        }
    )
    client = _get_client()
    return _execute(
        "send_transactional_email",
        lambda: client.send_transactional_email(
            payload,
            idempotency_key=idempotency_key,
            as_json=True,
        ),
    )


@mcp.tool()
def list_transactional_emails(
    per_page: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """List transactional email templates."""

    client = _get_client()
    return _execute(
        "list_transactional_emails",
        lambda: client.list_transactional_emails(per_page=per_page, cursor=cursor, as_json=True),
    )


@mcp.tool()
def verify_api_key() -> dict[str, Any]:
    """Verify current Loops API key."""

    client = _get_client()
    return _execute("verify_api_key", lambda: client.verify_api_key(as_json=True))


@mcp.tool()
def list_dedicated_sending_ips() -> list[str]:
    """List dedicated sending IPs."""

    client = _get_client()
    return _execute("list_dedicated_sending_ips", lambda: client.list_dedicated_sending_ips())


if __name__ == "__main__":
    mcp.run()
