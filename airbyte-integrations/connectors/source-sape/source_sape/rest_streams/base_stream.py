from abc import ABC
from typing import Optional, Mapping, Any

import pendulum
import requests
from airbyte_cdk import HttpStream, TokenAuthenticator


class SapeRestStream(HttpStream, ABC):
    url_base = "https://traffic.sape.ru/api/v2/"

    def __init__(
        self,
        authenticator: TokenAuthenticator,
        start_date: pendulum.Date,
        end_date: pendulum.Date,
    ):
        super().__init__(authenticator)
        self.start_date = start_date
        self.end_date = end_date
        self._authenticator = authenticator

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        return None
