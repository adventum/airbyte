#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from typing import Any, List, Mapping, Tuple

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from .utils import get_config_date_range
from .streams.subscribers import Subscribers
from .streams.find_clients import FindClients


# Source
class SourceSalebot(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, Any]:
        # Just testing easiest request for api
        data = {
            "offset": 0,
            "limit": 1,
            "list": 1,
        }
        try:
            r = requests.get(
                f"https://chatter.salebot.pro/api/{config['api_key']}/get_clients",
                json=data,
            )
            assert r.status_code == 200
            assert r.json()["status"] == "success"
            return True, None
        except Exception as e:
            return False, e

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        api_key = config["api_key"]
        time_from, time_to = get_config_date_range(config)
        group = config.get("group")
        tag = config.get("tag")
        client_type = config.get("client_type")
        streams = []

        subscribers_stream = Subscribers(
            api_key=api_key,
            time_from=time_from,
            time_to=time_to,
            group=group,
            tag=tag,
            client_type=client_type,
        )
        streams.append(subscribers_stream)

        q = config.get("q")
        search_in = config.get("search_in")
        include_all = config.get("include_all")
        if q:
            find_clients_stream = FindClients(
                api_key=api_key, q=q, search_in=search_in, include_all=include_all
            )
            streams.append(find_clients_stream)
        return streams
