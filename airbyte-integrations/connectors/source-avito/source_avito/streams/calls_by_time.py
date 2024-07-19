from typing import Any, Iterable, Mapping, Optional

import pendulum
import requests
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator
from . import AvitoStream


class CallsByTime(AvitoStream):
    http_method = "POST"
    primary_key = "id"
    records_batch_size = 50
    offset = 0

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "cpa/v2/callsByTime"

    def __init__(
        self,
        authenticator: TokenAuthenticator,
        time_from: pendulum.datetime,
        time_to: pendulum.datetime,
    ):
        super().__init__(authenticator)
        self.time_from: pendulum.datetime = time_from
        self.time_to: pendulum.date = time_to

    @classmethod
    def check_config(cls, config: Mapping[str, Any]) -> tuple[bool, str]:
        # Needs nothing except token and datetime checked in base config check
        return True, ""

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        response_json: dict[str, any] = response.json()
        calls: list[dict[str, any]] = response_json["result"]["calls"]
        if len(calls) < self.records_batch_size:
            return None  # Finished all

        self.offset += self.records_batch_size
        return {"offset": self.offset}

    def request_body_json(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        """Get request json"""
        offset: int = next_page_token["offset"] if next_page_token else 0

        data: dict[str, any] = {
            "limit": self.records_batch_size,
            "offset": offset,
            "dateTimeFrom": self.time_from.to_rfc3339_string(),
        }
        return data

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        response_json: dict[str, any] = response.json()
        if "error" in response_json:
            error_text: str = response_json["error"]["message"]
            self.logger.info(f"Request failed: {error_text}")
            raise RuntimeError("Failed to fetch data")

        if "calls" not in response_json["result"]:
            raise ValueError(response_json, response.request.body)

        for call in response_json["result"]["calls"]:
            if pendulum.parse(call["startTime"]).date() <= self.time_to.date():
                yield call
