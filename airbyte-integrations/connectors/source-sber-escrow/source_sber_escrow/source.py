import logging
import os
from datetime import datetime, timedelta
from typing import Mapping, Any, List, Tuple, Optional, Union

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from source_sber_escrow.auth import CredentialsCraftAuthenticator, TokenAuthenticator
from source_sber_escrow.streams import EscrowAccountsListStream, EscrowAccountsTransactionStream, check_sber_escrow_connection
from source_sber_escrow.types import EndDate, IsSuccess, Message, SberCredentials, StartDate


class SourceSberEscrow(AbstractSource):
    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        credentials = self._get_auth(config)()

        config_credentials = config["credentials"]
        sber_client_cert = credentials.client_cert or config_credentials.get("sber_client_cert")
        sber_client_key = credentials.client_key or config_credentials.get("sber_client_key")
        sber_ca_chain = credentials.ca_chain or config_credentials.get("sber_ca_chain")

        date_from, date_to = self._prepare_dates(config)
        return [
            EscrowAccountsListStream(
                credentials=credentials,
                date_from=date_from,
                date_to=date_to,
                sber_client_cert=sber_client_cert,
                sber_client_key=sber_client_key,
                sber_ca_chain=sber_ca_chain,
            ),
            EscrowAccountsTransactionStream(
                credentials=credentials,
                date_from=date_from,
                date_to=date_to,
                sber_client_cert=sber_client_cert,
                sber_client_key=sber_client_key,
                sber_ca_chain=sber_ca_chain,
            ),
        ]

    def check_connection(self, logger: logging.Logger, config: Mapping[str, Any]) -> Tuple[IsSuccess, Optional[Message]]:
        # Check auth
        auth = self._get_auth(config)
        is_success, message = auth.check_connection()
        if not is_success:
            return False, f"Failed to fetch Sber API token: {message}"

        credentials = auth()

        # Check config
        is_success, message = self._check_config(config=config, credentials=credentials)
        if not is_success:
            return is_success, message

        return True, None

    @staticmethod
    def _get_auth(config: Mapping[str, Any]) -> Union[CredentialsCraftAuthenticator, TokenAuthenticator]:
        credentials = config["credentials"]
        auth_type = credentials["auth_type"]

        if auth_type == "credentials_craft_auth":
            return CredentialsCraftAuthenticator(
                host=credentials["credentials_craft_host"],
                bearer_token=credentials["credentials_craft_token"],
                token_id=credentials["credentials_craft_token_id"],
            )

        if auth_type == "token_auth":
            return TokenAuthenticator(
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                sber_client_cert=credentials.get("sber_client_cert"),
                sber_client_key=credentials.get("sber_client_key"),
                sber_ca_chain=credentials.get("sber_ca_chain"),
            )

        raise ValueError(f"Unknown auth type: '{auth_type}'")

    @staticmethod
    def _check_config(config: Mapping[str, Any], credentials: SberCredentials) -> Tuple[IsSuccess, Optional[Message]]:
        # Check dates config
        date_from, date_to = SourceSberEscrow._prepare_dates(config)
        if not date_from and date_to:
            message = "You must specify date_range"
            return False, message
        if date_from > date_to:
            return False, "'Date from' exceeds 'Date to'."

        # Check certificates
        config_credentials = config["credentials"]
        if not os.environ.get("REQUESTS_CA_BUNDLE"):
            if not (credentials.client_cert and credentials.client_key):
                if not (config_credentials.get("sber_client_cert") and config_credentials.get("sber_client_key")):
                    return False, "REQUESTS_CA_BUNDLE env is missing and Sber certificates are not provided."

        # Check connection
        is_success, message = check_sber_escrow_connection(
            credentials=credentials,
            sber_client_cert=credentials.client_cert or config_credentials.get("sber_client_cert"),
            sber_client_key=credentials.client_key or config_credentials.get("sber_client_key"),
            sber_ca_chain=credentials.ca_chain or config_credentials.get("sber_ca_chain"),
        )
        if not is_success:
            return is_success, message

        return True, None

    @staticmethod
    def _prepare_dates(config: Mapping[str, Any]) -> Tuple[StartDate, EndDate]:
        date_range = config["date_range"]
        range_type = config["date_range"]["date_range_type"]
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        config_date_format: str = "%Y-%m-%d"

        if range_type == "custom_date":
            date_from = date_range["date_from"]
            date_to = date_range["date_to"]
        elif range_type == "from_start_date_to_today":
            date_from = date_range["date_from"]
            if date_range["should_load_today"]:
                date_to = today
            else:
                date_to = today - timedelta(days=1)
        elif range_type == "last_n_days":
            date_from = today - timedelta(days=date_range["last_days_count"])
            if date_range.get("should_load_today", False):
                date_to = today
            else:
                date_to = today - timedelta(days=1)
        else:
            raise ValueError("Invalid date_range_type")

        if isinstance(date_from, str):
            date_from = datetime.strptime(date_from, config_date_format)

        if isinstance(date_to, str):
            date_to = datetime.strptime(date_to, config_date_format)

        return date_from.date(), date_to.date()
