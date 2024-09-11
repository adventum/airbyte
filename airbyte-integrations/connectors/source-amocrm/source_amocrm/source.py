#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from abc import ABC
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple, Literal

import requests
from airbyte_cdk import TokenAuthenticator
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from requests.auth import AuthBase


class AmoCrmStream(HttpStream, ABC):

    def __init__(self, config: Mapping[str, Any], authenticator: Optional[AuthBase] = None):
        super().__init__(authenticator)
        self.subdomain = config["subdomain"]

    @property
    def url_base(self) -> str:
        return f"https://{self.subdomain}.amocrm.ru/api/"


class Contacts(AmoCrmStream):
    primary_key = "id"

    def __init__(self, config: Mapping[str, Any], authenticator: Optional[AuthBase] = None):
        super().__init__(config, authenticator)
        self._with: str = config["with"]
        self._page: int = 1
        self._limit: int = 250
        self._query: int | str | None = config.get("query")
        self._filter: dict[str, any] | None = None
        self._order_direction: Literal["asc", "desc"] = "asc"
        self._order_field: Literal["updated_at", "id"] = "id"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        return "v4/contacts"

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return {"page_number": self._page}

    def request_headers(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        return {
            "Authorization": f"Bearer {self.authenticator.token}",  # TODO
            "Content-Type": "application/hal+json",
        }

    def request_params(
        self, stream_state: Mapping[str, Any], stream_slice: Mapping[str, any] = None, next_page_token: Mapping[str, Any] = None
    ) -> MutableMapping[str, Any]:
        return {
            "with": self._with,
            "page": next_page_token["page_number"],
            "limit": self._limit,
            "query": self._query,
            "filter": self._filter,
            f"order[{self._order_direction}]": self._order_field,
        }

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        response_json: dict[str, any] = response.json()
        self._page = response_json["_page"] + 1
        yield from response_json["_embedded"]["contacts"]


class SourceAmocrm(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        """
        TODO: Implement a connection check to validate that the user-provided config can be used to connect to the underlying API

        See https://github.com/airbytehq/airbyte/blob/master/airbyte-integrations/connectors/source-stripe/source_stripe/source.py#L232
        for an example.

        :param config:  the user-input config object conforming to the connector's spec.yaml
        :param logger:  logger object
        :return Tuple[bool, any]: (True, None) if the input config can be used to connect to the API successfully, (False, error) otherwise.
        """
        return True, None

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        """
        TODO: Replace the streams below with your own streams.

        :param config: A Mapping of the user input configuration as defined in the connector spec.
        """
        # TODO remove the authenticator if not required.
        auth = TokenAuthenticator(token="api_key")  # Oauth2Authenticator is also available if you need oauth support
        return [Customers(authenticator=auth), Employees(authenticator=auth)]
