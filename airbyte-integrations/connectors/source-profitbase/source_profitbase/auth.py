import requests
import json

from typing import Any, Mapping
from airbyte_cdk.sources.streams.http.requests_native_auth import TokenAuthenticator


class ProfitbaseAuthenticator(TokenAuthenticator):
    """
    Here is authentication via api key
    We make a requiest to auth endpoint with apikey,
    after that we get the access token
    """

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
    def token(self) -> str:
        return self._token

    @property
    def token_header(self) -> str:
        return f"{self.auth_header}: {self._auth_method} {self._token}"


class CredentialsCraftAuthenticator(TokenAuthenticator):
    def __init__(
        self,
        credentials_craft_host: str,
        credentials_craft_token: str,
        credentials_craft_token_id: int,
        account_number: str = None,
        additional_headers: dict = {}
    ):
        self._cc_host = credentials_craft_host.rstrip("/")
        self._cc_token = credentials_craft_token
        self._cc_token_id = credentials_craft_token_id
        self._token = None
        self.account_number: str = account_number
        self.additional_headers = additional_headers

    @property
    def _url(self) -> str:
        return f"{self._cc_host}/api/v1/token/static/{self._cc_token_id}/"

    @property
    def token(self) -> str:
        # Получение API-ключа с CredentialsCraft
        response = requests.get(
            self._url,
            headers={"Authorization": f"Bearer {self._cc_token}"},
        )
        data: dict[str, Any] = response.json()

        # После получения API-ключа, запрашиваем у Profitbase access_token
        api_key = data["token_data"]["access_token"]
        access_token = ProfitbaseAuthenticator.get_access_token(api_key, self.account_number)

        return access_token

    def get_auth_header(self) -> Mapping[str, Any]:
        super().__init__(self._token, "Bearer", "Authorization")
        if self.auth_header:
            auth_header = {self.auth_header: f"{self._auth_method} {self.token}"}
        else:
            auth_header = {}
        if self.additional_headers:
            auth_header.update(self.additional_headers)
        return auth_header

    def check_connection(self) -> tuple[bool, str]:
        try:
            requests.get(self._cc_host, timeout=15)
        except:
            return False, f"Connection to {self._cc_host} timed out"

        data: dict[str, Any] = requests.get(
            self._url,
            headers={"Authorization": f"Bearer {self._cc_token}"},
        ).json()
        if data.get("error"):
            return False, f"CredentialsCraft error: {data.get('error')}"

        return True, None


def get_authenticator(config: json):
    auth_type = config["credentials"]["auth_type"]

    # Авторизация через API-ключ
    if auth_type == "access_token_auth":
        api_key: str = config["credentials"]["access_token"]
        account_number: str = config["account_number"]
        authenticator: ProfitbaseAuthenticator = (
            ProfitbaseAuthenticator(api_key=api_key, account_number=account_number)
        )
        return authenticator

    if auth_type == "credentials_craft_auth":
        credentials_craft_host: str = config["credentials"]["credentials_craft_host"]
        credentials_craft_token: str = config["credentials"]["credentials_craft_token"]
        credentials_craft_token_id: int = config["credentials"]["credentials_craft_token_id"]
        account_number: str = config["account_number"]

        #additional_headers: dict = config["credentials"][""]
        authenticator: CredentialsCraftAuthenticator = CredentialsCraftAuthenticator(
            credentials_craft_host,
            credentials_craft_token,
            credentials_craft_token_id,
            account_number
        )
        return authenticator
