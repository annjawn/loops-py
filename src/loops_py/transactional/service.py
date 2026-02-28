from __future__ import annotations

from typing import Any, Dict, Mapping, Union

from ..core import LoopsCore
from ..models import SendTransactionalEmailRequest, SuccessResponse, TransactionalEmailListResponse


class TransactionalService:
    def __init__(self, core: LoopsCore) -> None:
        self._core = core

    def send_transactional_email(
        self,
        request: Union[SendTransactionalEmailRequest, Mapping[str, Any]],
        *,
        idempotency_key: str | None = None,
        as_json: bool | None = None,
    ) -> SuccessResponse | Dict[str, Any]:
        payload = self._core.validate_request(request, SendTransactionalEmailRequest)
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        result = self._core.request("POST", "/transactional", payload=payload, headers=headers)
        return self._core.marshal_single(result, SuccessResponse, as_json)

    def list_transactional_emails(
        self,
        *,
        per_page: int | None = None,
        cursor: str | None = None,
        as_json: bool | None = None,
    ) -> TransactionalEmailListResponse | Dict[str, Any]:
        query: Dict[str, Any] = {}
        if per_page is not None:
            query["perPage"] = per_page
        if cursor:
            query["cursor"] = cursor

        result = self._core.request("GET", "/transactional", query=query or None)
        return self._core.marshal_single(result, TransactionalEmailListResponse, as_json)
