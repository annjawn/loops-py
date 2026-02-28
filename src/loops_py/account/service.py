from __future__ import annotations

from typing import Any, List

from ..core import LoopsCore
from ..exceptions import LoopsError
from ..models import ApiKeyResponse


class AccountService:
    def __init__(self, core: LoopsCore) -> None:
        self._core = core

    def verify_api_key(self, *, as_json: bool | None = None) -> ApiKeyResponse | dict[str, Any]:
        result = self._core.request("GET", "/api-key")
        return self._core.marshal_single(result, ApiKeyResponse, as_json)

    def list_dedicated_sending_ips(
        self,
        *,
        as_json: bool | None = None,
    ) -> List[str]:
        result = self._core.request("GET", "/dedicated-sending-ips")
        if self._core.is_json_mode(as_json):
            if not isinstance(result, list):
                raise LoopsError("Expected list response for dedicated sending IPs")
            return [str(item) for item in result]
        if not isinstance(result, list):
            raise LoopsError("Expected list response for dedicated sending IPs")
        return [str(item) for item in result]
