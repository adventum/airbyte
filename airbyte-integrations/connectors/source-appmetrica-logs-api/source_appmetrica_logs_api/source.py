#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import csv
import json
import logging
import os
import time
from abc import ABC
from datetime import datetime, timedelta
from time import sleep
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple
from urllib import request

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.core import package_name_from_class
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator
from airbyte_cdk.sources.utils.schema_helpers import ResourceSchemaLoader
from airbyte_cdk.sources.utils.transform import TransformConfig, TypeTransformer
from source_appmetrica_logs_api.auth import CredentialsCraftAuthenticator
from .fields import AVAILABLE_FIELDS
import sys

logger = logging.getLogger("airbyte")

csv.field_size_limit(sys.maxsize)

DATE_FORMAT = "%Y-%m-%d"

# Basic full refresh stream
class AppmetricaLogsApiStream(HttpStream, ABC):

    url_base = "https://api.appmetrica.yandex.ru/"
    primary_key = []
    transformer: TypeTransformer = TypeTransformer(config=TransformConfig.DefaultSchemaNormalization)
    should_redownload = False

    def __init__(
        self,
        *,
        authenticator: TokenAuthenticator = None,
        application_id: int,
        date_from: datetime,
        date_to: datetime,
        chunked_logs_params: Mapping[str, Any],
        fields: List[str] = [],
        source: str,
        filters: List[Mapping[str, str]] = [],
        date_dimension: str = "default",
        event_name_list: List[str] = [None],
        client_name: str = "",
        product_name: str = "",
        custom_json: Optional[Mapping[str, str]] = {},
        iter_content_chunk_size: int = 8192
    ):
        super().__init__(authenticator)
        self.application_id = application_id
        self.date_from = date_from
        self.date_to = date_to
        self.event_name_list = event_name_list
        self.chunked_logs_params = chunked_logs_params

        if not fields:
            fields = AVAILABLE_FIELDS[source]["fields"].keys()

        logger.info(f"event_name_list: {self.event_name_list}")

        self.fields = fields
        self.source = source
        self.filters = filters
        self.date_dimension = date_dimension
        self.client_name = client_name
        self.product_name = product_name
        self.custom_json = custom_json
        self._is_report_ready_to_load: bool = False
        self.iter_content_chunk_size = iter_content_chunk_size

    def path(self, *args, **kwargs) -> str:
        return f"logs/v1/export/{self.source}.csv"

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    @property
    def name(self) -> str:
        return self.source

    @staticmethod
    def filters_into_request_params(filters: List[Mapping[str, str]]) -> Mapping[str, Any]:
        params = {}
        for filter in filters:
            if filter["name"] not in params.keys():
                params[filter["name"]] = []
            params[filter["name"]].append(filter["value"])
        return params

    def request_params(self, stream_slice: Mapping[str, any] = None, *args, **kwargs) -> MutableMapping[str, Any]:
        print("stream_slice", stream_slice)
        params = {
            "application_id": self.application_id,
            "date_since": datetime.strftime(stream_slice["date_from"], "%Y-%m-%d %H:%M:%S"),
            "date_until": datetime.strftime(stream_slice["date_to"], "%Y-%m-%d %H:%M:%S"),
            "fields": ",".join(self.fields),
            "date_dimension": self.date_dimension,
        }
        if stream_slice.get("event_name"):
            params["event_name"] = stream_slice.get("event_name")
        if self.filters:
            params.update(self.filters_into_request_params(self.filters))
        print(params)
        return params

    def get_json_schema(self) -> Mapping[str, Any]:
        schema = ResourceSchemaLoader(package_name_from_class(self.__class__)).get_schema("appmetrika_report")
        for field_name in self.fields:
            lookup_field_type = AVAILABLE_FIELDS[self.source]["fields"].get(field_name, "string")
            schema["properties"][field_name] = {"type": ["null", lookup_field_type]}
        extra_properties = ["__productName", "__clientName"]
        extra_properties.extend(self.custom_json.keys())
        for key in extra_properties:
            schema["properties"][key] = {"type": ["null", "string"]}
        return schema

    def add_constants_to_record(self, record):
        constants = {
            "__productName": self.product_name,
            "__clientName": self.client_name,
        }
        constants.update(self.custom_json)
        record.update(constants)
        return record

    def parse_response(self, response: requests.Response, stream_slice: Mapping[str, Any], **kwargs) -> Iterable[Mapping]:
        stream_slice_formatted = f'{stream_slice["date_from"].date()}-{stream_slice["date_to"].date()}'
        if response.status_code == 202:
            logger.info(f"Response Code 202: awaiting for report for slice {stream_slice_formatted} will be ready.")
            time.sleep(10)
            yield from []
        elif response.status_code == 200:
            records_counter = 0
            self._is_report_ready_to_load = True

            try:
                logger.info(f"Response Code 200: start loading report for slice {stream_slice_formatted}")
                logger.info(f"Expected rows for slice {stream_slice_formatted}: {response.headers.get('Rows-Number', 'not calculated')}")

                try:
                    os.mkdir("output")
                except:
                    pass

                while_download_filename = f"output/{self.application_id}_{self.source}_{stream_slice_formatted}_dl.csv"
                succesfully_downloaded_filename = f"output/{self.application_id}_{self.source}_{stream_slice_formatted}_full.csv"
                if not os.path.exists(succesfully_downloaded_filename) or self.should_redownload:
                    with open(while_download_filename, "wb") as f:
                        logger.info(f"Downloading {while_download_filename}...")
                        for chunk in response.iter_content(chunk_size=self.iter_content_chunk_size):
                            f.write(chunk)

                logger.info(
                    f"Succesfully downloaded {while_download_filename}. "
                    f"Rename to {succesfully_downloaded_filename} and start reading into slices."
                )
                os.rename(while_download_filename, succesfully_downloaded_filename)

                with open(succesfully_downloaded_filename, errors='replace') as f:
                    logger.info(f"Start reading from {succesfully_downloaded_filename}")
                    reader = csv.DictReader(f)
                    for record in reader:
                        records_counter += 1
                        yield self.add_constants_to_record(record)
                    logger.info(f"Total records count loaded for slice {stream_slice_formatted}: {records_counter}")
                logger.info(f"Remove {succesfully_downloaded_filename}")
            except Exception as e:
                raise e
            finally:
                try:
                    os.remove(
                        succesfully_downloaded_filename,
                    )
                except FileNotFoundError:
                    pass
        else:
            pass

    def request_kwargs(self, *args, **kwargs) -> Mapping[str, Any]:
        rkwargs = super().request_kwargs(*args, **kwargs)
        rkwargs.update({"stream": True})
        return rkwargs

    @staticmethod
    def chunk_dates(date_from: datetime, date_to: datetime, chunk_days_count: int) -> Iterable[Mapping[str, str]]:
        cursor = date_from
        while cursor <= date_to:
            chunk_date_from = cursor
            chunk_date_to = (cursor + timedelta(days=chunk_days_count - 1)).replace(hour=23, minute=59, second=59)
            if chunk_date_to > date_to:
                chunk_date_to = date_to.replace(hour=23, minute=59, second=59)
            yield {"date_from": chunk_date_from, "date_to": chunk_date_to}
            cursor += timedelta(days=chunk_days_count)

    def stream_slices(self, *args, **kwargs) -> Iterable[Optional[Mapping[str, Any]]]:
        logger.info(f"Using date_from {self.date_from.date()} and date_to {self.date_to.date()}")

        if self.event_name_list:
            if self.chunked_logs_params["split_mode_type"] == "do_not_split_mode":
                for event_name in self.event_name_list:
                    self._is_report_ready_to_load = False
                    print("event_name", event_name)
                    while not self._is_report_ready_to_load:
                        yield {
                            "date_from": self.date_from,
                            "date_to": self.date_to.replace(hour=23, minute=59, second=59),
                            "event_name": event_name,
                        }
            else:
                for slice in self.chunk_dates(self.date_from, self.date_to, self.chunked_logs_params["split_range_days_count"]):
                    for event_name in self.event_name_list:
                        self._is_report_ready_to_load = False
                        slice.update({"event_name": event_name})
                        logger.info(f"Current slice: {slice}")
                        while True:
                            yield slice
                            if self._is_report_ready_to_load:
                                break
                            else:
                                logger.info(f"Sleep for 10 sec...")
                                sleep(10)
        else:
            if self.chunked_logs_params["split_mode_type"] == "do_not_split_mode":
                logger.info("Using do_not_split_mode")
                self._is_report_ready_to_load = False
                while not self._is_report_ready_to_load:
                    yield {
                        "date_from": self.date_from,
                        "date_to": self.date_to.replace(hour=23, minute=59, second=59),
                    }
            else:
                logger.info("Using split_into_chunks mode")
                for slice in self.chunk_dates(self.date_from, self.date_to, self.chunked_logs_params["split_range_days_count"]):
                    self._is_report_ready_to_load = False
                    logger.info(f"Current slice: {slice}")
                    while True:
                        yield slice
                        if self._is_report_ready_to_load:
                            break
                        else:
                            logger.info(f"Sleep for 10 sec...")
                            sleep(10)


# Source
class SourceAppmetricaLogsApi(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        config = SourceAppmetricaLogsApi.prepare_config(config)
        source_type = config["source"]
        available_fields = AVAILABLE_FIELDS[source_type]["fields"].keys()
        if config.get("check_fields", True):
            for field in config.get("fields", []):
                if field not in available_fields:
                    return False, f'Field "{field}" is invalid for source type {source_type}'

        if config.get("event_name_list") and config["source"] != "events":
            return False, f'event_name_list is not available for source {config["source"]}'

        try:
            json.loads(config.get("custom_json", "{}"))
        except Exception as msg:
            return False, f"Invalid Custom Constants JSON: {msg}"

        for filter_n, filter in enumerate(config.get("filters", [])):
            name = filter["name"]
            if name not in available_fields:
                return False, f"Filter {filter_n} ({name}) not in available fields list."

        auth = SourceAppmetricaLogsApi.get_auth(config)
        if isinstance(auth, CredentialsCraftAuthenticator):
            cc_auth_check_result = auth.check_connection()
            if not cc_auth_check_result[0]:
                return cc_auth_check_result

        applications_list_request = requests.get(
            "https://api.appmetrica.yandex.ru/management/v1/applications", headers=auth.get_auth_header()
        )
        if applications_list_request.status_code != 200:
            return False, f"Test API request error {applications_list_request.status_code}: {applications_list_request.text}"
        applications_list = applications_list_request.json()["applications"]
        available_ids_list = [app["id"] for app in applications_list]
        if config["application_id"] not in available_ids_list:
            return False, "Auth token is valid, but Application ID is invalid"

        return True, None

    @staticmethod
    def prepare_config_dates(config: Mapping[str, Any]) -> Mapping[str, Any]:
        date_range = config["date_range"]
        range_type = config["date_range"]["date_range_type"]
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        prepared_range = {}
        if range_type == "custom_date":
            prepared_range["date_from"] = date_range["date_from"]
            prepared_range["date_to"] = date_range["date_to"]
        elif range_type == "from_start_date_to_today":
            prepared_range["date_from"] = date_range["date_from"]
            if date_range["should_load_today"]:
                prepared_range["date_to"] = today
            else:
                prepared_range["date_to"] = today - timedelta(days=1)
        elif range_type == "last_n_days":
            prepared_range["date_from"] = today - timedelta(days=date_range["last_days_count"])
            if date_range["should_load_today"]:
                prepared_range["date_to"] = today
            else:
                prepared_range["date_to"] = today - timedelta(days=1)
        else:
            raise ValueError("Invalid date_range_type")

        if isinstance(prepared_range["date_from"], str):
            prepared_range["date_from"] = datetime.strptime(prepared_range["date_from"], DATE_FORMAT)

        if isinstance(prepared_range["date_to"], str):
            prepared_range["date_to"] = datetime.strptime(prepared_range["date_to"], DATE_FORMAT)
        config["prepared_date_range"] = prepared_range
        return config

    @staticmethod
    def get_auth(config: Mapping[str, Any]) -> TokenAuthenticator:
        if config["credentials"]["auth_type"] == "access_token_auth":
            return TokenAuthenticator(config["credentials"]["access_token"])
        elif config["credentials"]["auth_type"] == "credentials_craft_auth":
            return CredentialsCraftAuthenticator(
                credentials_craft_host=config["credentials"]["credentials_craft_host"],
                credentials_craft_token=config["credentials"]["credentials_craft_token"],
                credentials_craft_token_id=config["credentials"]["credentials_craft_token_id"],
            )
        else:
            raise Exception("Invalid Auth type. Available: access_token_auth and credentials_craft_auth")

    @staticmethod
    def prepare_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config = SourceAppmetricaLogsApi.prepare_config_dates(config)
        return config

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        config = SourceAppmetricaLogsApi.prepare_config(config)
        auth = SourceAppmetricaLogsApi.get_auth(config)
        stream = AppmetricaLogsApiStream(
            authenticator=auth,
            application_id=config["application_id"],
            date_from=config["prepared_date_range"]["date_from"],
            date_to=config["prepared_date_range"]["date_to"],
            chunked_logs_params=config.get("chunked_logs", {"split_mode_type": "do_not_split_mode"}),
            fields=config.get("fields", []),
            source=config["source"],
            filters=config.get("filters", []),
            date_dimension=config.get("date_dimension", "default"),
            product_name=config.get("product_name", ""),
            client_name=config.get("client_name", ""),
            custom_json=json.loads(config.get("custom_json", "{}")),
            event_name_list=config.get("event_name_list"),
            iter_content_chunk_size=config.get('iter_content_chunk_size', 8192)
        )
        return [stream]
