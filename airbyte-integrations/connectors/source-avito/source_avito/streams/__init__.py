from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import requests
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator


class AvitoStream(HttpStream, ABC):
    url_base = "https://api.avito.ru/"

    def __init__(self, authenticator: TokenAuthenticator):
        super().__init__(authenticator)

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        return {}

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        yield {}

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    @classmethod
    @abstractmethod
    def check_config(cls, config: Mapping[str, Any]) -> tuple[bool, str]:
        ...
