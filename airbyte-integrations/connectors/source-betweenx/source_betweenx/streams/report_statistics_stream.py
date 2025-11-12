import logging
import pendulum
import requests

from typing import Any, Iterable, List, Mapping, Optional
from requests import Response
from urllib.parse import parse_qsl
from airbyte_protocol.models import SyncMode

from .base_stream import BetweenxStream
from ..utils import base_headers

logger = logging.getLogger(__name__)


class ReportStatistics(BetweenxStream):
    primary_key = "id"

    def __init__(
        self,
        token: str,
        date_from: pendulum.DateTime,
        date_to: pendulum.DateTime,
        is_group_by_date: bool,
        user_id: str | int,
        group_by_field: str | None = None,
        campaign_ids: list[str | int] | None = None,
    ):
        super().__init__()
        self.token = token
        self.date_from = date_from
        self.date_to = date_to
        self.group_by_field = group_by_field
        self.is_group_by_date = is_group_by_date
        self.user_id = user_id
        self.campaign_ids = campaign_ids if campaign_ids else []

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None
    ) -> str:
        return ""

    def stream_slices(
        self,
        *,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_state: Mapping[str, Any] = None,
    ) -> Iterable[Optional[Mapping[str, Any]]]:
        for campaign_id in self.campaign_ids:
            yield {
                "campaign_id": campaign_id,
            }

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: Optional[List[str]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        stream_state: Optional[Mapping[str, Any]] = None,
    ) -> Iterable[Mapping[str, Any]]:
        """
        Here we make two requests:
        1. We make a POST request to create a report
        and receive a link in the response with all the report IDs in the URL parameters.
        2. We retrieve the report records, passing the report IDs in the request parameters.
        """
        main_url = f"{self.url_base}/users/{self.user_id}/stats-agencylab/reportlist"
        main_headers = {
            "Authorization": f"Token {self.token}"
        } | base_headers

        str_date_start: str = self.date_from.format("YYYY-MM-DD")
        str_date_end: str= self.date_to.format("YYYY-MM-DD")

        # 1. Post request
        report_list_body = {
            "campaign_id": [int(stream_slice["campaign_id"])],
            "date_start": str_date_start,
            "date_end": str_date_end,
            "is_group_by_date": self.is_group_by_date,
        }
        if self.group_by_field:
            report_list_body["additional_group_by"] = self.group_by_field

        report_list_response: Response = requests.post(
            url=main_url,
            headers = main_headers,
            json=report_list_body,
        )
        report_list_response.raise_for_status()
        report_settings_url: str = report_list_response.json()["data"]["action"]["url"]

        # 2. Get report_ids, and request for final records
        # TODO: Add pagination (not needed for now)
        report_records_params: dict[str, str] = dict(
            parse_qsl(
                report_settings_url.split("?")[1]
            )
        )
        report_records_params["page_number"] = "1"
        report_records_params["page_size"] = "500"

        report_records_response: Response = requests.get(
            url=main_url,
            headers=main_headers,
            params=report_records_params,
        )
        report_records_response.raise_for_status()

        yield from self.parse_response(
            report_records_response, campaign_id=stream_slice["campaign_id"]
        )

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        """
        1. Get the campaign_id from stream_slice(kwargs)

        2. Convert the response from BetweenX to a list of dictionaries to make parsing easier
        (since if a single record is received, it's just a dictionary).

        3. Parse the records.

        3.1. If the User doesn't group by campaign_id, we add it to the final record.

        3.2. If a single record is received, grouping doesn't work,
        and we replace the record ID == 1 with campaign_id
        (More like hardcoded to maintain a single style of final records).
        """
        campaign_id: str = kwargs["campaign_id"]

        data: dict[str, Any] = response.json().get("data", {})
        raw_list: list[dict[str, str]] | dict[str, str] = data.get("list")
        records: list[dict[str, str]] = (
            raw_list
            if isinstance(raw_list, list)
            else [raw_list]
        )

        key: str = self.group_by_field or "id"
        for record in records:
            filter_value = record.pop("filter", None)
            record[key] = filter_value

            if key != "campaign_id":
                record["campaign_id"] = campaign_id

            if record["campaign_id"] == "1":
                record["campaign_id"] = campaign_id

            yield record

        print(f"Data for campaign '{campaign_id}' has been successfully downloaded.")
