import functools
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import requests
from airbyte_cdk import ResourceSchemaLoader, package_name_from_class
from airbyte_protocol.models import SyncMode

from .base import Bitrix24CrmStream


class StageHistory(Bitrix24CrmStream):
    primary_key = "ID"
    entity_id_map = {"лид": 1, "сделка": 2, "отчет": 5}

    def path(self, **kwargs) -> str:
        return "crm.stagehistory.list"

    @functools.lru_cache()
    def get_json_schema(self) -> Mapping[str, Any]:
        # Parsing from stream spec file
        return ResourceSchemaLoader(package_name_from_class(self.__class__)).get_schema(
            self.name
        )

    def stream_slices(
        self,
        sync_mode: SyncMode,
        cursor_field: list[str] = None,
        stream_state: Mapping[str, Any] = None,
    ) -> Iterable[Optional[Mapping[str, Any]]]:
        for val in self.entity_id_map.values():
            yield {"entity_id": val}

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        # Has another time variable name
        params = super().request_params(stream_state, stream_slice, next_page_token)

        # "лид" by default
        extended_params = {
            "entityTypeId": stream_slice["entity_id"],
            "filter[>=CREATED_TIME]": self.config["date_from"],
            "filter[<=CREATED_TIME]": self.config["date_to"],
        }
        params.update(extended_params)
        return params

    def parse_response(
        self,
        response: requests.Response,
        stream_slice: Mapping[str, any] = None,
        **kwargs,
    ) -> Iterable[Mapping]:
        # Again, different format with its result/items
        id_entity_map: dict[int, str] = {
            value: key for key, value in self.entity_id_map.items()
        }
        for item in response.json()["result"]["items"]:
            item["ENTITY_TYPE_ID"] = stream_slice["entity_id"]
            item["ENTITY_TYPE_NAME"] = id_entity_map[stream_slice["entity_id"]]
            yield item
