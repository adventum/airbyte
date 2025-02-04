import functools
from typing import Mapping, Any, MutableMapping

import requests

from .base import ObjectListStream


class Leads(ObjectListStream):
    @functools.cached_property
    def fields(self) -> list[str]:
        """List of fields to request in response params select[]"""
        request = requests.get(self.url_base + "crm.lead.fields")
        return list(request.json()["result"].keys())

    def path(self, **kwargs) -> str:
        return "crm.lead.list"

    def request_params(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> MutableMapping[str, Any]:
        params = super().request_params(next_page_token=next_page_token, **kwargs)
        extended_params = {"select[]": self.fields}
        params.update(extended_params)
        return params
