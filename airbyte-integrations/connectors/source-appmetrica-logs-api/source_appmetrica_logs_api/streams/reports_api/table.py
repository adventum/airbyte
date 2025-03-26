#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#
from functools import lru_cache
from typing import Any, Mapping, Optional, MutableMapping, Iterable

import pendulum
import requests
from airbyte_cdk import (
    TokenAuthenticator,
    ResourceSchemaLoader,
    package_name_from_class,
)
from airbyte_cdk import HttpStream


class AppmetricaReportsTable(HttpStream):
    url_base = "https://api.appmetrica.yandex.ru/"
    datetime_format = "YYYY-MM-DD"
    primary_key = None

    def __init__(
        self,
        *,
        authenticator: TokenAuthenticator = None,
        application_id: int,
        date_from: pendulum.DateTime,
        date_to: pendulum.DateTime,
        table_name: str,
        metrics: list[str],
        dimensions: list[str] | None = None,
        filters: str | None = None,
    ):
        # setting source after super().__init__ will break name property
        self.table_name = table_name
        super().__init__(authenticator)
        self._token = authenticator._token
        self.application_id = application_id
        self.date_from = date_from
        self.date_to = date_to
        self.metrics = metrics
        self.dimensions = dimensions if dimensions is not None else []
        self.filters = filters

    @property
    def name(self) -> str:
        return self.table_name

    def path(self, *args, **kwargs) -> str:
        return "stat/v1/data"

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        # Actually supported, but has no real use
        return None

    @lru_cache(maxsize=None)
    def get_json_schema(self) -> Mapping[str, Any]:
        # needed due to overwritten name
        return ResourceSchemaLoader(package_name_from_class(self.__class__)).get_schema(
            "appmetrica_reports_table"
        )

    def request_params(
        self, stream_slice: Mapping[str, any] = None, *args, **kwargs
    ) -> MutableMapping[str, Any]:
        params = {
            "ids": [self.application_id],
            "date1": self.date_from.format(self.datetime_format),
            "date2": self.date_to.format(self.datetime_format),
            "metrics": ",".join(self.metrics),
        }
        if self.dimensions:
            params["dimensions"] = ",".join(self.dimensions)
        if self.filters:
            params["filters"] = self.filters
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
        data = response.json()["data"][0]  # TODO: is it correct???
        for dim, value in zip(self.dimensions, data.get("dimensions", [])):
            yield {"type": "dimension", "name": dim, "value": value}
        for metric, value in zip(self.metrics, data.get("metrics", [])):
            yield {"type": "metric", "name": metric, "value": value}
