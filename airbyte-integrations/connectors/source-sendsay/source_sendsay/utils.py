from typing import Any, Mapping, Optional

import pendulum


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

    # Sendsay uses datetime filters, so we will use
    # >= 2025-01-01 00:00:00 and < 2025-01-03 00:00:00
    # Will return in all data from 01-01 and 01-02
    time_to = time_to.add(days=1)

    return time_from, time_to
