import logging
import os
from datetime import date, datetime, timedelta
from typing import Mapping, Any, List, Tuple, Callable, Optional

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from source_sber_escrow.auth import CredentialsCraftAuthenticator
from source_sber_escrow.streams import EscrowAccountsListStream, EscrowAccountsTransactionStream, check_sber_escrow_connection
from source_sber_escrow.types import EndDate, IsSuccess, Message, SberCredentials, StartDate


class SourceSberEscrow(AbstractSource):
    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        credentials = self._get_auth(config)()

        config_credentials = config["credentials"]
        sber_client_cert = credentials.client_cert or config_credentials.get("sber_client_cert")
        sber_client_key = credentials.client_key or config_credentials.get("sber_client_key")
        sber_ca_chain = credentials.ca_chain or config_credentials.get("sber_ca_chain")

        commisioning_object_codes = config.get("commisioning_object_codes")
        individual_terms_id = config.get("individual_terms_id")

        date_from, date_to = self._prepare_dates(config)
        return [
            EscrowAccountsListStream(
                credentials=credentials,
                date_from=date_from,
                date_to=date_to,
                commisioning_object_codes=commisioning_object_codes,
                individual_terms_id=individual_terms_id,
                sber_client_cert=sber_client_cert,
                sber_client_key=sber_client_key,
                sber_ca_chain=sber_ca_chain,
            ),
            EscrowAccountsTransactionStream(
                credentials=credentials,
                date_from=date_from,
                date_to=date_to,
                commisioning_object_codes=commisioning_object_codes,
                individual_terms_id=individual_terms_id,
                sber_client_cert=sber_client_cert,
                sber_client_key=sber_client_key,
                sber_ca_chain=sber_ca_chain,
            ),
        ]

    def check_connection(self, logger: logging.Logger, config: Mapping[str, Any]) -> Tuple[IsSuccess, Optional[Message]]:
        # Check auth
        auth = self._get_auth(config)
        if isinstance(auth, CredentialsCraftAuthenticator):
            is_success, message = auth.check_connection()
            if not is_success:
                return False, f"Failed to connect to CredentialsCraft: {message}"

        credentials = auth()

        # Check config
        is_success, message = self._check_config(config=config, credentials=credentials)
        if not is_success:
            return is_success, message

        return True, None

    @staticmethod
    def _get_auth(config: Mapping[str, Any]) -> Callable:
        credentials = config["credentials"]
        auth_type = credentials["auth_type"]

        if auth_type == "credentials_craft_auth":
            return CredentialsCraftAuthenticator(
                host=credentials["credentials_craft_host"],
                bearer_token=credentials["credentials_craft_token"],
                sber_token_id=credentials["credentials_craft_sber_token_id"],
            )

        if auth_type == "token_auth":
            return lambda: SberCredentials(access_token=credentials["token"], client_id=credentials["client_id"])

        raise ValueError(f"Unknown auth type: '{auth_type}'")

    @staticmethod
    def _check_config(config: Mapping[str, Any], credentials: SberCredentials) -> Tuple[IsSuccess, Optional[Message]]:
        # Check dates config
        date_from = config.get("date_from")
        date_to = config.get("date_to")
        last_days = config.get("last_days")

        if not (last_days or (date_from and date_to)):
            message = "You must specify either 'Date from' and 'Date to' or just 'Load last N days' params in config."
            return False, message

        if date_from and date_to:
            if datetime.fromisoformat(date_from) > datetime.fromisoformat(date_to):
                return False, "'Date from' exceeds 'Date to'."

        # Check certificates
        config_credentials = config["credentials"]
        if not os.environ.get("REQUESTS_CA_BUNDLE"):
            if not (credentials.client_cert and credentials.client_key):
                if not (config_credentials.get("sber_client_cert") and config_credentials.get("sber_client_key")):
                    return False, "REQUESTS_CA_BUNDLE env is missing and Sber certificates are not provided."

        # Check commissioning object codes or individual terms IDs
        commisioning_object_codes = config.get("commisioning_object_codes")
        individual_terms_id = config.get("individual_terms_id")
        if not (commisioning_object_codes or individual_terms_id):
            return False, "No commissioning object codes or individual terms IDs provided"

        # Check connection
        is_success, message = check_sber_escrow_connection(
            credentials=credentials,
            commisioning_object_codes=commisioning_object_codes,
            individual_terms_id=individual_terms_id,
            sber_client_cert=credentials.client_cert or config_credentials.get("sber_client_cert"),
            sber_client_key=credentials.client_key or config_credentials.get("sber_client_key"),
            sber_ca_chain=credentials.ca_chain or config_credentials.get("sber_ca_chain"),
        )
        if not is_success:
            return is_success, message

        return True, None

    @staticmethod
    def _prepare_dates(config: Mapping[str, Any]) -> Tuple[Optional[StartDate], Optional[EndDate]]:
        if last_days := config.get("last_days"):
            date_from = date.today() - timedelta(days=last_days)
            date_to = date.today() - timedelta(days=1)  # yesterday
            return date_from, date_to

        default_date_from = default_date_to = date.today() - timedelta(days=1)  # yesterday
        date_from_str = config.get("date_from")
        date_to_str = config.get("date_to")
        date_from = date.fromisoformat(date_from_str) if date_from_str else default_date_from
        date_to = date.fromisoformat(date_to_str) if date_to_str else default_date_to
        return date_from, date_to
