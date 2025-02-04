from typing import Any, Optional, Mapping, List, Iterable, MutableMapping

import requests
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

    def stream_slices(
        self,
        *,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_state: Mapping[str, Any] = None,
    ) -> Iterable[Mapping[str, Any]]:
        for block_id in self.get_block_ids():
            yield {"block_id": block_id}

    def request_params(
        self, stream_slice: Mapping[str, any] = None, *args, **kwargs
    ) -> MutableMapping[str, Any]:
        return {"IBLOCK_TYPE_ID": "lists", "IBLOCK_ID": stream_slice["block_id"]}

    def get_block_ids(self) -> list[str]:
        resp = requests.get(
            self.url_base + self.block_list_path(), params={"IBLOCK_TYPE_ID": "lists"}
        )
        return [block["ID"] for block in resp.json()["result"]]
