#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from cgi import test
import csv
import io
import json
import logging
import re
from abc import ABC
from datetime import datetime
from functools import cache
from typing import Any, Dict, Iterable, List, Literal, Mapping, MutableMapping, Optional, Tuple
from airbyte_cdk.models import SyncMode
from datetime import datetime, timedelta

import pandas as pd
import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.core import package_name_from_class
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator
from airbyte_cdk.sources.utils.schema_helpers import ResourceSchemaLoader
from airbyte_cdk.sources.utils.transform import TransformConfig, TypeTransformer
from source_yandex_disk.auth import CredentialsCraftAuthenticator
from source_yandex_disk.utils import find_duplicates

logger = logging.getLogger('airbyte')

# Basic full refresh stream


class YandexDiskResource(HttpStream, ABC):
    url_base = "https://downloader.disk.yandex.ru/disk/"
    primary_key = []
    limit = 1000
    transformer: TypeTransformer = TypeTransformer(
        config=TransformConfig.DefaultSchemaNormalization)

    def __init__(
        self,
        authenticator: TokenAuthenticator,
        stream_name: str,
        resources_path: str,
        resources_filename_pattern: re.Pattern,
        resource_files_type: Literal['CSV', 'Excel'],
        excel_sheet_name: str,
        custom_constants: Dict[str, Any],
        user_specified_fields: List[str] = [],
        csv_delimiter: str = None,
        no_header: bool = False,
        date_from: datetime = None,
        date_to: datetime = None,
        field_name_map: Optional[dict[str, str]] = None,
        field_name_map_individual: Optional[dict[str, str]] = None,
        path_placeholder: str = None,
    ) -> None:
        super().__init__(authenticator=authenticator)

        # Copy of the authenticator has been added for correct operation of authorization via CC
        self.authenticator_copy = authenticator
        self.stream_name = stream_name
        self.resources_path = resources_path
        self.resources_filename_pattern = re.compile(
            resources_filename_pattern)
        self.resource_files_type = resource_files_type
        self.excel_sheet_name = excel_sheet_name
        self.custom_constants = custom_constants
        self.user_specified_fields = user_specified_fields
        self.csv_delimiter = csv_delimiter
        self.no_header = no_header
        self.date_from = date_from
        self.date_to = date_to
        self._field_name_map = field_name_map
        self.field_name_map_individual = field_name_map_individual
        self.path_placeholder = path_placeholder

    @property
    def name(self) -> str:
        return self.stream_name

    def get_json_schema(self) -> Mapping[str, Any]:
        schema = ResourceSchemaLoader(package_name_from_class(
            self.__class__)).get_schema("yandex_disk_resource")
        properties = schema["properties"]

        if self.user_specified_fields:
            fields = self.user_specified_fields
        else:
            fields = self.derive_fields_names_from_sample()

        for field_name in fields:
            schema["properties"][field_name] = {"type": ["null", "string"]}

        extra_properties = ["__filepath"]
        extra_properties.extend(self.custom_constants.keys())

        if extra_properties:
            for key in extra_properties:
                schema["properties"][key] = {"type": ["null", "string"]}

        # Replace properties keys
        replacements = {}
        for old_val, new_val in self._field_name_map.items():
            if old_val in properties:
                replacements[old_val] = new_val

        for old_val, new_val in replacements.items():
            properties[new_val] = properties.pop(old_val)

        return schema

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def request_params(self, *args, **kwargs) -> MutableMapping[str, Any]:
        return {}

    def path(self, stream_slice: Mapping[str, Any] = None, *args, **kwargs) -> str:
        return stream_slice['href']

    @staticmethod
    def add_filepath_to_record(record: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        record["__filepath"] = file_path
        return record

    def apply_field_name_map(self, record: Dict[str, Any], field_name_map_individual: Dict[str, str]) -> Dict[str, Any]:
        for record_key in list(record.keys()):
            if record_key in field_name_map_individual:
                record[field_name_map_individual[record_key]] = record.pop(record_key)
        return record

    def parse_csv_response(self, response: requests.Response, file_path) -> Iterable[Mapping]:
        lines_gen = (line.decode("utf-8").replace('\ufeff', '')
                     for line in response.iter_lines())

        if self.csv_delimiter:
            lines_reader = csv.reader(lines_gen, delimiter=self.csv_delimiter)
        else:
            lines_reader = csv.reader(lines_gen)
        if not self.no_header:
            if self.user_specified_fields:
                next(lines_reader)
                headers = self.user_specified_fields
            else:
                headers = next(lines_reader)
        else:
            headers = self.user_specified_fields

        for values_line_n, values_line in enumerate(lines_reader):
            if values_line_n == 0:
                if self.user_specified_fields and len(values_line) != len(self.user_specified_fields):
                    if len(values_line) == 0:
                        continue
                    raise Exception(
                        f'Stream {self.stream_name} user_specified_fields'
                        ' count doesn\'t equals to files columns count. '
                        '(user_specified_fields count - '
                        f'{len(self.user_specified_fields)}, columns '
                        f'count - {len(values_line)}).'
                    )
            record = dict(zip(headers, values_line))
            for record_key in list(record.keys()):
                if record_key in self._field_name_map:
                    record[self._field_name_map[record_key]] = record.pop(record_key)

            record = self.apply_field_name_map(record, self.field_name_map_individual)

            if record:
                record = self.add_constants_to_record(record)
                record = self.add_filepath_to_record(record, file_path)
                yield record

    def parse_excel_response(self, response: requests.Response, file_path) -> Iterable[Mapping]:
        with io.BytesIO(response.content) as fh:
            read_excel_kwargs = {
                "sheet_name": self.excel_sheet_name if self.excel_sheet_name else 0
            }

            if self.no_header:
                read_excel_kwargs['header'] = None
                read_excel_kwargs['names'] = self.user_specified_fields
            else:
                if self.user_specified_fields:
                    read_excel_kwargs['names'] = self.user_specified_fields

            df = pd.io.excel.read_excel(fh, **read_excel_kwargs)

            for record in df.to_dict('records'):
                for record_key in list(record.keys()):
                    if record_key in self._field_name_map:
                        record[self._field_name_map[record_key]] = record.pop(record_key)

                record = self.apply_field_name_map(record, self.field_name_map_individual)
                record = self.add_constants_to_record(record)
                record = self.add_filepath_to_record(record, file_path)
                yield record

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        file_path = kwargs.get("file_path") or kwargs.get("stream_slice", {}).get("file_path")
        if self.resource_files_type == 'CSV':
            yield from self.parse_csv_response(response, file_path)
        elif self.resource_files_type == 'Excel':
            yield from self.parse_excel_response(response, file_path)
        else:
            raise Exception(
                f'Unsupported file type: {self.resource_files_type}')

    def add_constants_to_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        constants = {
        }
        constants.update(self.custom_constants)
        if constants:
            record.update(constants)
        return record

    def request_kwargs(self, *args, **kwargs) -> Mapping[str, Any]:
        request_kwargs: Dict = super().request_kwargs(*args, **kwargs)
        request_kwargs.update({"stream": True})
        return request_kwargs

    def get_path_resources(self):
        available_resources = []
        offset = 0
        while True:
            resources_response = requests.get(
                url='https://cloud-api.yandex.net/v1/disk/resources',
                params={
                    'path': self.resources_path,
                    'limit': self.limit,
                    'offset': offset,
                    'sort': '-created'
                },
                headers=self.authenticator_copy.get_auth_header()
            )
            try:
                resources_response.raise_for_status()
            except:
                raise Exception(
                    f'Api Error {resources_response.status_code}: {resources_response.text}. URL {resources_response.request.url}')
            resources_response_items = resources_response.json()[
                '_embedded'].get('items')
            available_resources = [
                *available_resources,
                *resources_response_items
            ]
            if len(resources_response_items) < self.limit:
                break
            offset += self.limit
        return available_resources

    def derive_fields_names_from_sample(self):
        sample_file = self.lookup_resources_for_pattern()[0]
        download_file_link = self.get_download_link_for_resource(sample_file)['href']
        sample_record: Dict[str, Any] = next(self.parse_response(
            requests.get(
                download_file_link,
                headers=self.authenticator_copy.get_auth_header()
            ),
            file_path=sample_file['path']
        ))
        fields = sample_record.keys()
        print(f'Fields for stream {self.name}: {fields}')
        logger.info(f'Fields for stream {self.name}: {fields}')
        return fields

    def lookup_resources_for_pattern(self):
        availabe_path_resources = self.get_path_resources()
        resources = []
        for resource in filter(lambda r: r['type'] == 'file', availabe_path_resources):
            if self.resources_filename_pattern.match(resource['name']):
                resources.append(resource)
        if not resources:
            available_resource_names = list(
                map(
                    lambda r: '\'' + r.get('name', '<empty name>') + '\'',
                    availabe_path_resources
                )
            )
            raise Exception(
                f'Resources for stream \'{self.name}\' with pattern '
                f'\'{self.resources_filename_pattern.pattern}\' not found,'
                ' so it\'s failed to derive field names from sample file.'
                ' Specify \'user_specified_fields\' for this stream or check your'
                f' path or pattern for stream \'{self.name}\'. Available'
                f" resources with this stream \'path\': "
                f"{', '.join(available_resource_names)}."
            )
        logger.info(
            f'Stream {self.name}: found resources for pattern'
            f' {self.resources_filename_pattern}:'
            f' {[resource["path"] for resource in resources]}'
        )
        return resources

    def get_download_link_for_resource(self, resource):
        download_link_response = requests.get(
            url='https://cloud-api.yandex.net/v1/disk/resources/download',
            params={
                'path': resource['path']
            },
            headers=self.authenticator_copy.get_auth_header()
        )
        download_link_response.raise_for_status()
        download_link_obj = download_link_response.json()
        logger.info(
            f'Stream {self.name}: download link for resource'
            f' {resource["path"]} - {download_link_obj["href"]}'
        )
        return download_link_obj

    def stream_slices(self, *args, **kwargs) -> Iterable[Optional[Mapping[str, Any]]]:
        for resource in self.lookup_resources_for_pattern():
            file = self.get_download_link_for_resource(resource)
            file['href'] = file['href'].replace(self.url_base, '')
            file['file_path'] = f"{self.resources_path}/{resource['name']}"
            yield file


class SourceYandexDisk(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        try:
            json.loads(config.get("custom_constants_json", "{}"))
        except Exception as msg:
            return False, f"Invalid Custom Constants JSON: {msg}"
        
        stream_names = [stream_config['name'] for stream_config in config['streams']]
        stream_name_duplicates = find_duplicates(stream_names)
        if stream_name_duplicates:
            return False, f'Each stream name must be unique. Stream names duplicates: {stream_name_duplicates}'

        for stream_config in config['streams']:
            if stream_config.get('no_header', False) and not stream_config.get('user_specified_fields'):
                return False, f'"No Header" selected for stream {stream_config["name"]},' + \
                    ' but no user_specified_fields specified. Connector can\'t derive' + \
                    ' fields from sample file sinse you turn on \'No header\''

        auth = self.get_auth(config)
        if isinstance(auth, CredentialsCraftAuthenticator):
            cc_auth_check_result = auth.check_connection()
            if not cc_auth_check_result[0]:
                return cc_auth_check_result

        for stream in self.streams(config):
            stream.get_json_schema()

        return True, None

    @staticmethod
    def get_auth(config: Mapping[str, Any]) -> TokenAuthenticator:
        if config["credentials"]["auth_type"] == "access_token_auth":
            return TokenAuthenticator(
                token=config["credentials"]["access_token"],
                auth_method='OAuth'
            )
        elif config["credentials"]["auth_type"] == "credentials_craft_auth":
            return CredentialsCraftAuthenticator(
                credentials_craft_host=config["credentials"]["credentials_craft_host"],
                credentials_craft_token=config["credentials"]["credentials_craft_token"],
                credentials_craft_token_id=config["credentials"]["credentials_craft_token_id"],
            )
        else:
            raise Exception(
                "Invalid Auth type. Available: access_token_auth and credentials_craft_auth")

    @staticmethod
    def get_field_name_map(config: Mapping[str, any]) -> dict[str, str]:
        """Get values that needs to be replaced and their replacements"""
        field_name_map: Optional[list[dict[str, str]]]
        field_name_map = config.get("field_name_map")
        if not field_name_map:
            return {}
        else:
            return {item["old_value"]: item["new_value"] for item in field_name_map}

    @staticmethod
    def get_date_range(date_from: str, date_to: str) -> Tuple[datetime, datetime]:
        start = datetime.strptime(date_from, '%Y-%m-%d')
        end = datetime.strptime(date_to, '%Y-%m-%d')
        return start, end

    @staticmethod
    def get_last_days_date_range(n_days: int) -> Tuple[datetime, datetime]:
        end = datetime.now()
        start = end - timedelta(days=n_days)
        return start, end

    @staticmethod
    def contains_placeholder(file_path: str) -> bool:
        return "{placeholder}" in file_path

    @staticmethod
    def contains_date_placeholder(file_path: str) -> str:
        # Returns a format like %Y-%m-%d
        searching_pattern = r'!(.*?)!'
        is_match = re.search(searching_pattern, file_path)

        if is_match:
            extracted_string = is_match.group(1)
            return extracted_string

    @staticmethod
    def transform_file_path_and_files_pattern(stream_config: dict[str, Any], config: dict[str, Any]):
        if config.get("path_placeholder"):
            path_placeholder = config["path_placeholder"]

            files_pattern = stream_config["files_pattern"]
            if SourceYandexDisk.contains_placeholder(files_pattern):
                updated_files_pattern = files_pattern.replace("{placeholder}", path_placeholder)
                stream_config["files_pattern"] = updated_files_pattern

            files_path = stream_config["path"]
            if SourceYandexDisk.contains_placeholder(files_path):
                updated_files_path = files_path.replace("{placeholder}", path_placeholder)
                stream_config["path"] = updated_files_path
        return stream_config

    @staticmethod
    def transform_file_path_and_files_pattern_for_date(stream_config: dict[str, Any], config: dict[str, Any], date_from: datetime):
        if config.get("date_range"):
            date_path_placeholder_raw = date_from

            # Getting date format from Files Pattern
            files_pattern = stream_config["files_pattern"]
            extracted_date_format = SourceYandexDisk.contains_date_placeholder(files_pattern)

            if extracted_date_format:

                parsed_date = date_path_placeholder_raw
                formatted_date = parsed_date.strftime(extracted_date_format)

                updated_files_pattern = files_pattern.replace(f"!{extracted_date_format}!", formatted_date)
                stream_config["files_pattern"] = updated_files_pattern

            # Getting date format from Path
            files_path = stream_config["path"]
            extracted_date_format_path = SourceYandexDisk.contains_date_placeholder(files_path)
            if extracted_date_format_path:

                parsed_date = date_path_placeholder_raw
                formatted_date = parsed_date.strftime(extracted_date_format_path)

                updated_files_path = files_path.replace(f"!{extracted_date_format_path}!", formatted_date)
                stream_config["path"] = updated_files_path
        return stream_config

    def transform_config(self, config: dict[str, Any]) -> dict[str, Any]:
        config["field_name_map"] = SourceYandexDisk.get_field_name_map(config)

        return config

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        authenticator = self.get_auth(config)
        config = self.transform_config(config)
        streams = []
        logger.info(f'Streams: {config["streams"]}')

        for stream_config in config['streams']:
            user_specified_fields = stream_config.get(
                'user_specified_fields', '').strip().split(',')
            if user_specified_fields == ['']:
                user_specified_fields = None

            # Date range handling
            date_from, date_to = None, None
            date_type_choiced = config["date_range"]["date_range_type"]
            if date_type_choiced == "custom_date":
                date_from, date_to = self.get_date_range(
                    config["date_range"]["date_from"],
                    config["date_range"]["date_to"]
                )
            elif date_type_choiced == "last_n_days":
                date_from, date_to = self.get_last_days_date_range(
                    config["date_range"]["last_days"]
                )

            stream_config = SourceYandexDisk.transform_file_path_and_files_pattern(stream_config, config)
            stream_config = SourceYandexDisk.transform_file_path_and_files_pattern_for_date(stream_config, config, date_from)

            streams.append(
                YandexDiskResource(
                    authenticator=authenticator,
                    stream_name=stream_config['name'],
                    resources_path=stream_config['path'],
                    resources_filename_pattern=stream_config['files_pattern'],
                    resource_files_type=stream_config['files_type'],
                    excel_sheet_name=stream_config.get('excel_sheet_name'),
                    field_name_map=config.get("field_name_map"),
                    field_name_map_individual={item["old_value_individual"]:
                                               item["new_value_individual"] for item in stream_config.get("field_name_map_individual", [])},
                    custom_constants=json.loads(
                        config.get('custom_constants_json', '{}')
                    ),
                    user_specified_fields=user_specified_fields,
                    csv_delimiter=stream_config.get('csv_delimiter'),
                    no_header=stream_config.get('no_header'),
                    path_placeholder=config.get("path_placeholder"),
                    date_from=date_from,
                    date_to=date_to,
                )
            )
        return streams
