import functools
from typing import Mapping, Any, MutableMapping

import requests
from .base import Bitrix24CrmStream


class Deals(Bitrix24CrmStream):
    def path(self, **kwargs) -> str:
        return "crm.deal.list"

    @functools.cached_property
    def fields(self) -> list[str]:
        """List of fields to request in response params select[]"""
        request = requests.get(self.url_base + "crm.deal.fields")
        return list(request.json()["result"].keys())

    @functools.lru_cache()
    def get_json_schema(self) -> Mapping[str, Any]:
        schema = super().get_json_schema()
        for key in self.fields:
            schema["properties"][key] = {"type": ["null", "string"]}

        return schema

    def request_params(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> MutableMapping[str, Any]:
        params = super().request_params(next_page_token=next_page_token, **kwargs)
        extended_params = {"select[]": self.fields}
        params.update(extended_params)
        return params
