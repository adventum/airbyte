from typing import Any, Iterable, Mapping, Optional

import requests
from airbyte_cdk import TokenAuthenticator

from .base import SmartisStream


class Groupings(SmartisStream):
    primary_key = "code"

    def __init__(
        self,
        authenticator: TokenAuthenticator | None = None,
        metrics: list[str] | None = None,
    ):
        super().__init__(authenticator)
        self.metrics = metrics

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "reports/getGroupings"

    def request_body_json(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        params = {"filters": {"is_system": False}}
        if self.metrics:
            params["metrics"] = ";".join(self.metrics)
        return params

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        if self.metrics:  # Uses different schemas for some unknown reason
            yield from response.json()["groupings"]
        else:
            yield from response.json()["groupings"].values()
