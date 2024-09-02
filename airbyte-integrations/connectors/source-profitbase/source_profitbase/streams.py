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

    def get_data(self, offset: int = 99, *args, **kwargs) -> dict:

        url: str = f"{self.url_base()}/{self.path()}"
        headers: dict = {
            "Content-Type": "application/json"
        }
        request_params: dict = {
            "access_token": self.auth_token,
            "full": True,
            "isArchive": False,
            "offset": offset
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

