from typing import Any, Mapping

import requests
from airbyte_cdk.sources.streams.http.requests_native_auth import TokenAuthenticator


class ProfitbaseAuthenticator(TokenAuthenticator):
    """
    Here is authentication via api key
    We make a requiest to auth endpoint with apikey,
    after that we get the access token
    """

    @property
    def auth_header(self) -> str:
        return self._auth_header

    @staticmethod
    def get_access_token(api_key, account_number):
        base_auth_url = f"https://pb{account_number}.profitbase.ru/api/v4/json/authentication"
        data = {
            "type": "api-app",
            "credentials": {
                "pb_api_key": str(api_key)
            }
        }
        headers = {
            "Content-Type": "application/json"
        }

        result = requests.post(
            url=base_auth_url,
            data=data,
            headers=headers
        )

        return result.json()["access_token"]

    @property
    def raw_token(self) -> str:
        return self._token

    @property
    def token(self) -> str:
        return f"{self.auth_header}: {self._auth_method} {self._token}"

    def __init__(
        self,
        account_number: str,
        api_key: str,
        auth_method: str = "Bearer",
        auth_header: str = "Authorization",
    ):
        self.account_number = account_number
        self.apikey = api_key
        self._auth_header = auth_header
        self._auth_method = auth_method
        self._token = self.get_access_token(api_key, account_number)
