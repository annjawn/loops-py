from __future__ import annotations

from typing import Any, Dict, List

from ..core import LoopsCore
from ..models import MailingList


class MailingListsService:
    def __init__(self, core: LoopsCore) -> None:
        self._core = core

    def list_mailing_lists(
        self,
        *,
        as_json: bool | None = None,
    ) -> List[MailingList] | List[Dict[str, Any]]:
        result = self._core.request("GET", "/mailing-lists")
        return self._core.marshal_list(result, MailingList, as_json)
