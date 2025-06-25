#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from typing import (
    Any,
    List,
    Mapping,
    Tuple,
)

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_protocol.models import SyncMode

from .utils import get_config_date_range
from .streams.base import FraudscoreStream
from .streams.events_list import EventListStream
from .streams.events_groupings import EventGroupingsStream
from .streams.events_stream_base import EventType


# Source
class SourceFraudscore(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, Any]:
        streams = self.streams(config)
        if not streams:
            return (
                False,
                "Нет сконфигурированных стримов. Настройте хотя бы один, выбрав все нужные дял него поля",
            )
        stream = streams[0]
        stream.page_size = 1
        try:
            next(stream.read_records(sync_mode=SyncMode.full_refresh))
        except Exception as ex:
            return False, ex
        return True, None

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config["time_from_transformed"], config["time_to_transformed"] = (
            get_config_date_range(config)
        )
        # For future improvements
        return config

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        config = self.transform_config(config)

        channel: str = config["channel"]
        user_key: str = config["user_key"]
        time_from = config["time_from_transformed"]
        time_to = config["time_to_transformed"]

        streams: list[FraudscoreStream] = []

        # Event list stream
        event_type: EventType | None = config.get("event_list_type")
        event_list_fields: list[str] | None = config.get("event_list_fields")
        if event_type and event_list_fields:
            assert event_type is not None  # To shut ide index warning (or even mypy)
            event_list_stream = EventListStream(
                channel=channel,
                user_key=user_key,
                event=event_type,
                fields=event_list_fields,
                time_from=time_from,
                time_to=time_to,
            )
            streams.append(event_list_stream)

        # Event groupings stream
        group_type: EventType | None = config.get("event_group_type")
        event_group_fields: list[str] | None = config.get("event_group_fields")
        event_group_groups: list[str] | None = config.get("event_group_groups")
        if group_type and event_group_fields and event_group_groups:
            assert group_type is not None
            event_group_stream = EventGroupingsStream(
                channel=channel,
                user_key=user_key,
                event=group_type,
                fields=event_group_fields,
                group=event_group_groups,
                time_from=time_from,
                time_to=time_to,
            )
            streams.append(event_group_stream)
        return streams
