from typing import Optional, Mapping, Any, Iterable

import pendulum
import requests
from airbyte_protocol.models import SyncMode

from .base_stream import SapeRestStream


class ExtendedStatistics(SapeRestStream):
    primary_key = None
    datetime_format = "YYYY-MM-DD HH:mm:ss"
    http_method = "POST"

    def path(
        self,
        *,
        stream_state: Optional[Mapping[str, Any]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> str:
        return "statistics/extended"

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        data = response.json()
        pagination = data["pager"]
        page_count = pagination["pageMax"]
        current_page = pagination["pageNum"]
        if current_page < page_count:
            return current_page + 1
        return None

    def stream_slices(
        self,
        *,
        sync_mode: SyncMode,
        cursor_field: list[str] | None = None,
        stream_state: Mapping[str, any] | None = None,
    ) -> Iterable[Mapping[str, any] | None]:
        tmp_start_date: pendulum.Date = self.start_date
        tmp_end_date: pendulum.Date = min(self.start_date.add(days=30), self.end_date)
        while tmp_end_date < self.end_date:
            time_from = pendulum.DateTime(
                year=tmp_start_date.year,
                month=tmp_start_date.month,
                day=tmp_start_date.day,
            )
            end_date = tmp_end_date.subtract(
                days=1
            )  # According to Sape api usage on web page
            time_to = pendulum.DateTime(
                year=end_date.year,
                month=end_date.month,
                day=end_date.day,
                hour=23,
                minute=59,
                second=59,
            )

            yield {
                "start_date": time_from.format(format(self.datetime_format)),
                "end_date": time_to.format(format(self.datetime_format)),
            }

            tmp_start_date = tmp_start_date.add(days=30)
            tmp_end_date = tmp_end_date.add(days=30)

        if tmp_start_date <= tmp_end_date:
            time_to = pendulum.DateTime(
                year=self.end_date.year,
                month=self.end_date.month,
                day=self.end_date.day,
                hour=23,
                minute=59,
                second=59,
            )
            yield {
                "start_date": tmp_start_date.format(self.datetime_format),
                "end_date": time_to.format(self.datetime_format),
            }

    def request_body_json(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        # May be None only if request is first
        page_number = next_page_token if next_page_token else 1

        # TODO: may be updated later
        filters = []
        # group_by = "eventDate"
        fields = ["shows", "clicks", "cpm", "cpc", "amount"]
        params = {
            "filters": filters,
            # "groupBy": group_by,
            "fields": fields,
            "dateViewFrom": stream_slice["start_date"],
            "dateViewTo": stream_slice["end_date"],
            "pageSize": 100,
            "pageNum": page_number,
        }
        return params

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        yield from response.json()["statistics"]
