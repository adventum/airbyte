#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

import xml.etree.ElementTree as ET
from typing import Any, Mapping, Optional

import pendulum
import requests

url_base = "https://api.adriver.ru/"


def get_config_date_range(
    config: Mapping[str, Any],
) -> tuple[pendulum.datetime, pendulum.datetime]:
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

    return time_from, time_to


def get_auth(config: Mapping[str, Any]) -> tuple[str, str]:
    """Auth in Adriver to get user_id and token for api"""
    token_url: str = url_base + "login"
    login_headers: dict[str, str] = {
        "Content-Type": "application/atom+xml",
        "X-Auth-Login": config["login"],
        "X-Auth-Passwd": config["password"],
    }
    login_response: requests.Response = requests.get(token_url, headers=login_headers)
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
