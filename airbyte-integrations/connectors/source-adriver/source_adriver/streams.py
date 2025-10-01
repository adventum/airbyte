#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

import xml.etree.ElementTree as ET
from abc import ABC
from functools import lru_cache
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import pendulum
import requests
from airbyte_cdk.sources.streams.http import HttpStream
from .utils import get_auth, url_base as _url_base


class AdriverStream(HttpStream, ABC):
    url_base = _url_base

    # XML Namespaces
    NS = {
        "atom": "http://www.w3.org/2005/Atom",
        "adr": "http://adriver.ru/ns/restapi/atom",
    }

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
        config: Mapping[str, Any],
        user_id: str,
        token: str,
        start_date: pendulum.Date,
        end_date: pendulum.Date,
        objects_ids: list[int] | None = None,
        load_all: bool = False,
    ) -> None:
        # Adriver uses custom auth
        super().__init__(authenticator=None)
        self.config = config
        self.user_id = user_id
        self.token = token
        self.objects_ids = objects_ids
        self.start_date = start_date
        self.end_date = end_date
        self.load_all = load_all

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

    @staticmethod
    def _extract_numeric_id(raw_identifier: str | None, entity: str) -> int:
        if not raw_identifier or not raw_identifier.strip():
            raise ValueError(
                f"Received empty identifier for {entity}. Raw value: {raw_identifier!r}"
            )
        candidate = raw_identifier.strip().rsplit("/", 1)[-1]
        candidate = candidate.rsplit(":", 1)[-1]
        if not candidate.isdigit():
            raise ValueError(
                f"Failed to extract numeric id from {entity} identifier '{raw_identifier}'. Expected trailing digits."
            )
        return int(candidate)

    def _fetch_next_page(
        self,
        stream_slice: Optional[Mapping[str, Any]] = None,
        stream_state: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> tuple[requests.PreparedRequest, requests.Response]:
        # Adriver token tends to expire while processing data, so we need to renew it
        request, response = None, None
        attempts: int = 0
        while attempts < 3:
            request, response = super()._fetch_next_page(
                stream_slice, stream_state, next_page_token
            )
            if response.status_code != 401:
                break
            self.user_id, self.token = get_auth(self.config)
            attempts += 1
        return request, response

    def stream_slices(self, **kwargs) -> Iterable[Optional[Mapping[str, Any]]]:
        for object_id in self.objects_ids:
            self.logger.info(f"Yield obj: {object_id}")
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
        self.logger.info(f"Parsing obj: {object_id}")
        # 1. Parse XML
        root = ET.fromstring(response.text)

        # 3. Find <adr:item> inside <adr:stat>
        items = root.findall(
            ".//atom:content/adr:statUniqueObject/adr:stat/adr:item", self.NS
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

    @lru_cache()
    def get_ads_ids(self) -> list[int]:
        ads_ids = []
        for path in ("ads", "ads/delegated", "net_ads", "net_ads/delegated"):
            # Make request
            attempts: int = 0
            req = None
            while attempts < 3:
                req = requests.get(
                    f"{self.url_base}{path}",
                    headers=self.request_headers(None),
                    params={"user_id": self.user_id},
                )
                if req.status_code != 401:
                    break
                self.user_id, self.token = get_auth(self.config)
                attempts += 1

            # Parse request
            root = ET.fromstring(req.text)
            for entry in root.findall("atom:entry", self.NS):
                ad_element = entry.find("atom:id", self.NS)
                raw_ad_id = ad_element.text if ad_element is not None else None
                ad_id = self._extract_numeric_id(raw_ad_id, "ad")
                ads_ids.append(ad_id)
        return ads_ids

    def stream_slices(self, **kwargs) -> Iterable[Optional[Mapping[str, Any]]]:
        if self.load_all:
            # Load all with ads ids
            for ad_id in self.get_ads_ids():
                self.logger.info(f"Yield ad: {ad_id}")
                yield {"object_id": ad_id}
        else:
            # Load by manually stated ids
            yield from super().stream_slices(**kwargs)


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

    def __init__(
        self,
        config: Mapping[str, Any],
        user_id: str,
        token: str,
        start_date: pendulum.Date,
        end_date: pendulum.Date,
        objects_ids: list[int] | None = None,
        load_all: bool = False,
        ads_stream: Ads | None = None,
    ) -> None:
        super().__init__(
            config, user_id, token, start_date, end_date, objects_ids, load_all
        )
        self.ads_stream = ads_stream

    def load_banners_ids(self) -> Iterable[int]:
        """Get banners ids as iterator"""
        ads_ids = self.ads_stream.get_ads_ids()
        for ad_id in ads_ids:
            # Make request
            attempts: int = 0
            req = None
            while attempts < 3:
                req = requests.get(
                    f"{self.url_base}/adplacements",
                    headers=self.request_headers(None),
                    params={"user_id": self.user_id, "ad_id": ad_id},
                )
                if req.status_code != 401:
                    break
                self.user_id, self.token = get_auth(self.config)
                attempts += 1

            # Parse data
            root = ET.fromstring(req.text)
            for entry in root.findall("atom:entry", self.NS):
                banners = entry.find(
                    "atom:content/adr:adPlacement/adr:banners", self.NS
                )
                if banners is None:
                    continue
                for href in banners.findall("adr:href", self.NS):
                    if href.text and href.text.strip():
                        banner_id = self._extract_numeric_id(href.text, "banner")
                        yield banner_id

    def stream_slices(self, **kwargs) -> Iterable[Optional[Mapping[str, Any]]]:
        if self.load_all:
            # Load all with ads ids
            for banner_id in self.load_banners_ids():
                self.logger.info(f"Yield banner: {banner_id}")
                yield {"object_id": banner_id}
        else:
            # Load by manually stated ids
            yield from super().stream_slices(**kwargs)
