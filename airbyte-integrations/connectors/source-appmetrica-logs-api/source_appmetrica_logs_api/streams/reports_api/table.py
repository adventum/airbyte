#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#
from functools import lru_cache
from typing import Any, Mapping, Optional, MutableMapping, Iterable, Literal

import pendulum
import requests
from airbyte_cdk import (
    TokenAuthenticator,
    ResourceSchemaLoader,
    package_name_from_class,
)
from airbyte_cdk import HttpStream
from airbyte_protocol.models import SyncMode


class AppmetricaReportsTable(HttpStream):
    datetime_format = "YYYY-MM-DD"
    primary_key = None

    def __init__(
        self,
        *,
        api_version: Literal["v1", "v2"],
        authenticator: TokenAuthenticator = None,
        application_id: int,
        date_from: pendulum.DateTime,
        date_to: pendulum.DateTime,
        table_name: str,
        metrics: list[str],
        dimensions: list[str] | None = None,
        filters: str | None = None,
        event_names: list[str] | None = None,
    ):
        # setting source after super().__init__ will break name property
        self.api_version = api_version
        self.table_name = table_name
        super().__init__(authenticator)
        self._token = authenticator._token
        self.application_id = application_id
        self.date_from = date_from
        self.date_to = date_to
        self.metrics = metrics
        self.dimensions = dimensions if dimensions is not None else []
        self.filters = filters
        self.event_names = event_names if event_names is not None else []

    @property
    def url_base(self) -> str:
        if self.api_version == "v1":
            return "https://api.appmetrica.yandex.ru/"
        else:
            return "https://api.appmetrica.yandex.ru/v2/"

    @property
    def name(self) -> str:
        return self.table_name

    def path(self, *args, **kwargs) -> str:
        if self.api_version == "v1":
            return "stat/v1/data"
        else:
            return "user/acquisition"

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        # Actually supported, but has no real use
        return None

    @lru_cache(maxsize=None)
    def get_json_schema(self) -> Mapping[str, Any]:
        # needed due to overwritten name
        schema = ResourceSchemaLoader(
            package_name_from_class(self.__class__)
        ).get_schema("appmetrica_reports_table")

        try:
            stream_slices = self.stream_slices(sync_mode=SyncMode.full_refresh)
            record_iterator = self.read_records(
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

    def request_params(
        self, stream_slice: Mapping[str, any] = None, *args, **kwargs
    ) -> MutableMapping[str, Any]:
        params = {
            "date1": self.date_from.format(self.datetime_format),
            "date2": self.date_to.format(self.datetime_format),
            "metrics": ",".join(self.metrics),
        }
        if self.filters:
            params["filters"] = self.filters

        if self.api_version == "v1":
            params["ids"] = [self.application_id]
            if self.dimensions:
                params["dimensions"] = ",".join(self.dimensions)
        else:
            params["id"] = self.application_id
            params["accuracy"] = 1
            params["proposedAccuracy"] = True
            params["source"] = "installation"
            params["dimensions"] = self.dimensions or ["date"]
            params["lang"] = "ru"
            params["request_domain"] = "ru"
            if self.event_names:
                params["eventNames"] = (
                    "[[" + ",".join([f'"{name}"' for name in self.event_names]) + "]]"
                )
        return params

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        """
        Response format:
        "data" : [ {
            "dimensions" : [ ],
            "metrics" : [ 249472.0, 990223.0 ]
          } ],
        """
        yield from response.json()["data"]
