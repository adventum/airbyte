#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#
import io
import time
from datetime import datetime, timedelta
from typing import Any, Iterable, Mapping, MutableMapping, Optional, List

import pandas as pd
import pendulum
import requests
from airbyte_cdk import TokenAuthenticator
from airbyte_cdk.sources.streams.core import package_name_from_class, StreamData
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.utils.schema_helpers import ResourceSchemaLoader
from airbyte_cdk.sources.utils.transform import TransformConfig, TypeTransformer
from airbyte_protocol.models import SyncMode

from .fields import AVAILABLE_FIELDS


class AppmetricaLogsApiStream(HttpStream):
    url_base = "https://api.appmetrica.yandex.ru/"
    primary_key = []
    transformer: TypeTransformer = TypeTransformer(
        config=TransformConfig.DefaultSchemaNormalization
    )
    should_redownload = False
    datetime_format = "YYYY-MM-DD HH:mm:ss"

    def __init__(
        self,
        *,
        authenticator: TokenAuthenticator = None,
        application_id: int,
        date_from: pendulum.DateTime,
        date_to: pendulum.DateTime,
        chunked_logs_params: Mapping[str, Any],
        fields: list[str],
        source: str,
        filters: list[Mapping[str, str]] = None,
        date_dimension: str = "default",
        event_name_list: list[str] = None,
    ):
        # setting source after super().__init__ will break name property
        self.source = source
        super().__init__(authenticator)
        self._token = authenticator._token
        self.application_id = application_id
        self.date_from = date_from
        self.date_to = date_to
        self.event_name_list = (
            event_name_list if event_name_list is not None else [None]
        )
        self.chunked_logs_params = chunked_logs_params

        self.fields = fields if fields else AVAILABLE_FIELDS[source]["fields"].keys()
        self.filters = filters
        self.date_dimension = date_dimension

    def path(self, *args, **kwargs) -> str:
        return f"logs/v1/export/{self.source}.csv"

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        return None

    @property
    def name(self) -> str:
        return self.source

    @staticmethod
    def filters_into_request_params(
        filters: list[Mapping[str, str]],
    ) -> Mapping[str, Any]:
        params = {}
        for filter in filters:
            if filter["name"] not in params.keys():
                params[filter["name"]] = []
            params[filter["name"]].append(filter["value"])
        return params

    def request_params(
        self, stream_slice: Mapping[str, any] = None, *args, **kwargs
    ) -> MutableMapping[str, Any]:
        params = {
            "application_id": self.application_id,
            "date_since": stream_slice["date_from"].format(self.datetime_format),
            "date_until": stream_slice["date_to"].format(self.datetime_format),
            "fields": ",".join(self.fields),
            "date_dimension": self.date_dimension,
        }
        if stream_slice.get("event_name"):
            params["event_name"] = stream_slice.get("event_name")
        if self.filters:
            params.update(self.filters_into_request_params(self.filters))
        return params

    def get_json_schema(self) -> Mapping[str, Any]:
        schema = ResourceSchemaLoader(
            package_name_from_class(self.__class__)
        ).get_schema("appmetrica_report")

        for field_name in self.fields:
            lookup_field_type = AVAILABLE_FIELDS[self.source]["fields"].get(
                field_name, "string"
            )
            schema["properties"][field_name] = {"type": ["null", lookup_field_type]}

        return schema

    def make_request(
        self, stream_slice: Mapping[str, any] = None, **kwargs
    ) -> requests.Response:
        response = requests.get(
            self.url_base + self.path(),
            headers={"Authorization": f"OAuth {self._token}"},
            params=self.request_params(stream_slice=stream_slice),
        )
        return response

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping[str, Any]]:
        raise NotImplementedError()

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: Optional[List[str]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        stream_state: Optional[Mapping[str, Any]] = None,
    ) -> Iterable[StreamData]:
        self.logger.info(f"Started stream {stream_slice}")
        response = self.make_request(stream_slice)
        i: int = 0
        waited_time: int = 0
        while response.status_code == 202:
            wait_time = min((i + 0.2) * 10, 60)
            self.logger.info(
                f"Stream is being prepared on yandex server: {stream_slice}. "
                f"Already waiting: {waited_time} seconds, waiting for {wait_time} seconds more."
            )
            time.sleep(wait_time)
            i += 1
            waited_time += wait_time
            response = self.make_request(stream_slice)
        df = pd.read_csv(io.StringIO(response.content.decode("utf-8")))
        del response
        df.fillna("", inplace=True)
        for _, row in df.iterrows():
            yield row.to_dict()

    @staticmethod
    def chunk_dates(
        date_from: datetime, date_to: datetime, chunk_days_count: int
    ) -> list[dict[str, pendulum.DateTime]]:
        """Split dates into different intervals if apply split mode"""
        chunks = []
        cursor = date_from
        while cursor <= date_to:
            chunk_date_from = cursor
            chunk_date_to = (cursor.add(days=chunk_days_count - 1)).replace(
                hour=23, minute=59, second=59
            )
            if chunk_date_to > date_to:
                chunk_date_to = date_to.replace(hour=23, minute=59, second=59)
            chunks.append({"date_from": chunk_date_from, "date_to": chunk_date_to})
            cursor += timedelta(days=chunk_days_count)
        return chunks

    def stream_slices(self, *args, **kwargs) -> Iterable[Optional[Mapping[str, Any]]]:
        if self.chunked_logs_params["split_mode_type"] == "do_not_split_mode":
            chunks = [
                {
                    "date_from": self.date_from,
                    "date_to": self.date_to,
                }
            ]
        else:
            chunks = self.chunk_dates(
                self.date_from,
                self.date_to,
                self.chunked_logs_params["split_range_days_count"],
            )

        for chunk in chunks:
            if self.event_name_list:
                for event_name in self.event_name_list:
                    yield chunk | {"event_name": event_name}
            else:
                yield chunk
