from typing import Any, List, Mapping, Optional, Tuple

import pendulum
import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator

from .streams import AvitoStream
from .streams.calls_by_time import CallsByTime
from .streams.offers import Offers
from .streams.offers_aggregated import OffersAggregated


class SourceAvito(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        streams: list[AvitoStream] = self.streams(config)  # Will also check auth when creating streams
        for stream in streams:
            check, message = stream.check_config(config)
            if not check:
                return False, message
        return True, None

    @staticmethod
    def transform_config_date_range(config: Mapping[str, Any]) -> Mapping[str, Any]:
        date_range: Mapping[str, Any] = config.get("date_range", {})
        date_range_type: str = date_range.get("date_range_type")

        time_from: Optional[pendulum.datetime] = None
        time_to: Optional[pendulum.datetime] = None

        # Meaning is date but storing time since later will use time
        today_date: pendulum.datetime = pendulum.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        if date_range_type == "custom_date":
            time_from = pendulum.parse(date_range["date_from"])
            time_to = pendulum.parse(date_range["date_to"])
        elif date_range_type == "from_start_date_to_today":
            time_from = pendulum.parse(date_range["date_from"])
            if date_range.get("should_load_today"):
                time_to = today_date
            else:
                time_to = today_date.subtract(days=1)
        elif date_range_type == "last_n_days":
            time_from = today_date.subtract(days=date_range.get("last_days_count"))
            if date_range.get("should_load_today"):
                time_to = today_date
            else:
                time_to = today_date.subtract(days=1)

        config["time_from_transformed"], config["time_to_transformed"] = time_from, time_to
        return config

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config = SourceAvito.transform_config_date_range(config)
        # For future improvements
        return config

    @staticmethod
    def get_auth(config: Mapping[str, Any]) -> TokenAuthenticator:
        token_url: str = AvitoStream.url_base + "token"
        data: dict[str, str] = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "grant_type": "client_credentials",
        }
        response: requests.Response = requests.post(url=token_url, data=data)
        if not (200 <= response.status_code < 400):
            raise RuntimeError(f"Failed to get api token: status code = {response.status_code}")

        response_json: dict[str, any] = response.json()
        if "error" in response_json:
            raise RuntimeError(f"Failed to get api token: {response_json['error']['message']}")

        return TokenAuthenticator(token=response_json["access_token"])

    def streams(self, config: Mapping[str, Any]) -> List[AvitoStream]:
        config = self.transform_config(config)
        auth: TokenAuthenticator = self.get_auth(config)

        streams: List[Stream] = [
            CallsByTime(
                authenticator=auth,
                time_from=config["time_from_transformed"],
                time_to=config["time_to_transformed"],
            )
        ]

        if config["use_offers_stream"]:
            streams.append(
                Offers(
                    authenticator=auth,
                    time_from=config["time_from_transformed"],
                    time_to=config["time_to_transformed"],
                    statuses=config.get("offer_statuses", []),
                    category=config.get("offer_category"),
                )
            )

        if config["use_aggregated_offers_stream"]:
            streams.append(
                OffersAggregated(
                    authenticator=auth,
                    time_from=config["time_from_transformed"],
                    time_to=config["time_to_transformed"],
                    item_ids=config["aggregated_offers_item_ids"],
                    period_grouping=config["aggregated_offers_period_grouping"],
                    fields=config["aggregated_offers_fields"]
                )
            )

        return streams
