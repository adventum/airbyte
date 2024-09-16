#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from abc import ABC
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple, Literal

import pendulum
import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from .auth import CredentialsCraftAuthenticator, AmoCrmAuthenticator


class AmoCrmStream(HttpStream, ABC):

    def __init__(self, config: Mapping[str, Any], authenticator: CredentialsCraftAuthenticator | AmoCrmAuthenticator):
        super().__init__(authenticator=None)
        self._authenticator = authenticator
        self.subdomain = config["subdomain"]

    @property
    def url_base(self) -> str:
        return f"https://{self.subdomain}.amocrm.ru/api/"


class Contacts(AmoCrmStream):
    primary_key = "id"

    def __init__(self, config: Mapping[str, Any], authenticator: CredentialsCraftAuthenticator | AmoCrmAuthenticator = None):
        super().__init__(config, authenticator)
        self._with: str = config.get("with")
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
        if len(response.json()["_embedded"]["contacts"]) < self._limit:
            return None
        return {"page_number": response.json()["_page"] + 1}

    def request_headers(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        return {
            "Authorization": f"Bearer {self._authenticator.token}",
            "Content-Type": "application/hal+json",
        }

    def request_params(
        self, stream_state: Mapping[str, Any], stream_slice: Mapping[str, any] = None, next_page_token: Mapping[str, Any] = None
    ) -> MutableMapping[str, Any]:
        page: int = next_page_token["page_number"] if next_page_token else 1

        params: dict[str, any] = {
            "page": page,
            "limit": self._limit,
        }
        if self._with:
            params["with"] = self._with
        if self._query:
            params["query"] = self._query
        if self._filter:
            params["filter"] = self._filter
        if self._order_field:
            params[f"order[{self._order_field}]"] = self._order_direction

        return params

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        yield from response.json()["_embedded"]["contacts"]


class SourceAmoCrm(AbstractSource):

    @staticmethod
    def transform_config_date_range(config: Mapping[str, Any]) -> Mapping[str, Any]:
        date_range: Mapping[str, Any] = config.get("date_range", {})
        date_range_type: str = date_range.get("date_range_type")

        time_from: Optional[pendulum.datetime] = None
        time_to: Optional[pendulum.datetime] = None

        # Meaning is date but storing time since later will use time
        today_date: pendulum.datetime = pendulum.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if date_range_type == "custom_date":
            time_from = pendulum.parse(date_range["date_from"])
            time_to = pendulum.parse(date_range["date_to"])
        elif date_range_type == "from_start_date_to_today":
            time_from = pendulum.parse(date_range["date_from"])
            if date_range.get("should_load_today"):
                time_to = today_date
            else:
                time_to = today_date.subtract(days=1)
        elif date_range_type == "last_n_days":
            time_from = today_date.subtract(days=date_range.get("last_days_count"))
            if date_range.get("should_load_today"):
                time_to = today_date
            else:
                time_to = today_date.subtract(days=1)

        config["time_from_transformed"], config["time_to_transformed"] = time_from, time_to
        return config

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config = SourceAmoCrm.transform_config_date_range(config)
        # For future improvements
        return config

    @staticmethod
    def get_auth(config: Mapping[str, Any]) -> CredentialsCraftAuthenticator | AmoCrmAuthenticator:
        if config["credentials"]["auth_type"] == "access_token_auth":
            return AmoCrmAuthenticator(token=config["credentials"]["access_token"])
        elif config["credentials"]["auth_type"] == "credentials_craft_auth":
            return CredentialsCraftAuthenticator(
                credentials_craft_host=config["credentials"]["credentials_craft_host"],
                credentials_craft_token=config["credentials"]["credentials_craft_token"],
                credentials_craft_token_id=config["credentials"]["credentials_craft_token_id"],
            )
        else:
            raise Exception("Invalid Auth type. Available: access_token_auth and credentials_craft_auth")

    def check_connection(self, logger, config) -> Tuple[bool, any]:
        return True, None

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        config = self.transform_config(config)
        auth = self.get_auth(config)
        contacts_stream = Contacts(config, auth)
        return [contacts_stream]
