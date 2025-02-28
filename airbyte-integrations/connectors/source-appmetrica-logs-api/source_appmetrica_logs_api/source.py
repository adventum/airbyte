#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from typing import Any, Mapping

from airbyte_cdk import TokenAuthenticator
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from .auth import CredentialsCraftAuthenticator
from .streams.logs_api.stream import AppmetricaLogsApiStream
from .utils import get_config_date_range


# Source
class SourceAppmetricaLogsApi(AbstractSource):
    def check_connection(self, logger, config) -> tuple[bool, Any]:
        # config = SourceAppmetricaLogsApi.prepare_config(config)
        #
        # first_stream_source = config["sources"][0]
        #
        # source_type = first_stream_source["source_name"]
        # available_fields = AVAILABLE_FIELDS[source_type]["fields"].keys()
        # if config.get("check_fields", True):
        #     for field in first_stream_source.get("fields", []):
        #         if field not in available_fields:
        #             return (
        #                 False,
        #                 f'Field "{field}" is invalid for source type {source_type}',
        #             )
        #
        # if (
        #     config.get("event_name_list")
        #     and first_stream_source["source_name"] != "events"
        # ):
        #     return (
        #         False,
        #         f"event_name_list is not available for source {first_stream_source['source_name']}",
        #     )
        #
        # for filter_n, filter_ in enumerate(first_stream_source.get("filters", [])):
        #     name = filter_["name"]
        #     if name not in available_fields:
        #         return (
        #             False,
        #             f"Filter {filter_n} ({name}) not in available fields list.",
        #         )
        #
        # auth = SourceAppmetricaLogsApi.get_auth(config)
        # if isinstance(auth, CredentialsCraftAuthenticator):
        #     cc_auth_check_result = auth.check_connection()
        #     if not cc_auth_check_result[0]:
        #         return cc_auth_check_result
        #
        # applications_list_request = requests.get(
        #     "https://api.appmetrica.yandex.ru/management/v1/applications",
        #     headers=auth.get_auth_header(),
        # )
        # if applications_list_request.status_code != 200:
        #     return (
        #         False,
        #         f"Test API request error {applications_list_request.status_code}: {applications_list_request.text}",
        #     )
        # applications_list = applications_list_request.json()["applications"]
        # available_ids_list = [app["id"] for app in applications_list]
        # if config["application_id"] not in available_ids_list:
        #     return False, "Auth token is valid, but Application ID is invalid"

        return True, None

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
        return [
            AppmetricaLogsApiStream(
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
            for source in config["sources"]
        ]
