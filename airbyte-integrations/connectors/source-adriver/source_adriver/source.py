#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

from typing import Any, List, Mapping, Tuple

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from .streams import Ads, Banners
from .utils import get_config_date_range, get_auth


class SourceAdriver(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, Any]:
        try:
            config = self.transform_config(config)
            get_auth(config)
        except Exception as e:
            return False, e
        return True, None

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config["time_from_transformed"], config["time_to_transformed"] = (
            get_config_date_range(config)
        )
        # For future improvements
        return config

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        config = self.transform_config(config)
        time_from = config["time_from_transformed"]
        time_to = config["time_to_transformed"]
        user_id, token = get_auth(config)
        load_all_ads = config["load_all_ads"]
        load_all_banners = config["load_all_banners"]
        streams = []

        # Add ads stream
        ads_ids: list[int] | None = config.get("ads_ids")
        ads_stream = None
        if ads_ids or load_all_ads:
            # TODO: move params to config, config is still needed for auth
            ads_stream = Ads(
                config=config,
                user_id=user_id,
                token=token,
                objects_ids=ads_ids,
                start_date=time_from,
                end_date=time_to,
                load_all=load_all_ads,
            )
            streams.append(ads_stream)

        # Add banner stream
        banners_ids: list[int] | None = config.get("banners_ids")
        if banners_ids or load_all_banners:
            if load_all_banners and not ads_stream:
                # User in banners stream to get ads ids that are used to get banners ids
                ads_stream = Ads(
                    config=config,
                    user_id=user_id,
                    token=token,
                    objects_ids=None,
                    start_date=time_from,
                    end_date=time_to,
                    load_all=True,
                )
            streams.append(
                Banners(
                    config=config,
                    user_id=user_id,
                    token=token,
                    objects_ids=banners_ids,
                    start_date=time_from,
                    end_date=time_to,
                    load_all=load_all_banners,
                    ads_stream=ads_stream,
                )
            )
        return streams
