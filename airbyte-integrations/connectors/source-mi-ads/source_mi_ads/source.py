from typing import Any, List, Mapping, Tuple

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from .utils import get_config_date_range
from .auth import MiAdsAuthenticator
from .streams.reporting_api_streams.data_query_streams import (
    DataQueryInterfaceOneStream,
)


# Source
class SourceMiAds(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, Any]:
        # just try to get token
        try:
            auth = MiAdsAuthenticator(config["app_id"], config["app_key"])
            _ = auth.token
            return True, None
        except Exception as e:
            return False, e

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config["time_from_transformed"], config["time_to_transformed"] = (
            get_config_date_range(config)
        )
        # For future improvements
        return config

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        config = self.transform_config(config)
        auth = MiAdsAuthenticator(config["app_id"], config["app_key"])
        return [
            DataQueryInterfaceOneStream(
                authenticator=auth,
                time_from=config["time_from_transformed"],
                time_to=config["time_to_transformed"],
                ad_type=config["ad_type_query_stream"],
                dimensions=config["dimensions_query_stream"],
                account_ids=config.get("account_ids_query_stream"),
                ad_campaign_ids=config.get("ad_campaign_ids_query_stream"),
            )
        ]
