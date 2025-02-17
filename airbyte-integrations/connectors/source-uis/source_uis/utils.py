import random

from datetime import datetime, timedelta
from typing import Any, Mapping


def transform_config_date_range(config: Mapping[str, Any]) -> Mapping[str, Any]:
    date_range: Mapping[str, Any] = config.get("date_range", {})
    date_range_type: str = date_range.get("date_range_type")
    date_from: datetime | None = None
    date_to: datetime | None = None
    today_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    from_user_date_format: str = "%Y-%m-%d"
    date_format: str = "%Y-%m-%d %H:%M:%S"

    if date_range_type == "custom_date":
        date_from = datetime.strptime(date_range.get("date_from"), from_user_date_format)
        date_to = datetime.strptime(date_range.get("date_to"), from_user_date_format)
    elif date_range_type == "from_start_date_to_today":
        date_from = datetime.strptime(date_range.get("date_from"), from_user_date_format)
        date_to = today_date if date_range.get("should_load_today") else today_date - timedelta(days=1)
    elif date_range_type == "last_n_days":
        date_from = today_date - timedelta(days=date_range.get("last_days_count", 0))
        date_to = today_date if date_range.get("should_load_today") else today_date - timedelta(days=1)

    # Transform date format from "2000-01-01" to "2000-01-01 00:00:00"
    config["date_from_transformed"] = date_from.strftime(date_format) if date_from else None
    config["date_to_transformed"] = date_to.strftime(date_format) if date_to else None

    return config


def create_random_request_id() -> str:
    request_id: str = ''.join(str(random.randint(0, 9)) for _ in range(32))
    return request_id
