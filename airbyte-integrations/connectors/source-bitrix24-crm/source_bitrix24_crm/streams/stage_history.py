from typing import Any, Iterable, Mapping, MutableMapping

import requests

from .base import ObjectListStream


class StageHistory(ObjectListStream):
    primary_key = "ID"
    entity_id_map = {"лид": 1, "сделка": 2, "отчет": 5}

    def path(self, **kwargs) -> str:
        return "crm.stagehistory.list"

    def request_params(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> MutableMapping[str, Any]:
        # Has another time variable name
        params = super().request_params(next_page_token=next_page_token, **kwargs)

        # "лид" by default
        extended_params = {
            "entityTypeId": self.entity_id_map.get(
                self.config.get("entity_type_id"),
                1,
            ),
            "filter[>=CREATED_TIME]": self.config["date_from"],
            "filter[<=CREATED_TIME]": self.config["date_to"],
        }
        params.update(extended_params)
        return params

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        # Again, different format with its result/items
        yield from response.json()["result"]["items"]
