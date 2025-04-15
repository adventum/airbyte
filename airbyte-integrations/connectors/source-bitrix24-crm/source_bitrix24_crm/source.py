import logging
from typing import Any, List, Mapping, Optional, Tuple

import requests
from airbyte_cdk.sources import AbstractSource

from .auth import CredentialsCraftAuthenticator
from .utils import get_config_date_range
from .streams.base import Bitrix24CrmStream
from .streams.deals import Deals
from .streams.leads import Leads
from .streams.lists_element import ListsElement
from .streams.statuses import Statuses
from .streams.stage_history import StageHistory
from .streams.users import Users
from .streams.contacts import Contacts


class SourceBitrix24Crm(AbstractSource):
    def check_connection(
        self, logger: logging.Logger, config: Mapping[str, Any]
    ) -> Tuple[bool, Optional[Any]]:
        try:
            resp = requests.get(
                self.streams(config)[0].url_base + "lists.get",
                params={"IBLOCK_TYPE_ID": "lists"},
            )
            if resp.status_code == 200:
                return True, None
            else:
                return False, resp.json()
        except Exception as e:
            return False, e

    def streams(self, config: Mapping[str, Any]) -> List[Bitrix24CrmStream]:
        start_date, end_date = get_config_date_range(config)
        config["date_from"] = start_date.replace(hour=0, minute=0, second=0).strftime(
            "%Y/%m/%dT%H:%M:%S"
        )
        config["date_to"] = end_date.replace(hour=23, minute=59, second=59).strftime(
            "%Y/%m/%dT%H:%M:%S"
        )

        if config["credentials"]["auth_type"] == "credentials_craft_auth":
            cc_authenticator: CredentialsCraftAuthenticator = CredentialsCraftAuthenticator(
                credentials_craft_host=config["credentials"]["credentials_craft_host"],
                credentials_craft_token=config["credentials"]["credentials_craft_token"],
                credentials_craft_token_id=config["credentials"]["credentials_craft_token_id"],
            )
            config["webhook_endpoint"] = cc_authenticator.token

        if config["credentials"]["auth_type"] == "webhook_endpoint_auth":
            config["webhook_endpoint"] = config["credentials"]["webhook_endpoint"]

        return [
            Leads(config),
            Deals(config),
            Statuses(config),
            StageHistory(config),
            ListsElement(config),
            Users(config),
            Contacts(config),
        ]
