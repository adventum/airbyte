#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#


import logging
from abc import ABC
from datetime import datetime
from typing import Iterable, Mapping, MutableMapping, NamedTuple

import requests
from airbyte_cdk.sources.streams.core import package_name_from_class
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator
from airbyte_cdk.sources.utils.schema_helpers import ResourceSchemaLoader
from airbyte_cdk.sources.utils.transform import TransformConfig, TypeTransformer

from ..translations import (
    attribution_translations,
    currency_translations,
    date_group_translations,
    preset_name_translations,
)
from ..base_stream import YandexMetrikaStream

from .supported_fields import aggregated_data_streams_fields_manager

logger = logging.getLogger("airbyte")


class ReportConfig(NamedTuple):
    name: str
    counter_id: int | None
    preset_name: str | None
    metrics: list[str] | None
    dimensions: list[str] | None
    filters: str | None
    direct_client_logins: list[str] | None
    goal_id: str | int | None
    date_group: str | None
    attribution: str | None
    currency: str | None
    experiment_ab_id: str | None


# Full refresh stream
class AggregateDataYandexMetrikaReport(YandexMetrikaStream, ABC):
    limit = 1000
    primary_key = None
    transformer: TypeTransformer = TypeTransformer(
        config=TransformConfig.DefaultSchemaNormalization
    )

    def __init__(
        self,
        authenticator: TokenAuthenticator,
        stream_config: dict[str, any],
        counter_id: int,
        date_from: datetime,
        date_to: datetime,
        field_name_map: dict[str, any],
    ):
        super().__init__(field_name_map)
        self.counter_id = counter_id
        self._authenticator = authenticator
        self._name = stream_config["name"]
        self.date_from = date_from
        self.date_to = date_to
        self.attribution = attribution_translations.get(
            stream_config.get("attribution")
        )
        self.date_group = date_group_translations.get(
            stream_config.get("date_group", "день")
        )
        self.currency = currency_translations.get(stream_config.get("currency"))
        self.filters = stream_config.get("filters")
        self.preset_name = preset_name_translations.get(
            stream_config.get("preset_name")
        )
        self.metrics = stream_config.get("metrics")
        self.dimensions = stream_config.get("dimensions")

        # Caching explicitly json schema because read_records uses get_json_schema that makes extra requests
        self.stream_schema_json: dict[str, any] | None = None

    @property
    def name(self) -> str:
        return self._name

    url_base = "https://api-metrika.yandex.net/stat/v1/data"

    def path(self, *args, **kwargs) -> str:
        return ""

    def next_page_token(self, response: requests.Response) -> Mapping[str, any] | None:
        data = response.json()
        if len(data["data"]) < self.limit:
            return None
        return {"next_offset": data["query"]["offset"] + self.limit}

    def get_json_schema(self) -> Mapping[str, any]:
        # Caching schema For better performance on record validation
        # Airbyte may call multiple get_json_schema() with multiple test requests
        if not self.stream_schema_json:
            schema = ResourceSchemaLoader(
                package_name_from_class(self.__class__),
            ).get_schema("yandex_metrika_agg_data_stream")

            test_response = self.make_test_request().json()
            if test_response.get("errors"):
                raise Exception(test_response["message"])
            for dimension in test_response["query"]["dimensions"]:
                schema["properties"][dimension] = {"type": ["null", "string"]}
            for metric in test_response["query"]["metrics"]:
                field_type: str | None = (
                    aggregated_data_streams_fields_manager.field_lookup(metric)
                )
                if not field_type:
                    raise Exception(
                        f"Field '{metric}' is not supported in the connector"
                    )
                schema["properties"][metric] = {"type": [field_type, "null"]}

            super().replace_keys(schema["properties"])
            self.stream_schema_json = schema

        return self.stream_schema_json

    def request_params(
        self, next_page_token: Mapping[str, any] | None = None, *args, **kwargs
    ) -> MutableMapping[str, any]:
        params = {
            "ids": self.counter_id,
            "limit": self.limit,
        }
        if next_page_token:
            params["offset"] = next_page_token.get("next_offset")

        if self.metrics:
            params["metrics"] = ",".join(self.metrics)

        if self.dimensions:
            params["dimensions"] = ",".join(self.dimensions)

        params["accuracy"] = "full"

        params["date1"] = self.date_from.date()
        params["date2"] = self.date_to.date()

        if self.filters:
            params["filters"] = self.filters

        if self.preset_name and self.preset_name != "custom_report":
            params["preset"] = self.preset_name

        params["group"] = self.date_group if self.date_group else "day"

        if self.attribution not in ["default", "lastsign", None]:
            params["attribution"] = self.attribution

        if self.currency not in ["default", None]:
            params["currency"] = self.currency

        # TODO: may be implemented later. Now aren't even supported by schema
        # if self.report_config.get("experiment_ab_id"):
        #     params["experiment_ab"] = self.report_config.get("experiment_ab_id")
        #
        # if self.report_config.get("goal_id"):
        #     params["goal_id"] = self.report_config.get("goal_id")

        return params

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        logger.info(f"Request url with params: {response.request.url}")
        response_data = response.json()
        data = response_data["data"]
        query = response_data["query"]
        keys = query["dimensions"] + query["metrics"]

        for i in range(len(keys)):
            keys[i] = self.field_name_map.get(keys[i], keys[i])

        for row in data:
            row_values = []
            for dimension_value in row["dimensions"]:
                row_values.append(
                    dimension_value.get("id") or dimension_value.get("name")
                )
            row_values += row["metrics"]
            yield dict(zip(keys, row_values))
