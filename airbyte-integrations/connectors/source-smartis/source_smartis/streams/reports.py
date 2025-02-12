from typing import Any, Iterable, Mapping, Optional

import pendulum
import requests
from airbyte_cdk import TokenAuthenticator

from .base import SmartisStream


class Reports(SmartisStream):
    primary_key = None
    datetime_format = "YYYY-MM-DD HH:mm:ss"

    def __init__(
        self,
        authenticator: TokenAuthenticator | None = None,
        project: str | None = None,
        metrics: list[str] | None = None,
        date_from: pendulum.DateTime | None = None,
        date_to: pendulum.DateTime | None = None,
        group_by: str | None = None,
        top_count: int = 10000,
    ):
        super().__init__(authenticator=authenticator)
        self.project = project
        self.metrics = metrics
        self.date_from = date_from
        self.date_to = date_to
        self.group_by = group_by
        self.top_count = top_count
        self._auth_copy = authenticator

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "reports/getReport"

    def request_body_json(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        return {
            "project": self.project,
            "metrics": ";".join(self.metrics),
            "datetimeFrom": self.date_from.format(self.datetime_format),
            "datetimeTo": self.date_to.format(self.datetime_format),
            "groupBy": self.group_by,
            "topCount": self.top_count,
            "type": "aggregated",
        }

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        yield response.json()["reports"]
