#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from typing import Any, List, Mapping, Tuple

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk import TokenAuthenticator
from .utils import get_config_date_range
from .streams.calls_stream import Calls
from .auth import CredentialsCraftAuthenticator


# Source
class SourceYandexRealty(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, Any]:
        # TODO: check connection
        return True, None

    def get_auth(self, config: Mapping[str, Any]) -> TokenAuthenticator:
        if config["credentials"]["auth_type"] == "access_token_auth":
            return TokenAuthenticator(token=config["credentials"]["access_token"], auth_method="OAuth")
        elif config["credentials"]["auth_type"] == "credentials_craft_auth":
            return CredentialsCraftAuthenticator(
                credentials_craft_host=config["credentials"]["credentials_craft_host"],
                credentials_craft_token=config["credentials"][
                    "credentials_craft_token"
                ],
                credentials_craft_token_id=config["credentials"][
                    "credentials_craft_token_id"
                ],
            )
        else:
            raise Exception(
                "Неверный тип авторизации. Доступные: access_token_auth and credentials_craft_auth"
            )

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        # For future improvements
        return config

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        config = self.transform_config(config)
        time_from, time_to = get_config_date_range(config)
        auth = self.get_auth(config)
        return [
            Calls(
                authenticator=auth,
                date_from=time_from.date(),
                date_to=time_to.date(),
                client_id=config["client_id"],
                agency_id=config.get("agency_id"),
            )
        ]
