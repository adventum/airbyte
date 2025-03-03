from typing import Optional

import requests

from source_sber_escrow.types import SberCredentials, IsSuccess, Message


class CredentialsCraftAuthenticator:
    def __init__(self, host: str, bearer_token: str, sber_token_id: int):
        self._host = host
        self._bearer_token = bearer_token
        self._sber_token_id = sber_token_id

    @property
    def url(self) -> str:
        return f"{self._host}/api/v1/token/sber/{self._sber_token_id}/json/"

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._bearer_token}"}

    def __call__(self) -> SberCredentials:
        token_resp = requests.get(self.url, headers=self.headers).json()
        token_data = token_resp["token"]
        return SberCredentials(**token_data)

    def check_connection(self) -> tuple[IsSuccess, Optional[Message]]:
        try:
            resp = requests.get(self.url, headers=self.headers, timeout=10)
            if (status_code := resp.status_code) == 200:
                return True, None
            return False, f"Status code: {status_code}. Body: {resp.text}."
        except Exception as e:
            return False, str(e)
