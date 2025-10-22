from functools import lru_cache

import pendulum
import requests
from airbyte_cdk import ResourceSchemaLoader, package_name_from_class

from .base_stream import BigoAdsStream
from typing import Any, Mapping, Optional, Iterable
from ..auth import HeadersAuthenticator


class CampaignStream(BigoAdsStream):
    primary_key = None
    page_size = 100
    http_method = "POST"

    def __init__(
        self,
        authenticator: HeadersAuthenticator,
        indicators: list[str],
        date_from: pendulum.Date,
        date_to: pendulum.Date,
        campaign_codes: list[str] | None = None,
    ):
        super().__init__(authenticator)
        self._indicators = indicators
        self._date_from = date_from
        self._date_to = date_to
        self._campaign_codes = campaign_codes
        self._current_page = 1

    def path(self, *args, **kwargs) -> str:
        return "dsp/report/campaign_list"

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        if len(response.json()["result"]["list"]) < self.page_size:
            return None
        self._current_page += 1
        return {"page_number": self._current_page}

    def request_body_json(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        return {
            "startDate": self._date_from.isoformat(),
            "endDate": self._date_to.isoformat(),
            "indicators": self._indicators,
            "breakDowns": ["campaignCode"],
            "aggregateType": 2,
            "pageSize": self.page_size,
            "pageNo": next_page_token["page_number"] if next_page_token else 1,
            "adCode": [],
            "adsetCode": [],
            "campaignCode": self._campaign_codes,
            "orderBy": "aggregateTime",
        }

    @lru_cache(maxsize=None)
    def get_json_schema(self) -> Mapping[str, Any]:
        schema = ResourceSchemaLoader(
            package_name_from_class(self.__class__)
        ).get_schema("campaign_stream")
        for indicator in self._indicators:
            schema["properties"][indicator] = {
                "type": ["null", "number", "float", "string"]
            }
        return schema

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        yield from response.json()["result"]["list"]
