#
# Copyright (c) 2024 Airbyte, Inc., all rights reserved.
#
import functools
from abc import ABC
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import requests
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_protocol.models import SyncMode


# Basic full refresh stream
class Bitrix24CrmStream(HttpStream, ABC):
    """Base stream for bitrix24"""

    primary_key = "ID"

    def __init__(self, config: Mapping[str, Any]):
        super().__init__(authenticator=None)
        self.config = config

    @property
    def url_base(self) -> str:
        return self.config["webhook_endpoint"]

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        yield from response.json()["result"]

    @functools.lru_cache()
    def get_json_schema(self) -> Mapping[str, Any]:
        schema = super().get_json_schema()
        # Create stream copy (avoid accidentally ruining generators of this stream)
        try:
            test_stream = self.__class__(self.config)
            stream_slices = test_stream.stream_slices(sync_mode=SyncMode.full_refresh)
            record_iterator = test_stream.read_records(
                sync_mode=SyncMode.full_refresh, stream_slice=next(stream_slices)
            )
            record = next(record_iterator)
            sample_data_keys = record.keys()
        except Exception as e:
            raise Exception(
                f"Schema sample request failed for stream {self.__class__.__name__}. Reason: {e}"
            )

        for key in sample_data_keys:
            schema["properties"][key] = {"type": ["null", "string"]}

        return schema

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        last_response_data = response.json()
        if last_response_data.get("next"):
            return {"next": last_response_data.get("next")}
        return None

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        params = {"select[]": ["*", "UF_*"]}
        if next_page_token:
            params["start"] = next_page_token["next"]
        extended_params = {
            "filter[>=DATE_CREATE]": self.config["date_from"],
            "filter[<=DATE_CREATE]": self.config["date_to"],
        }
        params.update(extended_params)
        return params
