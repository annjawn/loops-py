from __future__ import annotations

import os
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from loops_py import LoopsAPIError, LoopsClient
from loops_py.exceptions import LoopsError

_transport = os.getenv("MCP_TRANSPORT", "stdio")
_host = os.getenv("MCP_HOST", "0.0.0.0")
_port = int(os.getenv("MCP_PORT", "8000"))

mcp = FastMCP("loops-api", host=_host, port=_port)

_client: LoopsClient | None = None


def _get_client() -> LoopsClient:
    """Return a cached LoopsClient, creating one on first call."""
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("LOOPS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("LOOPS_API_KEY environment variable is required")

    _client = LoopsClient(
        api_key=api_key,
        base_url=os.getenv("LOOPS_BASE_URL", "https://app.loops.so/api/v1"),
        timeout=float(os.getenv("LOOPS_TIMEOUT", "30")),
        response_mode="json",
        max_retries=int(os.getenv("LOOPS_MAX_RETRIES", "3")),
        retry_backoff_base=float(os.getenv("LOOPS_RETRY_BACKOFF_BASE", "0.25")),
        retry_backoff_max=float(os.getenv("LOOPS_RETRY_BACKOFF_MAX", "4.0")),
        retry_jitter=float(os.getenv("LOOPS_RETRY_JITTER", "0.1")),
        user_agent=os.getenv("LOOPS_USER_AGENT", "loops-mcp/1.0"),
    )
    return _client


def _strip_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if v is not None}


def _execute(name: str, fn: Any) -> Any:
    try:
        return fn()
    except LoopsAPIError as exc:
        raise RuntimeError(
            f"{name} failed ({exc.status_code}): {exc.message}"
        ) from exc
    except ValidationError as exc:
        raise RuntimeError(f"{name} validation error: {exc}") from exc
    except LoopsError as exc:
        raise RuntimeError(f"{name} error: {exc}") from exc


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
    """Create a contact in Loops.

    Args:
        email: Contact email address (required).
        first_name: Contact's first name.
        last_name: Contact's last name.
        subscribed: Whether the contact is subscribed.
        user_group: Group to assign the contact to.
        user_id: Unique user identifier in your system.
        mailing_lists: Map of mailing list IDs to subscription status, e.g. {"list_id": true}.
        source: Source of the contact, e.g. "website".
        custom_properties: Arbitrary custom contact properties as key-value pairs.

    Returns:
        Dict with "success" (bool) and "id" (str) of the created contact.
    """

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
    """Update an existing contact in Loops.

    At least one of email or user_id is required to identify the contact.

    Args:
        email: Contact email address (identifier).
        user_id: Unique user identifier in your system (identifier).
        first_name: Contact's first name.
        last_name: Contact's last name.
        subscribed: Whether the contact is subscribed.
        user_group: Group to assign the contact to.
        mailing_lists: Map of mailing list IDs to subscription status, e.g. {"list_id": true}.
        source: Source of the contact.
        custom_properties: Arbitrary custom contact properties as key-value pairs.

    Returns:
        Dict with "success" (bool) and "id" (str) of the updated contact.
    """

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
    """Find a contact by email or user_id.

    Exactly one of email or user_id must be provided.

    Args:
        email: Contact email address.
        user_id: Unique user identifier in your system.

    Returns:
        List of matching contact dicts.
    """

    payload = _strip_none({"email": email, "userId": user_id})
    client = _get_client()
    return _execute("find_contact", lambda: client.find_contact(payload, as_json=True))


@mcp.tool()
def delete_contact(email: str | None = None, user_id: str | None = None) -> dict[str, Any]:
    """Delete a contact by email or user_id.

    At least one of email or user_id must be provided.

    Args:
        email: Contact email address.
        user_id: Unique user identifier in your system.

    Returns:
        Dict with "success" (bool) and "message" (str).
    """

    payload = _strip_none({"email": email, "userId": user_id})
    client = _get_client()
    return _execute("delete_contact", lambda: client.delete_contact(payload, as_json=True))


@mcp.tool()
def create_contact_property(
    name: str,
    property_type: Literal["string", "number", "boolean", "date"],
    label: str | None = None,
) -> dict[str, Any]:
    """Create a custom contact property in Loops.

    Args:
        name: Property name (key).
        property_type: Data type — must be one of: "string", "number", "boolean", "date".
        label: Human-readable label for the property. Defaults to name if omitted.

    Returns:
        Dict with "success" (bool).
    """

    payload = _strip_none({"name": name, "type": property_type, "label": label})
    client = _get_client()
    return _execute(
        "create_contact_property",
        lambda: client.create_contact_property(payload, as_json=True),
    )


@mcp.tool()
def list_contact_properties(list_type: str | None = None) -> list[dict[str, Any]]:
    """List contact properties.

    Args:
        list_type: Filter by property type — "custom" for user-created properties,
            "default" for built-in properties, or omit for all.

    Returns:
        List of property dicts with "key", "label", and "type" fields.
    """

    client = _get_client()
    return _execute(
        "list_contact_properties",
        lambda: client.list_contact_properties(list_type=list_type, as_json=True),
    )


@mcp.tool()
def list_mailing_lists() -> list[dict[str, Any]]:
    """List all mailing lists.

    Returns:
        List of mailing list dicts with "id", "name", "description", and "isPublic" fields.
    """

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
    """Send an event to Loops to trigger automations.

    At least one of email or user_id is required to identify the contact.

    Args:
        event_name: Name of the event to send.
        email: Contact email address.
        user_id: Unique user identifier in your system.
        event_properties: Arbitrary event data as key-value pairs.
        mailing_lists: Map of mailing list IDs to subscription status, e.g. {"list_id": true}.
        idempotency_key: Optional key for safe retries (prevents duplicate processing).

    Returns:
        Dict with "success" (bool).
    """

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
    """Send a transactional email via Loops.

    Args:
        transactional_id: ID of the transactional email template.
        email: Recipient email address.
        data_variables: Template variables as key-value pairs, e.g. {"name": "Alice"}.
        add_to_audience: If true, add the recipient as a contact.
        attachments: List of attachment dicts, each with "filename" (str),
            "contentType" (MIME type str), and "data" (base64-encoded str).
        idempotency_key: Optional key for safe retries (prevents duplicate sends).

    Returns:
        Dict with "success" (bool).
    """

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
    """List transactional email templates with pagination.

    Args:
        per_page: Number of results per page.
        cursor: Pagination cursor from a previous response's "pagination.nextCursor".

    Returns:
        Dict with "pagination" (containing "nextCursor") and "data" (list of templates,
        each with "id", "name", "lastUpdated", and "dataVariables").
    """

    client = _get_client()
    return _execute(
        "list_transactional_emails",
        lambda: client.list_transactional_emails(per_page=per_page, cursor=cursor, as_json=True),
    )


@mcp.tool()
def verify_api_key() -> dict[str, Any]:
    """Verify that the configured Loops API key is valid.

    Returns:
        Dict with "success" (bool) and "teamName" (str).
    """

    client = _get_client()
    return _execute("verify_api_key", lambda: client.verify_api_key(as_json=True))


@mcp.tool()
def list_dedicated_sending_ips() -> list[str]:
    """List dedicated sending IPs for your Loops account.

    Returns:
        List of IP address strings.
    """

    client = _get_client()
    return _execute(
        "list_dedicated_sending_ips",
        lambda: client.list_dedicated_sending_ips(as_json=True),
    )


if __name__ == "__main__":
    mcp.run(transport=_transport)
