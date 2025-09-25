import json
import random
import string
from typing import Iterable, Tuple, Any, Literal, Union
from datetime import datetime, timedelta
from airbyte_cdk import logger as airbyte_logger
from airbyte_cdk.sources.streams.http.availability_strategy import (
    HttpAvailabilityStrategy as _HttpAvailabilityStrategy,
)


logger = airbyte_logger.AirbyteLogger()


class HttpAvailabilityStrategy(_HttpAvailabilityStrategy):
    def check_availability(self, *args, **kwargs):
        return True, None


def random_name(n: int) -> str:
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(10)
    )


def split_date_by_chunks(
    date_from: datetime, date_to: datetime, chunk_size_in_days: int
) -> Iterable[Tuple[str, str]]:
    print("split_date_by_chunks,", date_from, date_to)
    cursor = date_from
    delta = timedelta(days=chunk_size_in_days)
    while cursor < date_to:
        if cursor + delta > date_to:
            yield (cursor, date_to)
            break
        yield (cursor, cursor + delta)
        cursor += delta + timedelta(days=1)


def last_n_days_dates(last_n_days: int) -> Tuple[datetime, datetime]:
    yesterday = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=1)
    return (yesterday - timedelta(days=last_n_days), yesterday)


def yesterday():
    return (
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        - timedelta(days=1)
    ).date()


def today():
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).date()


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def find_by_key(data, target):
    """Search for target values in nested dict"""
    for key, value in data.items():
        if isinstance(value, dict):
            yield from find_by_key(value, target)
        elif key == target:
            yield value


def concat_multiple_lists(list_of_lists):
    return sum(list_of_lists, [])


def get_unique(list1):
    return list(set(list1))


def hide_sensitive_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Uses in streams logging
    Change sensitive values to [REDACTED]
    """
    sensitive_keys = [
        "authorization",
        "x-api-key",
        "access_token",
        "api_key",
        "token",
        "password",
        "secret",
    ]
    return {
        k: ("[REDACTED]" if k.lower() in sensitive_keys else v) for k, v in data.items()
    }


def log_stream_request_data(
    stream_name: str,
    data: Union[dict[str, Any], Any],
    section: Literal["headers", "params", "body", "response", "url"] = "headers",
) -> None:
    """
    Logs a specific section of an HTTP requests for a given stream.

    :param stream_name: The name of the stream being logged.
    :param data: The content to log (headers, params, body, response, or URL).
    :param section: The section type: "headers", "params", "body", "response", or "url".
    """

    label_map = {
        "headers": "REQUEST HEADERS",
        "params": "REQUEST PARAMS",
        "body": "REQUEST BODY",
        "response": "RESPONSE BODY",
        "url": "REQUEST URL",
    }

    label = label_map.get(section, "UNKNOWN SECTION")

    if isinstance(data, dict):
        payload = hide_sensitive_data(data)
    else:
        payload = data

    if isinstance(payload, dict):
        content = json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        content = str(payload)

    logger.info(
        f"\n\n--- {label} ---\n"
        f"Stream: {stream_name}\n"
        f"Content:\n{content}\n"
        f"--- END ---\n\n"
    )
