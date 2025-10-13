#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from typing import Any, Iterable, Mapping, MutableMapping, Optional

import pendulum
import requests
from airbyte_cdk import TokenAuthenticator
from .base_stream import YandexRealtyStream


class Calls(YandexRealtyStream):
    primary_key = None
    page_size = 100

    def __init__(
        self,
        authenticator: TokenAuthenticator,
        date_from: pendulum.Date,
        date_to: pendulum.Date,
        client_id: str,
        agency_id: str | None = None,
    ):
        super().__init__(authenticator)
        self._date_from = date_from
        self._date_to = date_to
        self._client_id = client_id
        self._agency_id = agency_id
        self._page_num = 0

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "publicPartner/calls"

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        if self._page_num == response.json()["totalPages"]:
            return None
        else:
            self._page_num += 1
            # Actually it is not important what we return here
            # Other methods rely on self._page_num
            # Using next_page_token's dict is just less convenient
            return {"page_num": self._page_num}

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        data = {
            "clientId": self._client_id,
            "fromDate": self._date_from.to_date_string(),
            "toDate": self._date_to.to_date_string(),
            "pageNum": self._page_num,
            "pageSize": self.page_size,
        }
        if self._agency_id is not None:
            data["agencyId"] = self._agency_id
        return data

    def parse_response(
        self,
        response: requests.Response,
        *,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Iterable[Mapping[str, Any]]:
        yield from response.json()["calls"]
