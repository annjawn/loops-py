from __future__ import annotations

from typing import Any, Dict, Mapping, Union

from ..core import LoopsCore
from ..models import SendEventRequest, SuccessResponse


class EventsService:
    def __init__(self, core: LoopsCore) -> None:
        self._core = core

    def send_event(
        self,
        request: Union[SendEventRequest, Mapping[str, Any]],
        *,
        idempotency_key: str | None = None,
        as_json: bool | None = None,
    ) -> SuccessResponse | Dict[str, Any]:
        payload = self._core.validate_request(request, SendEventRequest)
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        result = self._core.request("POST", "/events/send", payload=payload, headers=headers)
        return self._core.marshal_single(result, SuccessResponse, as_json)
