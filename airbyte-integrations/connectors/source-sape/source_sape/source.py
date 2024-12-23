#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


from typing import Any, Mapping
from xmlrpc.client import ServerProxy

from .client import CookiesTransport
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from .streams import GetAvgPrices
from .base_stream import SapeStream


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

        # Create production streams with auth from base one
        get_avg_prices_stream = GetAvgPrices(client_=client)
        return [get_avg_prices_stream]
