#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from abc import ABC
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import pendulum
import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_protocol.models import SyncMode

from .auth import CredentialsCraftAuthenticator, AmoCrmAuthenticator
from .utils import parse_date_range, get_auth


class AmoCrmStream(HttpStream, ABC):
    response_data_field: str | None = None

    def __init__(
        self,
        authenticator: CredentialsCraftAuthenticator | AmoCrmAuthenticator,
        config: Mapping[str, Any],
        date_from: pendulum.Date,
        date_to: pendulum.Date,
    ):
        super().__init__(authenticator=None)
        self._authenticator = authenticator
        self._subdomain = config["subdomain"]
        self._limit: int = 250  # default for most AmoCrm urls
        self._query: int | str | None = None
        self._date_from: pendulum.Date = date_from
        self._date_to: pendulum.Date = date_to
        self._with: str = ""
        self._custom_filters: list[str] = []

    @property
    def url_base(self) -> str:
        return f"https://{self._subdomain}.amocrm.ru/api/"

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
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        page: int = next_page_token["page_number"] if next_page_token else 1

        params: dict[str, Any] = {
            "page": page,
            "limit": self._limit,
            "order[id]": "asc",
        }
        if self._with:
            params["with"] = self._with
        if self._query:
            params["query"] = self._query

        # Add custom filters
        if self._custom_filters:
            for custom_filter in self._custom_filters:
                field, value = custom_filter.split("=")
                params[field] = value

        # Add created date filter
        # Loading data that was created or updated in this period
        # Created_at >= updated_at
        params["filter[updated_at][from]"] = pendulum.DateTime(
            year=self._date_from.year,
            month=self._date_from.month,
            day=self._date_from.day,
            hour=0,
            minute=0,
            second=0,
        ).timestamp()
        params["filter[created_at][to]"] = pendulum.DateTime(
            year=self._date_to.year,
            month=self._date_to.month,
            day=self._date_to.day,
            hour=23,
            minute=59,
            second=59,
        ).timestamp()

        return params

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        if len(response.json()["_embedded"][self.response_data_field]) < self._limit:
            return None
        return {"page_number": response.json()["_page"] + 1}

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        yield from response.json()["_embedded"][self.response_data_field]


class Contacts(AmoCrmStream):
    primary_key = "id"
    response_data_field = "contacts"

    def __init__(
        self,
        authenticator: CredentialsCraftAuthenticator | AmoCrmAuthenticator,
        config: Mapping[str, Any],
        date_from: pendulum.Date,
        date_to: pendulum.Date,
    ):
        super().__init__(authenticator, config, date_from, date_to)
        self._custom_filters = config.get("contacts_filters", [])
        # Add all possible with values to load full data
        self._with = ",".join(["catalog_elements", "leads", "customers"])
        self._query = config.get("contacts_query", None)

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "v4/contacts"


class Leads(AmoCrmStream):
    primary_key = "id"
    response_data_field = "leads"

    def __init__(
        self,
        authenticator: CredentialsCraftAuthenticator | AmoCrmAuthenticator,
        config: Mapping[str, Any],
        date_from: pendulum.Date,
        date_to: pendulum.Date,
    ):
        super().__init__(authenticator, config, date_from, date_to)
        self._custom_filters = config.get("leads_filters", [])
        self._with = ",".join(
            [
                "catalog_elements",
                "is_price_modified_by_robot",
                "loss_reason",
                "contacts",
                "source_id",
            ]
        )
        self._query = config.get("leads_query", None)

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "v4/leads"


class Events(AmoCrmStream):
    primary_key = "id"
    response_data_field = "events"

    def __init__(
        self,
        authenticator: CredentialsCraftAuthenticator | AmoCrmAuthenticator,
        config: Mapping[str, Any],
        date_from: pendulum.Date,
        date_to: pendulum.Date,
    ):
        super().__init__(authenticator, config, date_from, date_to)
        self._custom_filters = config.get("events_filters", [])

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "v4/events"

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        params: MutableMapping[str, Any] = super().request_params(
            stream_state, stream_slice, next_page_token
        )

        # Events do not support updated_at
        params["filter[created_at][from]"] = params["filter[updated_at][from]"]
        del params["filter[updated_at][from]"]

        return params


class Pipelines(AmoCrmStream):
    primary_key = "id"
    response_data_field = "pipelines"

    def __init__(
        self,
        authenticator: CredentialsCraftAuthenticator | AmoCrmAuthenticator,
        config: Mapping[str, Any],
        date_from: pendulum.Date,
        date_to: pendulum.Date,
    ):
        super().__init__(authenticator, config, date_from, date_to)

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "v4/leads/pipelines"

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        return {}  # No request args are supported


class Companies(AmoCrmStream):
    primary_key = "id"
    response_data_field = "companies"

    def __init__(
        self,
        authenticator: CredentialsCraftAuthenticator | AmoCrmAuthenticator,
        config: Mapping[str, Any],
        date_from: pendulum.Date,
        date_to: pendulum.Date,
    ):
        super().__init__(authenticator, config, date_from, date_to)
        self._custom_filters = config.get("companies_filters", [])
        # Add all possible with values to load full data
        self._with = ",".join(["catalog_elements", "leads", "customers", "contacts"])
        self._query = config.get("companies_query", None)

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "v4/companies"


class SourceAmoCrm(AbstractSource):
    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        # For future improvements
        return config

    def check_connection(self, logger, config) -> Tuple[bool, Any]:
        streams = self.streams(config)  # Check data correctness for all streams
        for stream in streams:
            stream._limit = 1  # Decrease amount of loaded values to speed up check
            try:
                next(stream.read_records(sync_mode=SyncMode.full_refresh))
            except Exception as ex:
                return False, ex

        return True, None

    def streams(self, config: Mapping[str, Any]) -> List[AmoCrmStream]:
        config = self.transform_config(config)
        auth = get_auth(config)
        date_from, date_to = parse_date_range(config)

        contacts_stream = Contacts(auth, config, date_from, date_to)
        leads_stream = Leads(auth, config, date_from, date_to)
        events_stream = Events(auth, config, date_from, date_to)
        pipelines_stream = Pipelines(auth, config, date_from, date_to)
        companies_stream = Companies(auth, config, date_from, date_to)

        return [contacts_stream, leads_stream, events_stream, pipelines_stream, companies_stream]
