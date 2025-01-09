from typing import Optional, Mapping, Any, List, Iterable

import pendulum
from airbyte_cdk.sources.streams.core import StreamData
from airbyte_protocol.models import SyncMode

from .base_stream import SapeXMLStream


class GetAvgPrices(SapeXMLStream):
    """
    get_avg_prices method
    Simplest stream
    """

    primary_key = None

    def path(
        self,
    ) -> str:
        return "get_avg_prices"

    def args(self) -> list[Any] | None:
        return None


class GetProjectsMoneyStats(SapeXMLStream):
    primary_key = None

    def path(self) -> str:
        return "get_projects_money_stats"

    def args(self) -> list[Any] | None:
        return None

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: Optional[List[str]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        stream_state: Optional[Mapping[str, Any]] = None,
    ) -> Iterable[StreamData]:
        # That's easier to get all data and filter here than using Sape date filters
        # because Sape date filters does not support > or <, only equals filter
        for record in super().read_records(
            sync_mode, cursor_field, stream_slice, stream_state
        ):
            record_date = pendulum.parse(record["date_logged"])
            if self._start_date <= record_date <= self._end_date:
                yield record


# class RtbGetStats(SapeXMLStream):
#     base_path = "rtb"
#
#     def path(self) -> str:
#         return "get_stats"
#
#     def stream_slices(
#         self, *, sync_mode: SyncMode, cursor_field: Optional[List[str]] = None, stream_state: Optional[Mapping[str, Any]] = None
#     ) -> Iterable[Optional[Mapping[str, Any]]]:
#
#
#     def args(self) -> list[Any] | None:
#         return [
#             pendulum.DateTime(
#                 year=self._start_date.year,
#                 month=self._start_date.month,
#                 day=self._start_date.day,
#             ).int_timestamp,
#             pendulum.DateTime(
#                 year=self._end_date.year,
#                 month=self._end_date.month,
#                 day=self._end_date.day,
#             ).int_timestamp,
#         ]
