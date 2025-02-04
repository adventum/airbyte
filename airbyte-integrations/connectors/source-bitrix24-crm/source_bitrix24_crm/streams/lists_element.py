import functools
from typing import Any, Optional, Mapping, List, Iterable

import requests
from airbyte_cdk import ResourceSchemaLoader, package_name_from_class
from airbyte_protocol.models import SyncMode

from .base import ObjectListStream


class ListsElement(ObjectListStream):
    primary_key = "ID"

    def path(self, **kwargs) -> str:
        return "lists.element.get"

    def block_list_path(self, **kwargs) -> str:
        return "lists.get"

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        return None

    def get_block_ids(self) -> list[str]:
        resp = requests.get(
            self.url_base + self.block_list_path(), params={"IBLOCK_TYPE_ID": "lists"}
        )
        return [block["ID"] for block in resp.json()["result"]]

    def get_records_by_block_id(self, block_id: str) -> Iterable[dict[str, Any]]:
        response_data = requests.get(
            self.url_base + self.path(),
            params={"IBLOCK_TYPE_ID": "lists", "IBLOCK_ID": block_id},
        ).json()
        yield from response_data["result"]

    @functools.lru_cache()
    def get_json_schema(self) -> Mapping[str, Any]:
        # Getting objects logic works too different because of unusual pagination
        schema = ResourceSchemaLoader(
            package_name_from_class(self.__class__)
        ).get_schema(self.name)
        try:
            block_id = self.get_block_ids()[0]
            record = next(self.get_records_by_block_id(block_id))
            sample_data_keys = record.keys()
        except Exception:
            raise Exception(
                f"Schema sample request failed for stream {self.__class__.__name__}"
            )

        for key in sample_data_keys:
            schema["properties"][key] = {"type": ["null", "string"]}

        return schema

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: Optional[List[str]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        stream_state: Optional[Mapping[str, Any]] = None,
    ) -> Iterable[Mapping[str, Any]]:
        print("DATA", sync_mode, cursor_field, stream_slice, stream_state)
        block_ids = self.get_block_ids()
        print(block_ids)
        for block_id in block_ids:
            print("PARSING BLOCK", block_id)
            yield from self.get_records_by_block_id(block_id)
        yield from []
