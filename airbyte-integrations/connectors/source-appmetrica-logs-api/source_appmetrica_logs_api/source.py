#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from typing import Any, Mapping

from airbyte_cdk import TokenAuthenticator
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_protocol.models import SyncMode

from .auth import CredentialsCraftAuthenticator
from .streams.logs_api.stream import AppmetricaLogsApi
from .streams.reports_api.table import AppmetricaReportsTable
from .utils import get_config_date_range


# Source
class SourceAppmetricaLogsApi(AbstractSource):
    def check_connection(self, logger, config) -> tuple[bool, Any]:
        config = SourceAppmetricaLogsApi.prepare_config(config)

        streams = self.streams(config)
        if not streams:
            return False, "You must add at least one stream"
        try:
            next(streams[0].read_records(sync_mode=SyncMode.full_refresh))
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_auth(config: Mapping[str, Any]) -> TokenAuthenticator:
        if config["credentials"]["auth_type"] == "access_token_auth":
            return TokenAuthenticator(config["credentials"]["access_token"])
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
                "Invalid Auth type. Available: access_token_auth and credentials_craft_auth"
            )

    @staticmethod
    def prepare_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        # for future improvements
        return config

    def streams(self, config: Mapping[str, Any]) -> list[Stream]:
        config = SourceAppmetricaLogsApi.prepare_config(config)
        auth = SourceAppmetricaLogsApi.get_auth(config)
        start_date, end_date = get_config_date_range(config)
        tables_api_version = config.get("tables_api_version", "v1")
        streams = []

        for source in config.get("sources", []):
            streams.append(
                AppmetricaLogsApi(
                    authenticator=auth,
                    application_id=config["application_id"],
                    date_from=start_date,
                    date_to=end_date,
                    chunked_logs_params=config.get(
                        "chunked_logs", {"split_mode_type": "do_not_split_mode"}
                    ),
                    fields=source.get("fields", []),
                    source=source["source_name"],
                    filters=source.get("filters", []),
                    date_dimension=source.get("date_dimension", "default"),
                    event_name_list=source.get("event_name_list"),
                )
            )

        for table in config.get("tables", []):
            streams.append(
                AppmetricaReportsTable(
                    api_version=tables_api_version,
                    authenticator=auth,
                    application_id=config["application_id"],
                    date_from=start_date,
                    date_to=end_date,
                    table_name=table["table_name"],
                    metrics=table["metrics"],
                    dimensions=table.get("dimensions"),
                    filters=table.get("filters"),
                )
            )

        return streams
