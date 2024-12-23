#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


from typing import Any, Mapping
from xmlrpc.client import ServerProxy

from .client import CookiesTransport
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from .streams import GetAvgPrices, GetProjectsMoneyStats
from .base_stream import SapeStream
from .utils import parse_date_range


# Source
class SourceSape(AbstractSource):
    def check_connection(self, logger, config) -> tuple[bool, any]:
        # TODO
        return True, None

    def streams(self, config: Mapping[str, Any]) -> list[Stream]:
        # Create authenticated client for Sape session
        client: ServerProxy = ServerProxy(
            SapeStream.url_base, transport=CookiesTransport()
        )
        # TODO: credentialsCraft auth not supported yet
        client.sape.login(
            config["credentials"]["login"], config["credentials"]["token"]
        )

        # Parse datetime
        time_from, time_to = parse_date_range(config)

        # Create production streams with auth from base one
        get_avg_prices_stream = GetAvgPrices(client_=client)
        get_projects_money_stats_stream = GetProjectsMoneyStats(client_=client, start_date=time_from, end_date=time_to)

        return [get_avg_prices_stream, get_projects_money_stats_stream]
