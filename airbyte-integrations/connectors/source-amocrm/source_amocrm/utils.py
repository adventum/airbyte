#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#
from typing import Any, Mapping

import pendulum

from .auth import CredentialsCraftAuthenticator, AmoCrmAuthenticator


def parse_date_range(
    config: Mapping[str, Any],
) -> tuple[pendulum.DateTime, pendulum.DateTime]:
    date_range: Mapping[str, Any] = config["date_range"]
    date_range_type: str = date_range["date_range_type"]

    time_from: pendulum.DateTime | None
    time_to: pendulum.DateTime

    today_date: pendulum.datetime = pendulum.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    match date_range_type:
        case "custom_date":
            time_from = pendulum.parse(date_range["date_from"])
            time_to = pendulum.parse(date_range["date_to"])
        case "from_start_date_to_today":
            time_to = today_date
            if date_range.get("should_load_today"):
                time_to = time_to.subtract(days=1)
            time_from = pendulum.parse(date_range["date_from"])
        case "last_n_days":
            time_to = today_date
            if date_range.get("should_load_today"):
                time_to = time_to.subtract(days=1)
            time_from = today_date.subtract(days=date_range["last_days"])
        case _:
            raise ValueError(f"Invalid date range type: {date_range_type}")

    # To load data including time_to
    time_to = time_to.add(days=1).subtract(microseconds=1)
    return time_from, time_to


def get_auth(
    config: Mapping[str, Any],
) -> CredentialsCraftAuthenticator | AmoCrmAuthenticator:
    if config["credentials"]["auth_type"] == "access_token_auth":
        return AmoCrmAuthenticator(token=config["credentials"]["access_token"])
    elif config["credentials"]["auth_type"] == "credentials_craft_auth":
        return CredentialsCraftAuthenticator(
            credentials_craft_host=config["credentials"]["credentials_craft_host"],
            credentials_craft_token=config["credentials"]["credentials_craft_token"],
            credentials_craft_token_id=config["credentials"][
                "credentials_craft_token_id"
            ],
        )
    else:
        raise ValueError(
            "Invalid Auth type. Available: access_token_auth and credentials_craft_auth"
        )
