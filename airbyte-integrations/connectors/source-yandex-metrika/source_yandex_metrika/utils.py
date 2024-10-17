import random
import string
from datetime import datetime, timedelta
from typing import Mapping

import pendulum

DATE_FORMAT = "%Y-%m-%d"


def daterange_days_list(date_from: datetime, date_to: datetime, days_delta: int = 1) -> list[str]:
    cursor_date = date_from
    date_to = date_to

    ranges = []
    while cursor_date <= date_to:
        if cursor_date + timedelta(days=days_delta) > date_to:
            ranges.append({"date_from": cursor_date, "date_to": date_to})
            break
        ranges.append(
            {
                "date_from": cursor_date,
                "date_to": cursor_date + timedelta(days=days_delta - 1),
            }
        )
        cursor_date += timedelta(days=days_delta)
    return ranges


def yesterday_date() -> str:
    return datetime.strftime(datetime.now() - timedelta(1), DATE_FORMAT)


def today_minus_n_days_date(n_days: int) -> str:
    return datetime.strftime(datetime.now() - timedelta(n_days), DATE_FORMAT)


def random_output_filename() -> str:
    return f"output/{random_str(20)}.csv"


def random_str(n: int) -> str:
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))


def partition_list(lst, n):
    # Calculate the length of each partition
    partition_size = len(lst) // n

    # Calculate the number of remaining elements after partitioning
    remaining = len(lst) % n

    # Build a list of partitions
    partitions = []
    start = 0
    for i in range(n):
        # Determine the end index of the partition, accounting for remaining elements
        end = start + partition_size
        if i < remaining:
            end += 1

        # Add the partition to the list
        partitions.append(lst[start:end])
        start = end

    return partitions


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
