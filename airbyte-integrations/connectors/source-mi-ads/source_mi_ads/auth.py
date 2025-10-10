from typing import Mapping, Any

import pendulum
from airbyte_cdk.sources.streams.http.requests_native_auth import TokenAuthenticator
import requests


class MiAdsAuthenticator(TokenAuthenticator):
    base_url = "https://global.e.mi.com/foreign/token/"

    def __init__(self, app_id: str, app_key: str):
        self._app_id: str = app_id
        self._app_key: str = app_key
        self._access_token: str | None = None
        self._access_token_expire_at: pendulum.DateTime | None = None
        self._refresh_token: str | None = None
        self._refresh_token_expire_at: pendulum.DateTime | None = None

    def _get_tokens(self) -> None:
        """Get all tokens with app id and app key"""
        # https://global.e.mi.com/doc/reporting_api_guide.html#_1-create-token
        r = requests.post(
            self.base_url + "createToken",
            json={"appId": self._app_id, "appKey": self._app_key},
        )
        r.raise_for_status()
        data = r.json()
        self._access_token = data["result"]["accessToken"]
        self._access_token_expire_at = pendulum.parse(
            data["result"]["expireDate"]
        ).in_tz("UTC")
        self._refresh_token = data["result"]["refreshToken"]
        self._refresh_token_expire_at = pendulum.parse(
            data["result"]["refreshExpireDate"]
        ).in_tz("UTC")

    def _update_access_token(self) -> None:
        """Update access token with refresh token"""
        # https://global.e.mi.com/doc/reporting_api_guide.html#_2-update-token
        r = requests.post(
            self.base_url + "refreshToken", json={"refreshToken": self._refresh_token}
        )
        r.raise_for_status()
        data = r.json()
        self._access_token = data["result"]["accessToken"]
        self._access_token_expire_at = pendulum.parse(
            data["result"]["expireDate"]
        ).in_tz("UTC")
        self._refresh_token = data["result"]["refreshToken"]
        self._refresh_token_expire_at = pendulum.parse(
            data["result"]["refreshExpireDate"]
        ).in_tz("UTC")

    @property
    def token(self) -> str:
        # Mi ads uses utc datetimes
        if not self._access_token or pendulum.now("UTC") > self._access_token_expire_at:
            self._get_tokens()
        elif pendulum.now("UTC") > self._access_token_expire_at:
            self._update_access_token()
        return self._access_token

    def get_auth_header(self) -> Mapping[str, Any]:
        # Cookies auth is used, this part is just for airbyte internal functions
        return {}
