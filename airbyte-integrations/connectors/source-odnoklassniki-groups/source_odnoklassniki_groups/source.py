from __future__ import annotations

import logging
from datetime import date, timedelta, datetime
from typing import Mapping, Any, List, Tuple

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from source_odnoklassniki_groups.auth import CredentialsCraftAuthenticator, OKCredentials
from source_odnoklassniki_groups.streams import GetStatTrendsStream, check_group_stream_connection
from source_odnoklassniki_groups.types import IsSuccess, Message, StartDate, EndDate


class SourceOdnoklassnikiGroups(AbstractSource):
    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        credentials = self._get_auth(config)()
        date_from, date_to = self._prepare_dates(config)
        gid = config.get("gid")
        return [
            GetStatTrendsStream(credentials=credentials, gid=gid, date_from=date_from, date_to=date_to),
        ]

    def check_connection(self, logger: logging.Logger, config: Mapping[str, Any]) -> Tuple[IsSuccess, Message | None]:
        # Check connection to CredentialsCraft
        auth = self._get_auth(config)
        if isinstance(auth, CredentialsCraftAuthenticator):
            is_success, message = auth.check_connection()
            if not is_success:
                return False, f"Failed to connect to CredentialsCraft: {message}"

        credentials = auth()

        # Check ads config
        is_success, message = self._check_config(config=config, credentials=credentials)
        if not is_success:
            return is_success, message

        return True, None

    @staticmethod
    def _get_auth(config: Mapping[str, Any]) -> CredentialsCraftAuthenticator:
        credentials = config["credentials"]
        auth_type = credentials["auth_type"]
        if auth_type == "credentials_craft_auth":
            return CredentialsCraftAuthenticator(
                host=credentials["credentials_craft_host"],
                bearer_token=credentials["credentials_craft_token"],
                token_id=credentials["credentials_craft_odnoklassniki_token_id"],
            )
        raise ValueError(f"Unknown auth type: '{auth_type}'")

    @staticmethod
    def _prepare_dates(config: Mapping[str, Any]) -> Tuple[StartDate | None, EndDate | None]:
        if last_days := config.get("last_days"):
            date_from = date.today() - timedelta(days=last_days)
            date_to = date.today() - timedelta(days=1)  # yesterday
            return date_from, date_to

        date_from_str = config.get("date_from")
        date_to_str = config.get("date_to")
        date_from = date.fromisoformat(date_from_str) if date_from_str else None
        date_to = date.fromisoformat(date_to_str) if date_to_str else None
        return date_from, date_to

    @staticmethod
    def _check_config(config: Mapping[str, Any], credentials: OKCredentials) -> Tuple[IsSuccess, Message | None]:
        # Check dates config
        date_from = config.get("date_from")
        date_to = config.get("date_to")
        if date_from and date_to:
            if datetime.fromisoformat(date_from) > datetime.fromisoformat(date_to):
                return False, "'Date from' exceeds 'Date to' in config"

        # Check connection
        is_success, message = check_group_stream_connection(credentials=credentials, gid=config.get("gid"))
        if not is_success:
            return is_success, message

        return True, None
