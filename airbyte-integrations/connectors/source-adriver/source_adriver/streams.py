#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

import xml.etree.ElementTree as ET
from abc import ABC
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import pendulum
import requests
from airbyte_cdk.sources.streams.http import HttpStream


class AdriverStream(HttpStream, ABC):
    url_base = "https://api.adriver.ru/"

    @property
    def state(self) -> MutableMapping[str, Any]:
        """Get connector state (default from HttpStream)"""
        cursor = self.get_cursor()
        if cursor:
            return cursor.get_stream_state()  # type: ignore
        return self._state

    @state.setter
    def state(self, value: MutableMapping[str, Any]) -> None:
        """Set empty state as in old connectors"""
        value = {}
        cursor = self.get_cursor()
        if cursor:
            cursor.set_initial_state(value)
        self._state = value

    def __init__(
        self,
        user_id: str,
        token: str,
        objects_ids: list[int],
        start_date: pendulum.Date,
        end_date: pendulum.Date,
    ) -> None:
        # Adriver uses custom auth
        super().__init__(authenticator=None)
        self.user_id = user_id
        self.token = token
        self.objects_ids = objects_ids
        self.start_date = start_date
        self.end_date = end_date

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        # No pagination is supported
        return None

    def request_headers(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        headers = {
            "Content-Type": "application/atom+xml",
            "X-Auth-UserID": self.user_id,
            "X-Auth-Passwd": self.token,
        }
        return headers

    def stream_slices(self, **kwargs) -> Iterable[Optional[Mapping[str, Any]]]:
        for object_id in self.objects_ids:
            yield {"object_id": object_id}

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        return {}

    def parse_response(
        self,
        response: requests.Response,
        stream_slice: Mapping[str, Any] = None,
        **kwargs,
    ) -> Iterable[Mapping]:
        object_id = stream_slice["object_id"]
        # 1. Parse XML
        root = ET.fromstring(response.text)

        # 2. Namespaces
        NS = {
            "atom": "http://www.w3.org/2005/Atom",
            "adr": "http://adriver.ru/ns/restapi/atom",
        }

        # 3. Find <adr:item> inside <adr:stat>
        items = root.findall(
            ".//atom:content/adr:statUniqueObject/adr:stat/adr:item", NS
        )

        # 4. Parse rows
        for it in items:
            row = {}
            for child in it:
                # Get just name from tags
                tag = child.tag.split("}", 1)[1]
                row[tag] = int(child.text) if tag != "date" else child.text

            # Filter by date range
            parsed_date = pendulum.parse(row["date"])
            if self.start_date <= parsed_date <= self.end_date:
                yield row | {"object_id": object_id}


class Ads(AdriverStream):
    primary_key = "date"

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        object_id = stream_slice["object_id"]
        return f"/stat/ads/{object_id}/unique"


class Banners(AdriverStream):
    primary_key = "date"

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        object_id = stream_slice["object_id"]
        return f"/stat/banners/{object_id}/unique"
