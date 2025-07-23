from .base import FraudscoreStream

from abc import ABC
import json
from typing import (
    Any,
    Iterable,
    Mapping,
    Optional,
    Literal,
)

import pendulum
import requests


EventType = Literal["install", "click", "impression", "custom"]


class EventStreamBase(FraudscoreStream, ABC):
    primary_key = None

    def __init__(
        self,
        channel: str,
        user_key: str,
        event: EventType,
        time_from: pendulum.DateTime,
        time_to: pendulum.DateTime,
    ) -> None:
        super().__init__(authenticator=None)
        self._channel = channel
        self._user_key = user_key
        self._event = event
        self._time_from = time_from
        self._time_to = time_to
        self._current_page: int = 1

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        count = sum(1 for line in response.text.split("\n") if line)
        if count < self.page_size:
            return None
        self._current_page += 1
        return {"current_page": self._current_page}

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> dict[str, Any]:
        # Also you can add sorted, but then you must enforce users
        # to pass some params as fields to be filtered by
        params: dict[str, Any] = {
            "key": self._user_key,
            "filter": json.dumps(
                [
                    "AND",
                    ["date_ge", self._time_from.to_date_string()],
                    ["date_le", self._time_to.to_date_string()],
                ]
            ),
            "page": self._current_page,  # The same as in next_page_token
            "page_size": self.page_size,
            "tz": "UTC",
        }
        return params

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        yield from map(json.loads, response.iter_lines())
