#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#


import logging
import os
import typing
from abc import ABC
from datetime import datetime
from typing import Iterable, Mapping, MutableMapping, Optional, Tuple

import requests
from airbyte_cdk.sources.streams.core import package_name_from_class
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator
from airbyte_cdk.sources.utils.schema_helpers import ResourceSchemaLoader

from .stream_preprocessor import YandexMetrikaStreamPreprocessor
from ..base_stream import YandexMetrikaStream
from ..translations import attribution_translations
from ..utils import (
    daterange_days_list,
    random_output_filename,
)
from ..exceptions import ConfigInvalidError
from ..raw_data_streams.supported_fields import hits_fields_manager, visits_fields_manager, YandexMetrikaFieldsManager

if typing.TYPE_CHECKING:
    from airbyte_cdk.sources import Source

logger = logging.getLogger("airbyte")


class YandexMetrikaRawDataStream(YandexMetrikaStream, ABC):
    url_base = "https://api-metrika.yandex.net/management/v1/"

    def __init__(
            self,
            stream_config: dict[str, any],
            authenticator: TokenAuthenticator,
            counter_id: int,
            date_from: datetime,
            date_to: datetime,
            log_source: str,
            field_name_map: dict[str, str],
            created_for_test: bool = False,
    ):
        """Load basic attributes"""
        super().__init__(field_name_map)

        self.counter_id = counter_id
        self._authenticator = authenticator
        self.date_from = date_from
        self.date_to = date_to
        self.log_source = log_source
        self.preprocessor = YandexMetrikaStreamPreprocessor(stream_instance=self)
        self.created_for_test = created_for_test

        self._name = stream_config.get("name")
        self.split_range_days_count = stream_config.get("split_range_days_count", False)
        self.multithreading_threads_count = stream_config.get("multithreading_threads_count", 1)
        self.clean_slice_after_successfully_loaded = stream_config.get("clean_slice_after_successfully_loaded", False)
        self.clean_log_requests_before_replication = stream_config.get("clean_log_requests_before_replication", False)
        self.check_log_requests_ability = stream_config.get("check_log_requests_ability", False)

        """Load and check fields"""
        self.fields = stream_config.get("fields", [])
        attribution: str | None = stream_config.get("attribution")
        if not attribution and any(("<attribution>" in field for field in self.fields)):
            raise ConfigInvalidError("В полях отчета используется <attribution>, при этом аттрибуция не задана")

        if attribution:
            attribution = attribution_translations.get(attribution)
            if not attribution:
                raise ConfigInvalidError(f"Неизвестная аттрибуция {attribution}")

        for i, field in enumerate(self.fields):
            if "<attribution>" in field:
                self.fields[i] = field.replace("<attribution>", attribution)

        field_manager: YandexMetrikaFieldsManager = visits_fields_manager if log_source == "visits" else hits_fields_manager
        for f in self.fields:
            if f not in field_manager.get_all_fields_values():
                raise ConfigInvalidError(
                    f'Сырые отчёты - источник {log_source} не может содержать поле "{f}". См. доступные поля: "https://yandex.ru/dev/metrika/doc/api2/logs/fields/visits.html"')

        for f in visits_fields_manager.get_required_fields_names():
            if f not in self.fields:
                raise ConfigInvalidError(
                    f'Сырые отчёты - источник {log_source} должен содержать поля {" ".join(field_manager.get_required_fields_names())}')

        if self.primary_key in self.field_name_map.keys():
            raise ConfigInvalidError(f"Поле {self.primary_key} не может быть переименовано")

        # Get rid of duplicates
        self.fields = list(set(self.fields))

        """Clean and check if needed"""
        if self.clean_log_requests_before_replication and not self.created_for_test:
            logger.info("Clean all log requests before replication...")
            self.preprocessor.clean_all_log_requests()

        if self.check_log_requests_ability and not self.created_for_test:
            can_replicate, message = self.preprocessor.check_stream_slices_ability()
            if not can_replicate:
                raise Exception(message)

    @property
    def primary_key(self) -> str | list[str] | list[list[str]]:
        if self.log_source == "visits":
            return "ym:s:visitID"
        if self.log_source == "hits":
            return "ym:pv:watchID"

    @property
    def name(self) -> str:
        return f"raw_data_{self.log_source}{('_' + self._name) if self.name else ''}"

    def get_json_schema(self) -> Mapping[str, any]:
        schema = ResourceSchemaLoader(package_name_from_class(self.__class__)).get_schema(
            "yandex_metrika_raw_data_stream"
        )
        for key in self.fields:
            schema["properties"][key] = {"type": ["null", "string"]}

        super().replace_keys(schema["properties"])

        return schema

    def path(
            self,
            next_page_token: Mapping[str, any] = None,
            stream_slice: Mapping[str, any] = None,
            *args,
            **kwargs,
    ) -> str:
        path = f"counter/{self.counter_id}/logrequest/{stream_slice['log_request_id']}/part/{stream_slice['part']['part_number']}/download"
        logger.info(f"Path: {path}")
        return path

    def check_availability(self, logger: logging.Logger, source: Optional["Source"] = None) -> Tuple[bool, Optional[str]]:
        # Custom stream used custom read that fails to check it
        return True, None

    def next_page_token(self, *args, **kwargs) -> Mapping[str, any] | None:
        return None

    def request_params(
            self, stream_slice: Mapping[str, any] = None, *args, **kwargs
    ) -> MutableMapping[str, any]:
        return {
            "date1": datetime.strftime(stream_slice["date_from"], "%Y-%m-%d"),
            "date2": datetime.strftime(stream_slice["date_to"], "%Y-%m-%d"),
            "fields": ",".join(self.fields),
            "source": self.log_source,
        }

    def request_headers(self, stream_state=None, *args, **kwargs) -> Mapping[str, any]:
        headers = super().request_headers(stream_state, *args, **kwargs)
        headers.update({"Content-Type": "application/x-yametrika+json"})
        return headers

    def should_retry(self, response: requests.Response) -> bool:
        return response.status_code in [429, 400] or 500 <= response.status_code < 600

    def parse_response(
            self,
            response: requests.Response,
            stream_slice: Mapping[str, str],
            *args,
            **kwargs,
    ) -> Iterable:
        logger.info(f"parse_response {response.url}")
        try:
            os.mkdir("output")
        except FileExistsError:
            pass
        filename = random_output_filename()
        logger.info(f"Save slice {stream_slice} data to {filename}")
        with open(filename, "wb") as f:
            f.write(response.content)
        logger.info(f"end of parse_response")
        return [filename]

    def stream_slices(self, *args, **kwargs) -> Iterable[Mapping[str, any] | None]:
        if not self.split_range_days_count:
            slices = [{"date_from": self.date_from, "date_to": self.date_to}]
        elif self.split_range_days_count:
            slices = daterange_days_list(self.date_from, self.date_to, self.split_range_days_count)
        else:
            slices = None
        return slices
