from typing import Any, Iterable, Mapping

import requests

from .base import SmartisStream


class Attributions(SmartisStream):
    primary_key = "id"

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "reports/getModelAttributions"

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        yield from response.json()["modelAttributions"].values()
