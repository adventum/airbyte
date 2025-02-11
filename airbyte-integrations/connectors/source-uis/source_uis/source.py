#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

import requests

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from datetime import datetime
from typing import Any, List, Mapping, Tuple

from .auth import CredentialsCraftAuthenticator
from .streams.communications import Communications
from .streams.communications_report import CommunicationsReport
from .streams.visitor_sessions_report import VisitorSessionsReport
from .utils import transform_config_date_range, create_random_request_id


"""
If you want to add a new stream, you need to:
1. Create a new python file in the ./streams directory
2. Inherit from UisStream
3. Add a list of fields (str) to the file ./streams/stream_fields.py and import it in a new stream file
4. Create the api_endpoint attribute in the new stream class and substitute the value from the API documentation
5. Overload the arguments into the parent class, as is done in other streams (communications_report)
6. Add a schema according to the fields described in the API documentation in ./schemas/new_stream.json
7. Add a new stream to the final list source.streams

API DOCS: https://www.uiscom.ru/academiya/spravochnyj-centr/dokumentatsiya-api/data_api/
"""


class SourceUis(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        """
        :param config:  the user-input config object conforming to the connector's spec.yaml
        :param logger:  logger object
        :return Tuple[bool, any]: (True, None) if the input config can be used to connect to the API successfully, (False, error) otherwise.
        """

        try:
            api_url = "https://dataapi.uiscom.ru/v2.0"
            random_id: str = create_random_request_id()
            access_token: str = self.get_auth(config)
            headers: dict[str, str] = {
                "Content-Type": "application/json; charset=UTF-8"
            }
            body: dict[str, Any] = {
                "jsonrpc": "2.0",
                "id": random_id,
                "method": "get.communications_report",
                "params": {
                    "access_token": access_token,
                }
            }

            response: requests.Response = requests.post(api_url, headers=headers, json=body)

            """
            We only check the status code.
            Due to the fact that we do not pass all the data required by the API for simplification,
            as a result the API itself will return an error,
            but with code 200. We only check for connection
            """

            if response.status_code == 200:
                logger.info("Connection successful.")
                return True, None
            else:
                logger.error(f"Failed to connect. Status code: {response.status_code}")
                return False, response.text

        except Exception as e:
            logger.error(f"Error during connection check: {str(e)}")
            return False, str(e)

    @staticmethod
    def get_auth(config: Mapping[str, Any]) -> str:
        auth_type: str = config["credentials"]["auth_type"]
        if auth_type == "access_token_auth":
            return config["credentials"]["access_token"]
        elif auth_type == "credentials_craft_auth":
            return CredentialsCraftAuthenticator(
                credentials_craft_host=config["credentials"]["credentials_craft_host"],
                credentials_craft_token=config["credentials"]["credentials_craft_token"],
                credentials_craft_token_id=config["credentials"]["credentials_craft_token_id"],
            ).token
        else:
            raise Exception(
                f"Invalid Auth type {auth_type}. Available: access_token_auth and credentials_craft_auth",
            )

    @staticmethod
    def prepare_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config = transform_config_date_range(config)
        return config

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        """
        :param config: A Mapping of the user input configuration as defined in the connector spec.
        """
        prepared_config = self.prepare_config(config)

        access_token: str = self.get_auth(prepared_config)
        date_from: datetime = prepared_config["date_from_transformed"]
        date_to: datetime = prepared_config["date_to_transformed"]

        """Add aggregated streams"""
        communication_streams = []
        for stream_config in prepared_config.get("communication_streams", []):
            stream = Communications(
                access_token=access_token,
                report_id=stream_config["report_id"],
                fields=stream_config["fields"],
                date_from=date_from,
                date_to=date_to,
            )
            communication_streams.append(stream)

        return [
            CommunicationsReport(access_token, date_from, date_to),
            VisitorSessionsReport(access_token, date_from, date_to),
            *communication_streams
        ]
