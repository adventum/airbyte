from datetime import datetime, timedelta
from typing import Mapping

import pendulum


def get_yesterday_date() -> str:
    """Returns yesterday date (mm/dd/yyyy for requests report)."""
    return (datetime.now() - timedelta(1)).date().strftime("%Y/%m/%d") + "T23:59:59"


def get_today_minus_n_days_date(days: int):
    return (datetime.now() - timedelta(days)).date().strftime("%m/%d/%Y") + "T00:00:00"


def get_config_date_range(
    config: Mapping[str, any],
) -> tuple[pendulum.DateTime, pendulum.DateTime]:
    date_range: Mapping[str, any] = config.get("date_range", {})
    date_range_type: str = date_range.get("date_range_type")

    time_from: pendulum.DateTime | None = None
    time_to: pendulum.DateTime | None = None

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

    return (
        time_from,
        time_to,
    )
