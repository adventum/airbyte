#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

import logging
import requests

from requests import Response
from typing import Any, List, Mapping, Tuple

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_protocol.models import SyncMode

from .auth import CredentialsCraftAuthenticator
from .streams.report_statistics_stream import ReportStatistics
from .utils import get_config_date_range, base_headers

logger = logging.getLogger(__name__)


class SourceBetweenx(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, Any]:
        """
        We check the success of authorization in the BetweenX service
        """
        try:
            config = SourceBetweenx.transform_config(config)
            login, password = self.get_auth(config)
            token: str = SourceBetweenx.get_token(login, password)
            if token:
                return True, None
            else:
                return False, None
        except Exception as e:
            return False, e

    @staticmethod
    def get_auth(config: Mapping[str, Any]) -> tuple[str, str]:
        if config["credentials"]["auth_type"] == "login_password_auth":
            credentials = config["credentials"]
            return credentials["account_email"], credentials["account_password"]

        elif config["credentials"]["auth_type"] == "credentials_craft_auth":
             account_email, account_password = CredentialsCraftAuthenticator(
                credentials_craft_host=config["credentials"]["credentials_craft_host"],
                credentials_craft_token=config["credentials"][
                    "credentials_craft_token"
                ],
                credentials_craft_token_id=config["credentials"][
                    "credentials_craft_token_id"
                ],
            ).token
             return account_email, account_password

        else:
            raise Exception(
                "Invalid Auth type. Available: login_password_auth and credentials_craft_auth"
            )

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config["time_from_transformed"], config["time_to_transformed"] = (
            get_config_date_range(config)
        )
        return config

    @staticmethod
    def get_token(email: str, password: str) -> str:
        """
        BetweenX does not have a public API. First,
        we need to obtain an auth token through login/password authentication.

        Returns: token
        """
        # Get cookies
        token_response: Response = requests.post(
            url=f"https://api.betweendigital.com/system/auth/login",
            headers=base_headers,
            json={
                "lang":"ru-RU", "email": email, "password": password
            },
        )
        token_response.raise_for_status()

        token: str = token_response.json()["data"]["token"]
        return token

    def streams(self, config: Mapping[str, Any]) -> List[HttpStream]:
        """
        :param config: A Mapping of the user input configuration as defined in the connector spec.
        """
        config = self.transform_config(config)
        login, password = self.get_auth(config)
        token: str = self.get_token(login, password)
        user_id: str = config["user_id"]

        return [
            ReportStatistics(
                token=token,
                user_id=user_id,
                date_from=config["time_from_transformed"],
                date_to=config["time_to_transformed"],
                group_by_field=config.get("group_by_field", None),
                is_group_by_date=config.get("is_group_by_date", False),
                campaign_ids=config["campaign_ids"],
            ),
        ]
