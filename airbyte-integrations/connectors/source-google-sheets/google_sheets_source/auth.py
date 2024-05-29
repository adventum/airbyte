from typing import Any, Mapping

import requests
from airbyte_cdk.sources.streams.http.requests_native_auth import TokenAuthenticator

#
# class CredentialsCraftAuthenticator(TokenAuthenticator):
#     def __init__(
#         self,
#         credentials_craft_host: str,
#         credentials_craft_token: str,
#         credentials_craft_token_id: int,
#         additional_headers: dict = {},
#     ):
#         self._cc_host = credentials_craft_host.rstrip("/")
#         self._cc_token = credentials_craft_token
#         self._cc_token_id = credentials_craft_token_id
#         self._token = None
#         self.additional_headers = additional_headers
#
#     @property
#     def _url(self) -> str:
#         return f"{self._cc_host}/api/v1/token/static/{self._cc_token_id}/"
#
#     @property
#     def token(self) -> str:
#         response = requests.get(
#             self._url,
#             headers={"Authorization": f"Bearer {self._cc_token}"},
#         )
#         data: dict[str, Any] = response.json()
#         return data["token_data"]["access_token"]
#
#     def get_auth_header(self) -> Mapping[str, Any]:
#         super().__init__(self._token, "Bearer", "Authorization")
#         if self.auth_header:
#             auth_header = {self.auth_header: f"{self._auth_method} {self.token}"}
#         else:
#             auth_header = {}
#         if self.additional_headers:
#             auth_header.update(self.additional_headers)
#         return auth_header
#
#     def check_connection(self) -> tuple[bool, str]:
#         try:
#             requests.get(self._cc_host, timeout=15)
#         except:
#             return False, f"Connection to {self._cc_host} timed out"
#
#         data: dict[str, Any] = requests.get(
#             self._url,
#             headers={"Authorization": f"Bearer {self._cc_token}"},
#         ).json()
#         if data.get("error"):
#             return False, f"CredentialsCraft error: {data.get('error')}"
#
#         return True, None


class CredentialsCraftAuthenticator(TokenAuthenticator):
    def __init__(
        self,
        credentials_craft_host: str,
        credentials_craft_token: str,
        credentials_craft_token_id: int,
        additional_headers: dict = {},
    ):
        self._cc_host = credentials_craft_host.rstrip("/")
        self._cc_token = credentials_craft_token
        self._cc_token_id = credentials_craft_token_id
        self._token = None
        self.additional_headers = additional_headers

    @property
    def _url(self) -> str:
        return f"{self._cc_host}/api/v1/token/static/{self._cc_token_id}/"

    @property
    def token(self) -> str:
        response = requests.get(
            self._url,
            headers={"Authorization": f"Bearer {self._cc_token}"},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        return data["token_data"]["credentials"]

    def get_auth_header(self) -> Mapping[str, Any]:
        super().__init__(self.token, "Bearer", "Authorization")
        auth_header = {self.auth_header: f"{self._auth_method} {self.token}"}
        if self.additional_headers:
            auth_header.update(self.additional_headers)
        return auth_header

    def check_connection(self) -> tuple[bool, str]:
        try:
            requests.get(self._cc_host, timeout=15)
        except Exception as e:
            return False, f"Connection to {self._cc_host} timed out: {e}"

        response = requests.get(
            self._url,
            headers={"Authorization": f"Bearer {self._cc_token}"},
        )
        if response.status_code != 200:
            return False, f"CredentialsCraft error: {response.text}"

        data: dict[str, Any] = response.json()
        if data.get("error"):
            return False, f"CredentialsCraft error: {data.get('error')}"

        return True, None
