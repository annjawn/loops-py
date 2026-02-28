from __future__ import annotations

from typing import Any, Dict, List, Mapping, Union

from .account import AccountService
from .contacts import ContactsService
from .core import HttpRequest, HttpResponse, LoopsCore, ResponseMode, Transport
from .events import EventsService
from .mailing_lists import MailingListsService
from .models import (
    ApiKeyResponse,
    Contact,
    ContactProperty,
    ContactRequest,
    ContactUpsertResponse,
    CreateContactPropertyRequest,
    DeleteContactRequest,
    FindContactQuery,
    MailingList,
    SendEventRequest,
    SendTransactionalEmailRequest,
    SuccessResponse,
    TransactionalEmailListResponse,
    UpdateContactRequest,
)
from .transactional import TransactionalService


class LoopsClient:
    """Synchronous, lightweight client for Loops API v1."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://app.loops.so/api/v1",
        timeout: float = 30.0,
        response_mode: ResponseMode = "model",
        max_retries: int = 3,
        retry_backoff_base: float = 0.25,
        retry_backoff_max: float = 4.0,
        retry_jitter: float = 0.1,
        user_agent: str = "pyloops-so/0.1",
        transport: Transport | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("api_key must not be empty")
        if response_mode not in ("model", "json"):
            raise ValueError("response_mode must be either 'model' or 'json'")
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if retry_backoff_base <= 0:
            raise ValueError("retry_backoff_base must be > 0")
        if retry_backoff_max <= 0:
            raise ValueError("retry_backoff_max must be > 0")
        if retry_backoff_max < retry_backoff_base:
            raise ValueError("retry_backoff_max must be >= retry_backoff_base")
        if retry_jitter < 0:
            raise ValueError("retry_jitter must be >= 0")
        if not user_agent.strip():
            raise ValueError("user_agent must not be empty")

        core = LoopsCore(
            api_key,
            base_url=base_url,
            timeout=timeout,
            response_mode=response_mode,
            transport=transport,
            max_retries=max_retries,
            retry_backoff_base=retry_backoff_base,
            retry_backoff_max=retry_backoff_max,
            retry_jitter=retry_jitter,
            user_agent=user_agent,
        )

        self.contacts = ContactsService(core)
        self.mailing_lists = MailingListsService(core)
        self.events = EventsService(core)
        self.transactional = TransactionalService(core)
        self.account = AccountService(core)

    def create_contact(
        self,
        request: Union[ContactRequest, Mapping[str, Any]],
        *,
        as_json: bool | None = None,
    ) -> Union[ContactUpsertResponse, Dict[str, Any]]:
        return self.contacts.create_contact(request, as_json=as_json)

    def update_contact(
        self,
        request: Union[UpdateContactRequest, Mapping[str, Any]],
        *,
        as_json: bool | None = None,
    ) -> Union[ContactUpsertResponse, Dict[str, Any]]:
        return self.contacts.update_contact(request, as_json=as_json)

    def find_contact(
        self,
        query: Union[FindContactQuery, Mapping[str, Any]],
        *,
        as_json: bool | None = None,
    ) -> Union[List[Contact], List[Dict[str, Any]]]:
        return self.contacts.find_contact(query, as_json=as_json)

    def delete_contact(
        self,
        request: Union[DeleteContactRequest, Mapping[str, Any]],
        *,
        as_json: bool | None = None,
    ) -> Union[SuccessResponse, Dict[str, Any]]:
        return self.contacts.delete_contact(request, as_json=as_json)

    def create_contact_property(
        self,
        request: Union[CreateContactPropertyRequest, Mapping[str, Any]],
        *,
        as_json: bool | None = None,
    ) -> Union[SuccessResponse, Dict[str, Any]]:
        return self.contacts.create_contact_property(request, as_json=as_json)

    def list_contact_properties(
        self,
        *,
        list_type: str | None = None,
        as_json: bool | None = None,
    ) -> Union[List[ContactProperty], List[Dict[str, Any]]]:
        return self.contacts.list_contact_properties(list_type=list_type, as_json=as_json)

    def list_mailing_lists(
        self,
        *,
        as_json: bool | None = None,
    ) -> Union[List[MailingList], List[Dict[str, Any]]]:
        return self.mailing_lists.list_mailing_lists(as_json=as_json)

    def send_event(
        self,
        request: Union[SendEventRequest, Mapping[str, Any]],
        *,
        idempotency_key: str | None = None,
        as_json: bool | None = None,
    ) -> Union[SuccessResponse, Dict[str, Any]]:
        return self.events.send_event(
            request,
            idempotency_key=idempotency_key,
            as_json=as_json,
        )

    def send_transactional_email(
        self,
        request: Union[SendTransactionalEmailRequest, Mapping[str, Any]],
        *,
        idempotency_key: str | None = None,
        as_json: bool | None = None,
    ) -> Union[SuccessResponse, Dict[str, Any]]:
        return self.transactional.send_transactional_email(
            request,
            idempotency_key=idempotency_key,
            as_json=as_json,
        )

    def list_transactional_emails(
        self,
        *,
        per_page: int | None = None,
        cursor: str | None = None,
        as_json: bool | None = None,
    ) -> Union[TransactionalEmailListResponse, Dict[str, Any]]:
        return self.transactional.list_transactional_emails(
            per_page=per_page,
            cursor=cursor,
            as_json=as_json,
        )

    def verify_api_key(
        self,
        *,
        as_json: bool | None = None,
    ) -> Union[ApiKeyResponse, Dict[str, Any]]:
        return self.account.verify_api_key(as_json=as_json)

    def list_dedicated_sending_ips(
        self,
        *,
        as_json: bool | None = None,
    ) -> List[str]:
        return self.account.list_dedicated_sending_ips(as_json=as_json)


__all__ = [
    "HttpRequest",
    "HttpResponse",
    "LoopsClient",
    "ResponseMode",
    "Transport",
]
