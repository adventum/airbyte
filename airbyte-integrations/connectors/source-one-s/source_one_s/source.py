from functools import cached_property
from typing import Iterable, Mapping, MutableMapping

import pendulum
import requests
from airbyte_cdk import ResourceSchemaLoader, package_name_from_class
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.requests_native_auth import BasicHttpAuthenticator
from .utils import get_config_date_range, translate_name


class OneSStream(HttpStream):
    """Base stream for 1C (You can not call class 1C in python)"""

    primary_key = None

    def __init__(
        self,
        authenticator: BasicHttpAuthenticator,
        base_url: str,
        stream_path: str,
        start_date: pendulum.DateTime,
        end_date: pendulum.DateTime,
        stream_name: str | None = None,
        use_name_translation: bool = False,
    ):
        self._authenticator: BasicHttpAuthenticator = authenticator
        self._base_url: str = base_url
        self._stream_path: str = stream_path
        self._start_date: pendulum.DateTime= start_date
        self._end_date: pendulum.DateTime= end_date
        self._stream_name: str = translate_name(stream_name or stream_path)
        self._schema_json: Mapping[str, any] | None = None
        self._use_name_translation: bool = use_name_translation

        # Calling super().__init__(...) before setting _stream_name fails source
        # because super needs name property which can not be used before full init
        super().__init__(authenticator)

    @property
    def url_base(self) -> str:
        return self._base_url + "/"

    @cached_property
    def name(self) -> str:
        return self._stream_name

    def path(
        self,
        *,
        stream_state: Mapping[str, any] | None = None,
        stream_slice: Mapping[str, any] | None = None,
        next_page_token: Mapping[str, any] | None = None,
    ) -> str:
        return self._stream_path

    def next_page_token(self, response: requests.Response) -> Mapping[str, any] | None:
        return None

    def request_params(
        self,
        stream_state: Mapping[str, any],
        stream_slice: Mapping[str, any] = None,
        next_page_token: Mapping[str, any] = None,
    ) -> MutableMapping[str, any]:
        return {
            "StartDate": self._start_date.format("YYYYMMDD"),
            "EndDate": self._end_date.format("YYYYMMDD"),
        }

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        response.encoding = "utf-8"
        for record in response.json()["Data"]:
            if self._use_name_translation:
                record = {translate_name(key): value for key, value in record.items()}
            yield record

    def make_test_request(self) -> requests.Response:
        test_params = self.request_params({})
        request = requests.get(
            self.url_base + self.path(),
            params=test_params,
            headers={self._authenticator.auth_header: self._authenticator.token},
        )
        request.encoding = "utf-8"
        return request

    def get_json_schema(self) -> Mapping[str, any]:
        if self._schema_json is None:
            data: dict[str, any] = self.make_test_request().json()
            fields: list[str] = list(data["Data"][0].keys())
            schema = ResourceSchemaLoader(
                package_name_from_class(self.__class__)
            ).get_schema("one_s_stream")
            for field in fields:
                field_name = field if not self._use_name_translation else translate_name(field)
                schema["properties"][field_name] = {"type": ["null", "string"]}
            self._schema_json = schema
        return self._schema_json


class SourceOneS(AbstractSource):
    @staticmethod
    def transform_config(config: Mapping[str, any]) -> Mapping[str, any]:
        # TODO: may be used in the nearest future
        return config

    def check_connection(self, logger, config) -> tuple[bool, any]:
        # Check configuration
        streams = self.streams(config)
        stream_names: list[str] = [stream.name for stream in streams]
        if len(stream_names) != len(set(stream_names)):
            return (
                False,
                "Имена стримов должны быть уникальными. Попробуйте переименовать ваши стримы. Названия Test и test считаются одинаковыми",
            )
        # Check connection
        txt = "Произошла ошибка при обращении к 1С"
        try:
            response = streams[0].make_test_request()
            txt = response.text
            assert response.status_code == 200 and response.json()["status"] == 200
        except Exception:
            return False, txt
        return True, None

    def streams(self, config: Mapping[str, any]) -> list[OneSStream]:
        config = self.transform_config(config)
        start_date, end_date = get_config_date_range(config)

        match config["credentials"]["auth_type"]:
            case "password":
                auth = BasicHttpAuthenticator(
                    username=config["credentials"]["login"],
                    password=config["credentials"]["password"],
                )
            case _:
                raise NotImplementedError(
                    "Коннектор 1С пока поддерживает авторизацию только по логину и паролю"
                )

        streams = []
        for stream_data in config["streams"]:
            stream = OneSStream(
                authenticator=auth,
                base_url=config["base_url"],
                stream_path=stream_data["path"],
                start_date=start_date,
                end_date=end_date,
                stream_name=stream_data.get("name"),
                use_name_translation=config.get("use_name_translation", False),
            )
            streams.append(stream)

        return streams
