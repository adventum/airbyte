import base64
import uuid
from typing import Optional, Tuple, Dict

import requests

from source_sber_escrow.types import SberCredentials, IsSuccess, Message
from source_sber_escrow.utils import CertifiedRequests


class TokenAuthenticator:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scope: str,
        sber_client_cert: Optional[str] = None,
        sber_client_key: Optional[str] = None,
        sber_ca_chain: Optional[str] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.sber_client_cert = sber_client_cert
        self.sber_client_key = sber_client_key
        self.sber_ca_chain = sber_ca_chain

        self._url = "https://mc.api.sberbank.ru/prod/tokens/v3/oauth"
        self._certified_request = CertifiedRequests(client_cert=sber_client_cert, client_key=sber_client_key, ca_chain=sber_ca_chain)

    def __call__(self) -> SberCredentials:
        rquid = uuid.uuid4().hex.upper()

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        auth_header = f"Basic {encoded_credentials}"

        headers = {
            "accept": "application/json",
            "authorization": auth_header,
            "content-type": "application/x-www-form-urlencoded",
            "rquid": rquid,
        }

        data = {
            "grant_type": "client_credentials",
            "scope": self.scope,
        }

        response = self._certified_request.post(self._url, headers=headers, data=data)
        response.raise_for_status()

        token_data = response.json()
        return SberCredentials(
            access_token=token_data["access_token"],
            client_id=self.client_id,
            client_cert=self.sber_client_cert,
            client_key=self.sber_client_key,
            ca_chain=self.sber_ca_chain,
        )

    def check_connection(self) -> Tuple[IsSuccess, Optional[Message]]:
        try:
            self()
            return True, None
        except Exception as e:
            return False, str(e)


class CredentialsCraftAuthenticator:
    def __init__(self, host: str, bearer_token: str, token_id: int):
        self._host = host
        self._bearer_token = bearer_token
        self._token_id = token_id

    @property
    def url(self) -> str:
        return f"{self._host}/api/v1/token/static/{self._token_id}/json/"

    @property
    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._bearer_token}"}

    def __call__(self) -> SberCredentials:
        token_resp = requests.get(self.url, headers=self.headers).json()
        token_data = token_resp["token"]["token_data"]
        authenticator = TokenAuthenticator(
            client_id=token_data["client_id"],
            client_secret=token_data["client_secret"],
            scope=token_data["scope"],
            sber_client_cert=token_data.get("sber_client_cert"),
            sber_client_key=token_data.get("sber_client_key"),
            sber_ca_chain=token_data.get("sber_ca_chain"),
        )
        return authenticator()

    def check_connection(self) -> Tuple[IsSuccess, Optional[Message]]:
        try:
            self()
            return True, None
        except Exception as e:
            return False, str(e)
