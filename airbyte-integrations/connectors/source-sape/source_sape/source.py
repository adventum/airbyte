#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


from typing import Any, Mapping
from xmlrpc.client import ServerProxy

import requests
from airbyte_cdk import TokenAuthenticator

from .xml_streams.client import CookiesTransport
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from .xml_streams.streams import GetAvgPrices, GetProjectsMoneyStats
from .xml_streams.base_stream import SapeXMLStream
from .rest_streams.base_stream import SapeRestStream
from .rest_streams.streams import ExtendedStatistics
from .utils import parse_date_range


# Source
class SourceSape(AbstractSource):
    def check_connection(self, logger, config) -> tuple[bool, any]:
        try:
            self.get_auth(config)
        except Exception as e:  # TODO: getting xml client may be added if those streams will ever be used
            return False, str(e)
        return True, None

    @staticmethod
    def get_auth(config: Mapping[str, any]) -> TokenAuthenticator:
        """Auth for rest stream"""
        login = config["credentials"]["login"]
        token = config["credentials"]["token"]
        response = requests.post(
            SapeRestStream.url_base + "login", json={"login": login, "token": token}
        )
        access_token = response.json()["accessToken"]
        # No Bearer for Sape rest api
        return TokenAuthenticator(token=access_token, auth_method="")

    @staticmethod
    def get_xml_client(config: Mapping[str, any]) -> ServerProxy:
        login = config["credentials"]["login"]
        token = config["credentials"]["token"]

        client: ServerProxy = ServerProxy(
            SapeXMLStream.url_base, transport=CookiesTransport()
        )
        # TODO: credentialsCraft auth not supported yet
        client.sape.login(login, token)
        return client

    def streams(self, config: Mapping[str, Any]) -> list[Stream]:
        # Create authenticated client for Sape XML session
        client = self.get_xml_client(config)

        # Get Sape Rest temporary api token
        auth = self.get_auth(config)

        # Parse datetime
        time_from, time_to = parse_date_range(config)

        # Create XML streams with auth from base one
        get_avg_prices_stream = GetAvgPrices(client_=client)
        get_projects_money_stats_stream = GetProjectsMoneyStats(
            client_=client, start_date=time_from, end_date=time_to
        )

        # Create Rest streams
        extended_statistics_stream = ExtendedStatistics(
            authenticator=auth, start_date=time_from, end_date=time_to
        )
        return [
            get_avg_prices_stream,
            get_projects_money_stats_stream,
            extended_statistics_stream,
        ]
