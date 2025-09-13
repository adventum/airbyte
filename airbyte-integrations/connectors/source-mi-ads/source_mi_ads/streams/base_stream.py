import uuid
from abc import ABC
import time
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import pendulum
import requests
from airbyte_cdk.sources.streams.http import HttpStream
from ..auth import MiAdsAuthenticator


class MiAdsStream(HttpStream, ABC):
    url_base = "https://global.e.mi.com/foreign/"

    def __init__(
        self,
        authenticator: MiAdsAuthenticator,
        time_from: pendulum.DateTime,
        time_to: pendulum.DateTime,
    ):
        super().__init__(authenticator)
        self._authenticator = authenticator
        self._time_from = time_from
        self._time_to = time_to

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        return None

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        return {}

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        yield {}

    def request_headers(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        """Mi ads requires cookies, however airbyte does not support cookies in direct way"""
        # all api requires the same cookies: https://global.e.mi.com/doc/reporting_api_guide.html#_1-interface-1
        cookies = {
            "access_token": self._authenticator.token,
            "timestamp": str(int(time.time() * 1000)),
            "uid": str(uuid.uuid4()),
        }
        cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        return {"Cookie": cookie_header}

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
