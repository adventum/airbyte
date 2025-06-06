#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

import xml.etree.ElementTree as ET
from typing import Any, List, Mapping, Optional, Tuple

import pendulum
import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from .streams import AdriverStream, Ads, Banners


class SourceAdriver(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, Any]:
        try:
            config = self.transform_config(config)
            self.get_auth(config)
        except Exception as e:
            return False, e
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

        config["time_from_transformed"], config["time_to_transformed"] = (
            time_from,
            time_to,
        )
        return config

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config = SourceAdriver.transform_config_date_range(config)
        # For future improvements
        return config

    @staticmethod
    def get_auth(config: Mapping[str, Any]) -> tuple[str, str]:
        """Auth in Adriver to get user_id and token for api"""
        token_url: str = AdriverStream.url_base + "login"
        login_headers: dict[str, str] = {
            "Content-Type": "application/atom+xml",
            "X-Auth-Login": config["login"],
            "X-Auth-Passwd": config["password"],
        }
        login_response: requests.Response = requests.get(
            token_url, headers=login_headers
        )
        if not (200 <= login_response.status_code < 400):
            raise RuntimeError(
                f"Failed to get api token: status code = {login_response.status_code}"
            )

        # Register namespaces
        namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "adriver": "http://adriver.ru/ns/restapi/atom",
        }

        # Parse the XML
        root = ET.fromstring(login_response.text)

        # Extract values
        user_id = root.find("adriver:userId", namespaces).text
        token = root.find("adriver:token", namespaces).text
        return user_id, token

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        config = self.transform_config(config)
        time_from = config["time_from_transformed"]
        time_to = config["time_to_transformed"]
        user_id, token = self.get_auth(config)
        streams = []

        # Add ads stream
        ads_ids: list[int] | None = config.get("ads_ids")
        if ads_ids:
            streams.append(
                Ads(
                    user_id=user_id,
                    token=token,
                    objects_ids=ads_ids,
                    start_date=time_from,
                    end_date=time_to,
                )
            )

        # Add banner stream
        banners_ids: list[int] | None = config.get("banners_ids")
        if banners_ids:
            streams.append(
                Banners(
                    user_id=user_id,
                    token=token,
                    objects_ids=banners_ids,
                    start_date=time_from,
                    end_date=time_to,
                )
            )
        return streams
