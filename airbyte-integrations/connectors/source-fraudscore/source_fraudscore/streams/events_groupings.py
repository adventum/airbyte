from typing import (
    Any,
    Mapping,
    Optional,
)

import pendulum
from airbyte_cdk import ResourceSchemaLoader, package_name_from_class

from .events_stream_base import EventStreamBase, EventType


class EventGroupingsStream(EventStreamBase):
    def __init__(
        self,
        channel: str,
        user_key: str,
        event: EventType,
        time_from: pendulum.DateTime,
        time_to: pendulum.DateTime,
        group: list[str],
        fields: list[str],
    ) -> None:
        super().__init__(channel, user_key, event, time_from, time_to)
        self._fields = fields
        self._group = group

    def path(
        self,
        *,
        stream_state: Optional[Mapping[str, Any]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> str:
        return f"{self._channel}/{self._event}/groups"

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> dict[str, Any]:
        return super().request_params(stream_state, stream_slice, next_page_token) | {
            "field": self._fields,
            "group": self._group,
        }

    def get_json_schema(self) -> dict[str, Any]:
        schema = ResourceSchemaLoader(
            package_name_from_class(self.__class__)
        ).get_schema("base_stream")
        for field in self._fields:
            schema["properties"][field] = {"type": ["null", "string"]}
        schema["properties"]["count"] = {"type": ["null", "integer"]}

        # TODO: figure out, it may actually be non needed
        schema["properties"]["date"] = {"type": ["null", "string"]}
        return schema
