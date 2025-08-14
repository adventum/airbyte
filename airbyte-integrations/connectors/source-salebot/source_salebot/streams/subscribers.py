from typing import Optional, Mapping, Any, Iterable

import pendulum
import requests

from .base_stream import SalebotStream


class Subscribers(SalebotStream):
    page_size = 1000
    primary_key = "id"

    def __init__(
        self,
        api_key: str,
        time_from: pendulum.DateTime,
        time_to: pendulum.DateTime,
        group: str | None = None,
        tag: str | None = None,
        client_type: int | None = None,
    ) -> None:
        super().__init__(api_key, time_from, time_to)
        self._group = group
        self._tag = tag
        self._client_type = client_type
        # "чтобы получить следующую 1000 клиентов, нужно указывать параметр page значение 1."
        self._page_number = 0

    def path(self, *args, **kwargs) -> str:
        return self._api_key + "/subscribers"

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        if len(response.json()) < self.page_size:
            return None
        self._page_number += 1
        # Value actually is not user
        return {"page_number": self._page_number}

    def request_params(
        self, next_page_token: Optional[Mapping[str, Any]] = None, *args, **kwargs
    ) -> Optional[Mapping[str, Any]]:
        data = {
            "date_from": self._time_from.timestamp(),
            "date_to": self._time_to.timestamp(),
            # "page": self._page_number,
        }
        if self._group:
            data["group"] = self._group
        if self._tag:
            data["tag"] = self._tag
        if self._client_type:
            data["client_type"] = self._client_type

        self.logger.info("PAGE %s", self._page_number)
        return data

    def parse_response(
        self, response: requests.Response, *args, **kwargs
    ) -> Iterable[Mapping[str, Any]]:
        yield from response.json()
