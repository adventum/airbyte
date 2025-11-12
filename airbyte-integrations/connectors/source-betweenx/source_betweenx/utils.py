from typing import Any, Mapping, Optional

import pendulum

def get_config_date_range(
    config: Mapping[str, Any],
) -> tuple[pendulum.DateTime, pendulum.DateTime]:
    date_range: Mapping[str, Any] = config.get("date_range", {})
    date_range_type: str = date_range.get("date_range_type")

    time_from: Optional[pendulum.DateTime] = None
    time_to: Optional[pendulum.DateTime] = None

    # Meaning is date but storing time since later will use time
    today_date: pendulum.DateTime = pendulum.now().replace(
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


base_headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "X-Requested-With": "XMLHttpRequest",
}
