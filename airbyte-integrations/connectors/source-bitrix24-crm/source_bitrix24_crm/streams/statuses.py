from typing import MutableMapping, Any, Mapping

from .base import Bitrix24CrmStream


class Statuses(Bitrix24CrmStream):
    primary_key = "STATUS_ID"

    def path(self, **kwargs) -> str:
        return "crm.status.list"

    def request_params(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> MutableMapping[str, Any]:
        return {}
