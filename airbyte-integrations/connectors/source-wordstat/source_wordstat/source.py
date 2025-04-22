from typing import Any, List, Mapping, Optional, Tuple

import pendulum
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_protocol.models import SyncMode

from .auth import HeadersAuthenticator
from .streams import Search


class SourceWordstat(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        auth: HeadersAuthenticator = HeadersAuthenticator(curl_request=config["curl"])

        today_date: pendulum.datetime = pendulum.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        keyword: str = "Google Sheets"  # Random word combination not to use main ones to lower chances of getting captcha
        new_config: dict[str, Any] = {
            "keywords": [keyword],
            "group_by": {"group_type": "day"},
            "devices": [config["devices"][0]],
            "region": {"region_type": "all"},
            "split_devices": False,
        }

        try:
            test_stream = Search(
                authenticator=auth,
                config=new_config,
                date_from=today_date.subtract(days=3),
                date_to=today_date.subtract(days=1),
            )
        except ValueError as ex:
            return False, str(ex)
        try:
            test_stream.read_records(
                sync_mode=SyncMode.full_refresh,
                stream_slice={"keyword": keyword},
            )
        except ValueError as ex:
            return False, str(ex)
        except StopIteration:
            return False, "Не удалось получить данные. Проверьте конфигурацию источника"
        except Exception as ex:
            logger.warning(ex)
            return False, f"Не удалось получить данные из-за ошибки: {str(ex)}"
        return True, None

    @staticmethod
    def transform_config_date_range(config: Mapping[str, Any]) -> Mapping[str, Any]:
        """Transform start date and end date to pendulum for easier further work"""
        date_range: Mapping[str, Any] = config.get("date_range", {})
        date_range_type: str = date_range.get("date_range_type")

        date_from: Optional[pendulum.datetime] = None
        date_to: Optional[pendulum.datetime] = None

        # Meaning is date but storing time since later will use time
        today_date: pendulum.datetime = pendulum.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        """Transform str to pendulum.datetime"""
        if date_range_type == "custom_date":
            date_from = pendulum.parse(date_range["date_from"])
            date_to = pendulum.parse(date_range["date_to"])
        elif date_range_type == "from_start_date_to_yesterday":
            date_from = pendulum.parse(date_range["date_from"])
            date_to = today_date.subtract(days=1)
        elif date_range_type == "last_n_days":
            date_from = today_date.subtract(days=date_range.get("last_days_count"))
            date_to = today_date.subtract(days=1)

        group_by: str = config["group_by"]["group_type"]

        """Adjust dates for pendulum api requirements"""
        batch_size: int = 3

        match group_by:
            case "day":
                """No earlier than 60 days ago, no later than yesterday"""
                sixty_days_ago = today_date.subtract(days=60)
                yesterday_date = today_date.subtract(days=1)
                date_from = min(max(date_from, sixty_days_ago), yesterday_date)
                date_to = max(min(date_to, yesterday_date), sixty_days_ago)

                delta: int = (date_to - date_from).days
                if delta < batch_size - 1:
                    date_from = date_to.subtract(
                        days=batch_size - 1 - delta
                    )  # delta is 0 -> the same day -> needs 2 days before
                    if date_from < sixty_days_ago:
                        date_from = date_from.add(days=3)
                        date_to = date_to.add(days=3)

            case "week":
                """
                Starts on monday, ends on sunday.
                No earlier than 1st month of year 6 years ago from tomorrow date
                (now is 2024 means no older than january 2018)
                """
                min_date_from = (
                    today_date.subtract(years=6).set(month=1, day=1).start_of("week")
                )
                if min_date_from.year != today_date.year - 6:  # Got previous year
                    min_date_from = min_date_from.add(weeks=1)

                end_of_last_week = today_date.subtract(weeks=1).end_of("week")

                date_from = min(
                    max(date_from.start_of("week"), min_date_from),
                    today_date.start_of("week"),
                )

                # Sunday, no more than last sunday, no less than 6 years ago
                date_to = max(
                    min(date_to.end_of("week"), end_of_last_week),
                    today_date.subtract(years=6).set(month=1, day=1).end_of("week"),
                )

                delta: int = (date_to - date_from).weeks
                if delta < batch_size - 1:
                    date_from = date_from.subtract(
                        weeks=batch_size - 1 - delta
                    )  # delta is 0 -> the same week -> need also 2 weeks before
                    if date_from < min_date_from:
                        date_from = date_from.add(weeks=3)
                        date_to = date_to.add(weeks=3)
            case "month":
                """
                Starts with 1st day of month, ends with last, no later than last month
                """
                min_date_from = today_date.subtract(years=6).start_of("year")
                date_from = min(
                    max(date_from.start_of("month"), min_date_from),
                    today_date.start_of("month"),
                )

                end_of_previous_month = today_date.subtract(months=1).end_of("month")
                date_to = max(
                    min(date_to.end_of("month"), end_of_previous_month),
                    today_date.subtract(years=6).set(month=1).end_of("month"),
                )

                delta: int = (date_to - date_from).months
                if delta < batch_size - 1:
                    date_from = date_from.subtract(months=batch_size - 1 - delta)
                    if date_from < min_date_from:
                        date_from = date_from.add(months=3)
                        date_to = date_to.add(months=3)

        config["date_from_transformed"], config["date_to_transformed"] = (
            date_from,
            date_to,
        )
        return config

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config = SourceWordstat.transform_config_date_range(config)
        config["group_by"] = config["group_by"]["group_type"]
        return config

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        config = self.transform_config(config)
        auth: HeadersAuthenticator = HeadersAuthenticator(curl_request=config["curl"])
        return [
            Search(
                authenticator=auth,
                config=config,
                date_from=config["date_from_transformed"],
                date_to=config["date_to_transformed"],
            )
        ]
