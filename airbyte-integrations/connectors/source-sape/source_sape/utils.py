#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#
from typing import Any, Mapping

import pendulum


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
            time_from = today_date.subtract(days=date_range["last_days_count"])
        case _:
            raise ValueError(f"Invalid date range type: {date_range_type}")

    # To load data including time_to
    time_to = time_to.add(days=1).subtract(microseconds=1)
    return time_from, time_to
