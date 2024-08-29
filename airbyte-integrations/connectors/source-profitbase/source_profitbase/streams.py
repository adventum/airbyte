import logging
import sys
from abc import ABC
from typing import Any, Generator, Iterable, Mapping, MutableMapping, Optional

import requests
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.utils.transform import TransformConfig, TypeTransformer


class ProfitBaseStream(HttpStream, ABC):
    max_retries = 8
    transformer: TypeTransformer = TypeTransformer(config=TransformConfig.DefaultSchemaNormalization)

    def __init__(self, auth_token: str, account_number: str | None = None):
        super().__init__(authenticator=None)
        self.auth_token = auth_token
        self.account_number = account_number

    def get_url_base(self) -> str:
        return f"https://pb{self.account_number}.profitbase.ru/api/v4/json/"


class Houses(ProfitBaseStream, ABC):
    def path(self, *args, **kwargs) -> str:
        return "house"

    def get_data(self, *args, **kwargs):
        url = f"{self.get_url_base()}/{self.path()}"
        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
