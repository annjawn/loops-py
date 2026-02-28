from __future__ import annotations

from typing import Any, Dict, List

from ..core import LoopsCore
from ..models import ApiKeyResponse, DedicatedSendingIp


class AccountService:
    def __init__(self, core: LoopsCore) -> None:
        self._core = core

    def verify_api_key(self, *, as_json: bool | None = None) -> ApiKeyResponse | Dict[str, Any]:
        result = self._core.request("GET", "/api-key")
        return self._core.marshal_single(result, ApiKeyResponse, as_json)

    def list_dedicated_sending_ips(
        self,
        *,
        as_json: bool | None = None,
    ) -> List[DedicatedSendingIp] | List[Dict[str, Any]]:
        result = self._core.request("GET", "/dedicated-sending-ips")
        return self._core.marshal_list(result, DedicatedSendingIp, as_json)
