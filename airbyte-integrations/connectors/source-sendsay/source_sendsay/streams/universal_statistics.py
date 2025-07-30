from functools import lru_cache
from typing import Mapping, Any, Optional, MutableMapping, Iterable

import requests
from airbyte_cdk import ResourceSchemaLoader, package_name_from_class

from .base import SendsayStream
import pendulum


class UniversalStatistics(SendsayStream):
    action_name = "stat.uni"
    primary_key = None

    def __init__(
        self,
        login: str,
        session: str,
        fields: list[str],
        date_field: str,
        time_from: pendulum.DateTime,
        time_to: pendulum.DateTime,
    ) -> None:
        super().__init__(
            login=login,
            session=session,
            time_from=time_from,
            time_to=time_to,
        )
        self._fields = fields
        self._date_field = date_field

    def request_body_json(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> MutableMapping[str, Any]:
        params = super().request_body_json(stream_state, stream_slice, next_page_token)
        params["select"] = self._fields
        params["filter"] = [
            {
                "a": self._date_field,
                "op": ">=",
                "v": self._time_from.to_datetime_string(),
            },
            {"a": self._date_field, "op": "<", "v": self._time_to.to_datetime_string()},
        ]
        return params

    def path(self, stream_slice: Mapping[str, Any] = None, **kwargs) -> str:
        return f"{self.url_base}{self._login}/"

    def parse_response(
        self,
        response: requests.Response,
        *,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Iterable[Mapping[str, Any]]:
        for row in response.json()["list"]:
            yield dict(zip(self._fields, row))

    @lru_cache
    def get_json_schema(self) -> Mapping[str, Any]:
        schema = ResourceSchemaLoader(
            package_name_from_class(self.__class__)
        ).get_schema("universal_statistics")
        for field in self._fields:
            schema["properties"][field] = {"type": ["null", "string"]}

        return schema
