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
    def get_access_token(api_key, account_number) -> str:
        base_auth_url: str = f"https://pb{account_number}.profitbase.ru/api/v4/json/authentication"
        data: dict[Any, Any] = {
            "type": "api-app",
            "credentials": {
                "pb_api_key": str(api_key)
            }
        }
        headers: dict[str, Any] = {
            "Content-Type": "application/json"
        }

        result = requests.post(
            url=base_auth_url,
            json=data,
            headers=headers
        )

        response_json = result.json()
        return response_json.get("access_token")

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
        self.account_number: str = account_number
        self.api_key: str = api_key
        self._auth_header: str = auth_header
        self._auth_method: str = auth_method
        self._token: str = self.get_access_token(api_key, account_number)
