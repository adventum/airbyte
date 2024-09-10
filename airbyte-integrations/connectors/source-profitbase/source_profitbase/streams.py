from abc import ABC
from typing import Any, Mapping, Optional

import requests
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.utils.transform import TransformConfig, TypeTransformer


class ProfitBaseStream(HttpStream, ABC):
    max_retries = 8
    transformer: TypeTransformer = TypeTransformer(config=TransformConfig.DefaultSchemaNormalization)

    def __init__(self, auth_token: str, account_number: Optional[str] = None):
        super().__init__(authenticator=None)
        self.auth_token = auth_token
        self.account_number = account_number

    def url_base(self) -> str:
        return f"https://pb{self.account_number}.profitbase.ru/api/v4/json"

    def get_data(
            self,
            offset: int = 99,
            crm: str = "amo",
            property_ids: list = None,
            house_ids: list = None,
            date_from: str = None,
            date_to: str = None,
            deal_id: str = None,
            *args,
            **kwargs
        ) -> dict:

        url: str = f"{self.url_base()}/{self.path()}"
        headers: dict = {
            "Content-Type": "application/json"
        }
        request_params: dict = {
            "access_token": self.auth_token,
            "full": True,
            "isArchive": False,
            "offset": offset,
            "crm": crm
        }

        response = requests.get(url, headers=headers, params=request_params)
        response.raise_for_status()
        return response.json()


class House(ProfitBaseStream, ABC):
    primary_key = "id"

    def path(self, *args, **kwargs) -> str:
        return "house"

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def parse_response(
        self,
        response: requests.Response,
        *,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> None: #Iterable[Mapping[str, Any]]:
        return None


class Projects(ProfitBaseStream, ABC):
    primary_key: str = "id"

    def path(self, *args, **kwargs) -> str:
        return "projects"

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def parse_response(
        self,
        response: requests.Response,
        *,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> None: #Iterable[Mapping[str, Any]]:
        return None


class Property(ProfitBaseStream, ABC):
    primary_key: str = "id"

    def path(self, *args, **kwargs) -> str:
        return "property"

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def parse_response(
        self,
        response: requests.Response,
        *,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> None: #Iterable[Mapping[str, Any]]:
        return None


class Statuses(ProfitBaseStream, ABC):
    primary_key: str = "id"

    def path(self, *args, **kwargs) -> str:
        return "custom-status/list"

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def parse_response(
        self,
        response: requests.Response,
        *,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> None: #Iterable[Mapping[str, Any]]:
        return None


class History(ProfitBaseStream, ABC):
    primary_key: str = "dealId"

    def path(self, *args, **kwargs) -> str:
        return "history"

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def parse_response(
        self,
        response: requests.Response,
        *,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> None: #Iterable[Mapping[str, Any]]:
        return None

    def get_data(
            self,
            offset: int = 99,
            property_ids: list = None,
            house_ids: list = None,
            date_from: str = None,
            date_to: str = None,
            deal_id: str = None,
            *args,
            **kwargs
        ) -> dict:

        url: str = f"{self.url_base()}/{self.path()}"
        headers: dict = {
            "Content-Type": "application/json"
        }
        request_params: dict = {
            "access_token": self.auth_token,
            "isArchive": False,
            "offset": offset,
        }

        data: dict = {
            "property_ids": property_ids,
            "house_ids": house_ids,
            "from": date_from,
            "to": date_to,
            "dealId": deal_id
        }
        response = requests.post(url, headers=headers, params=request_params, data=data)
        response.raise_for_status()
        return response.json()
