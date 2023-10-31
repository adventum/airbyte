#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#


from abc import ABC
from enum import Enum
from typing import Iterable, Mapping, MutableMapping, NamedTuple

import requests
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator
from airbyte_cdk.sources.streams.core import package_name_from_class
from airbyte_cdk.sources.utils.schema_helpers import ResourceSchemaLoader
from airbyte_cdk.sources.utils.transform import TransformConfig, TypeTransformer
from . import supported_fields
from .translations import date_group_translations, attribution_translations, preset_name_translations, currency_translations
import logging
logger = logging.getLogger('airbyte')

class DateRangeType(Enum):
    DATE_RANGE = "date_range"
    LAST_DAYS = "last_days"
    DAY_ENUM = "day_enum"


class DateRangeDay(Enum):
    NONE = "none"
    TODAY = "today"
    YESTERDAY = "yesterday"


class DateRange(NamedTuple):
    date_range_type: DateRangeType
    date_from: str | None
    date_to: str | None
    last_days_count: int | None
    load_today: bool | None
    day: DateRangeDay | None


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
class AggregateDataYandexMetrikaReport(HttpStream, ABC):
    limit = 1000
    primary_key = None
    transformer: TypeTransformer = TypeTransformer(config=TransformConfig.DefaultSchemaNormalization)

    def __init__(self, authenticator: TokenAuthenticator, global_config: dict[str, any], report_config: ReportConfig):
        super().__init__()
        self._authenticator = authenticator
        self.global_config = global_config
        self.report_config = report_config

    @property
    def name(self) -> str:
        return self.report_config["name"]

    url_base = "https://api-metrika.yandex.net/stat/v1/data"

    def path(self, *args, **kwargs) -> str:
        return ""

    def next_page_token(self, response: requests.Response) -> Mapping[str, any] | None:
        data = response.json()
        if len(data["data"]) < self.limit:
            return None
        return {"next_offset": data["query"]["offset"] + self.limit}

    def get_json_schema(self) -> Mapping[str, any]:
        schema = ResourceSchemaLoader(
            package_name_from_class(self.__class__),
        ).get_schema("yandex_metrika_agg_data_stream")
        test_response = self.make_test_request().json()
        if test_response.get("errors"):
            raise Exception(test_response["message"])
        for dimension in test_response["query"]["dimensions"]:
            schema["properties"][dimension] = {"type": ["string", "null"]}
        for metric in test_response["query"]["metrics"]:
            lookup = supported_fields.field_lookup(metric, supported_fields.METRICS_FIELDS)
            if not lookup[0]:
                raise Exception(f"Field '{metric}' is not supported in the connector")
            schema["properties"][metric] = {"type": [lookup[1][1], "null"]}

        return schema

    def make_test_request(self):
        test_params = self.request_params()
        test_params["limit"] = 1
        headers = self._authenticator.get_auth_header()
        return requests.get(self.url_base + self.path(), params=test_params, headers=headers)

    def request_params(self, next_page_token: Mapping[str, any] = {}, *args, **kwargs) -> MutableMapping[str, any]:
        params = {
            "ids": self.global_config["counter_id"],
            "limit": self.limit,
        }
        if next_page_token:
            params["offset"] = next_page_token.get("next_offset")

        if self.report_config.get("metrics"):
            params["metrics"] = ",".join(self.report_config.get("metrics"))

        if self.report_config.get("dimensions"):
            params["dimensions"] = ",".join(self.report_config.get("dimensions"))

        params["accuracy"] = "full"

        params["date1"] = self.global_config.get("date_from")
        params["date2"] = self.global_config.get("date_to")

        if self.report_config.get("direct_client_logins"):
            params["direct_client_logins"] = ",".join(self.report_config.get("direct_client_logins"))

        if self.report_config.get("filters"):
            params["filters"] = self.report_config.get("filters")

        preset_name_input = preset_name_translations.get(self.report_config.get("preset_name"))
        if preset_name_input:
            params["preset"] = preset_name_input

        date_group_input = date_group_translations.get(self.report_config.get("date_group", "день"))
        if date_group_input not in ["day", None]:
            params["group"] = date_group_input
        else:
            params["group"] = "day"

        attribution_input = attribution_translations.get(self.report_config.get("attribution"))
        if attribution_input not in ["default", "lastsign", None]:
            params["attribution"] = attribution_input

        currency_input = currency_translations.get(self.report_config.get("currency"))
        if currency_input not in ["default", None]:
            params["currency"] = currency_input

        if self.report_config.get("experiment_ab_id"):
            params["experiment_ab"] = self.report_config.get("experiment_ab_id")

        if self.report_config.get("goal_id"):
            params["goal_id"] = self.report_config.get("goal_id")

        return params

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        logger.info(f"Request url with params: {response.request.url}")
        response_data = response.json()
        sampling_info = {
            "sampled": response_data["sampled"],
            "sample_share": response_data["sample_share"],
            "sample_size": response_data["sample_size"],
            "sample_space": response_data["sample_space"],
            "data_lag": response_data["data_lag"],
            "total_rows": response_data["total_rows"],
            "total_rows_rounded": response_data["total_rows_rounded"],
            "totals": response_data["totals"],
            "min": response_data["min"],
            "max": response_data["max"],
        }
        logger.info(f"Response sampling info: {sampling_info}")
        data = response_data["data"]
        query = response_data["query"]
        keys = query["dimensions"] + query["metrics"]

        for row in data:
            row_values = []
            for dimension_value in row["dimensions"]:
                row_values.append(dimension_value.get("id") or dimension_value.get("name"))
            row_values += row["metrics"]
            yield dict(zip(keys, row_values))
