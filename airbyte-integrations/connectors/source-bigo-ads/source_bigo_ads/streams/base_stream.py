from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import requests
from airbyte_cdk.sources.streams.http import HttpStream
from ..auth import HeadersAuthenticator


class BigoAdsStream(HttpStream, ABC):
    url_base = "https://ads.bigo.sg/api/"

    def __init__(
        self,
        authenticator: HeadersAuthenticator,
    ):
        super().__init__(authenticator=authenticator)
        self._authenticator = authenticator

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        return None

    # def request_headers(
    #     self,
    #     stream_state: Optional[Mapping[str, Any]],
    #     stream_slice: Optional[Mapping[str, Any]] = None,
    #     next_page_token: Optional[Mapping[str, Any]] = None,
    # ) -> Mapping[str, Any]:
    #     return self._authenticator.headers

    @abstractmethod
    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]: ...

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
