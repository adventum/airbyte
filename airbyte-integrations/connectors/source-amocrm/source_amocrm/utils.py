#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#
from typing import Any, Mapping

import pendulum

from .auth import CredentialsCraftAuthenticator, AmoCrmAuthenticator


def parse_date_range(
    config: Mapping[str, Any],
) -> tuple[pendulum.Date, pendulum.Date]:
    date_range: Mapping[str, Any] = config["date_range"]
    date_range_type: str = date_range["date_range_type"]

    date_from: pendulum.Date | None
    date_to: pendulum.Date

    today_date: pendulum.Date = pendulum.now().date()

    match date_range_type:
        case "custom_date":
            date_from = pendulum.parse(date_range["date_from"])
            date_to = pendulum.parse(date_range["date_to"])
        case "from_start_date_to_today":
            date_to = today_date
            if date_range.get("should_load_today"):
                date_to = date_to.subtract(days=1)
            date_from = pendulum.parse(date_range["date_from"])
        case "last_n_days":
            date_to = today_date
            if date_range.get("should_load_today"):
                date_to = date_to.subtract(days=1)
            date_from = today_date.subtract(days=date_range["last_days_count"])
        case _:
            raise ValueError(f"Invalid date range type: {date_range_type}")

    return date_from, date_to


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
