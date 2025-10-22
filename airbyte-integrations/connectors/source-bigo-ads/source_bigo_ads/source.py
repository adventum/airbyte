from typing import Any, List, Mapping, Tuple

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from .utils import get_config_date_range
from .auth import HeadersAuthenticator
from .streams.campaign_stream import CampaignStream


# Source
class SourceBigoAds(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, Any]:
        try:
            auth: HeadersAuthenticator = HeadersAuthenticator(
                curl_request=config["curl"]
            )
            response = requests.post(
                "https://ads.bigo.sg/api/dsp/user/user", headers=auth.headers, json={}
            )
            assert response.status_code == 200
            return True, None
        except Exception as e:
            return False, e

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        time_from, time_to = get_config_date_range(config)
        config["time_from_transformed"], config["time_to_transformed"] = (
            time_from.date(),
            time_to.date(),
        )
        # For future improvements
        return config

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        config = self.transform_config(config)
        auth: HeadersAuthenticator = HeadersAuthenticator(curl_request=config["curl"])
        return [
            CampaignStream(
                authenticator=auth,
                indicators=config["indicators"],
                date_from=config["time_from_transformed"],
                date_to=config["time_to_transformed"],
                campaign_codes=config["campaign_codes"],
            )
        ]
