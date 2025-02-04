import functools
from typing import Any, Iterable, Mapping, MutableMapping

import requests
from airbyte_cdk import ResourceSchemaLoader, package_name_from_class

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

    @functools.lru_cache()
    def get_json_schema(self) -> Mapping[str, Any]:
        # Has a bit different data format with result/items
        # TODO: duplicate, but no idea, how to make it simple and clean
        schema = ResourceSchemaLoader(
            package_name_from_class(self.__class__)
        ).get_schema(self.name)
        try:
            response_data = requests.get(
                self.url_base + self.path(), params=self.request_params(None)
            ).json()
            sample_data_keys = response_data["result"]["items"][0].keys()
        except Exception:
            raise Exception(
                f"Schema sample request failed for stream {self.__class__.__name__}"
            )

        for key in sample_data_keys:
            schema["properties"][key] = {"type": ["null", "string"]}

        return schema

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        # Again, different format with its result/items
        yield from response.json()["result"]["items"]
