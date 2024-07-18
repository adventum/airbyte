import time
from abc import ABC, abstractmethod
import random
from json import JSONDecodeError
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import pendulum
import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.core import StreamData
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_protocol.models import SyncMode

from .auth import HeadersAuthenticator
from .translations import device_translations, region_translations


class WordstatStream(HttpStream, ABC):
    url_base = "https://wordstat.yandex.ru/wordstat/api/"

    def __init__(
        self,
        authenticator: HeadersAuthenticator,
        retry_count: int = 10,
    ):
        super().__init__(authenticator=authenticator)
        self._authenticator = authenticator
        self._retry_count: int = retry_count

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        return {}

    @abstractmethod
    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]: ...

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: Optional[List[str]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        stream_state: Optional[Mapping[str, Any]] = None,
    ) -> Iterable[StreamData]:
        """Get Wordstat API response"""
        attempts_count: int = 0
        waiting_start: int = 10

        body = self.request_body_json(stream_state, stream_slice)
        succeeded: bool = False

        while attempts_count < self._retry_count:
            try:
                response: requests.Response = requests.post(
                    url=self.url_base + self.path(), json=body, headers=self._authenticator.headers
                )
                if response.status_code == 400:
                    raise ValueError(
                        "Статус 400. Пользовательская конфигурация некорректна или же произошла ошибка в коде ее обработки"
                    )
                if response.status_code != 200:
                    raise ValueError(f"Status code is {response.status_code}")

                response.json()  # If got captcha, wordstat returns status 200, but json fails
            except JSONDecodeError:
                self.logger.warning("Wordstat выдал капчу")
                time.sleep(random.uniform(waiting_start, waiting_start + 10))
                waiting_start += 1
                attempts_count += 1
                continue
            else:
                succeeded = True
                break

        if succeeded:
            yield from self.parse_response(response=response, stream_slice=stream_slice)
        else:
            raise ValueError(
                f"Не удалось загрузить данные за {attempts_count} попыток. Если в логах коннектора сообщается о капче, попробуйте позже или замените curl запроса в конфиге"
            )


class Search(WordstatStream):
    primary_key = None

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "search"

    def __init__(
        self,
        authenticator: HeadersAuthenticator,
        config: Mapping[str, Any],
        date_from: pendulum.datetime,
        date_to: pendulum.datetime,
    ):
        super().__init__(authenticator=authenticator)
        self.group_by: str = config["group_by"]
        self.date_from = date_from
        self.date_to = date_to

        self.keywords: list[str] = config["keywords"]
        if not self.keywords:
            raise ValueError("Нет ключевых слов. Введите хотя бы одно")

        self.devices: list[str] = [device_translations.get(device) for device in config["devices"]]
        if not self.devices:
            raise ValueError("Не выбран ни один тип устройства. Выберите хотя бы один")

        self.regions: list[str] | str
        if config["region"]["region_type"] == "all":
            self.regions = "all"
        else:
            self.regions = [
                region_translations[region] for region in config["region"]["selected_regions"]
            ]
            self.regions.extend(config["region"].get("custom_regions", []))
            self.regions = list(set(self.regions))
            if len(self.regions) == 0:
                raise ValueError(
                    'Нет регионов. Добавьте хотя бы один из списка или введите свой код хотя бы для одного региона. Или выберите тип регионов "все"'
                )

    def stream_slices(
        self,
        *,
        sync_mode: SyncMode,
        cursor_field: Optional[List[str]] = None,
        stream_state: Optional[Mapping[str, Any]] = None,
    ) -> Iterable[Optional[Mapping[str, Any]]]:
        yield from ({"keyword": keyword} for keyword in self.keywords)

    def request_body_json(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        """Get request json"""
        data: dict[str, any] = {
            "currentDevice": ",".join(self.devices),
            "currentGraphType": self.group_by,
            "currentMapType": "all",
            "filters": {
                "region": "all",
                "tableType": "popular",
            },
            "searchValue": stream_slice["keyword"],
            "startDate": self.date_from.strftime("%d.%m.%Y"),
            "endDate": self.date_to.strftime("%d.%m.%Y"),
            "text": {  # Mostly useless, just copying wordstat request. Since there is no public api, this format may be helpful
                "graph": {
                    "title": "История запросов «»",
                    "disclaimer": f"Для каждой даты с {self.date_from.strftime('%d.%m.%Y')} по {self.date_to.strftime('%d.%m.%Y')} мы посчитали отношение числа запросов «» к среднему числу таких запросов за весь период.\\nГрафик показывает, как отличается дневное количество запросов от среднего значения.",
                },
                "map": {"title": "", "disclaimer": ""},
                "table": {"title": "", "disclaimer": ""},
            },
        }
        """Add regions if needed"""
        if isinstance(self.regions, list):
            data["filters"]["region"] = ",".join(map(str, self.regions))

        return data

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        response_json: dict[str, any] = response.json()
        stream_slice = kwargs["stream_slice"]
        graph_data = response_json.get("graph", {})
        if not graph_data:
            yield from []
        else:
            table_data = graph_data.get("tableData", [])
            if not table_data:
                yield from []
            else:
                for record in table_data:
                    record["absoluteValue"] = int(record["absoluteValue"].replace(" ", ""))
                    record["value"] = float(record["value"].replace(",", "."))
                    record["keyword"] = stream_slice["keyword"]
                    yield record


class SourceWordstat(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        auth: HeadersAuthenticator = HeadersAuthenticator(curl_request=config["curl"])

        today_date: pendulum.datetime = pendulum.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        keyword: str = (
            "Google Sheets"  # Random word combination not to use main ones to lower chances of getting captcha
        )
        new_config: dict[str, Any] = {
            "keywords": [keyword],
            "group_by": {"group_type": "day"},
            "devices": [config["devices"][0]],
            "region": {"region_type": "all"},
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
        if group_by == "day":  # No earlier than 60 days ago, no later than yesterday
            date_from = max(date_from, today_date.subtract(days=60))
            date_to = min(date_to, today_date.subtract(days=1))
            if (date_to - date_from).days < 2:
                date_from = date_from.subtract(days=1)
        elif (
            group_by == "week"
        ):  # Starts on monday, ends on sunday. No earlier than 2 years ago, no later than last sunday
            nearest_to_start_monday = (
                date_from.previous(pendulum.MONDAY)
                if date_from.day_of_week != pendulum.MONDAY
                else date_from
            )
            while nearest_to_start_monday < today_date.subtract(years=2):
                nearest_to_start_monday = nearest_to_start_monday.add(weeks=1)

            nearest_to_end_sunday = (
                date_to.next(pendulum.SUNDAY) if date_to.day_of_week != pendulum.SUNDAY else date_to
            )
            last_sunday = today_date.previous(pendulum.SUNDAY)
            while nearest_to_end_sunday > last_sunday:
                nearest_to_end_sunday = nearest_to_end_sunday.subtract(weeks=1)

            date_from, date_to = nearest_to_start_monday, nearest_to_end_sunday
        elif (
            group_by == "month"
        ):  # Starts with 1st day of month, ends with last, no later than last month
            nearest_to_start_first = date_from.start_of("month")
            four_years_ago = today_date.subtract(years=4)
            while nearest_to_start_first < four_years_ago:
                nearest_to_start_first = nearest_to_start_first.add(months=1).start_of("month")

            nearest_to_end_last = date_to.end_of("month")
            last_day_of_previous_month = today_date.subtract(months=1).end_of("month")
            while nearest_to_end_last > last_day_of_previous_month:
                nearest_to_end_last = nearest_to_end_last.subtract(months=1).end_of("month")

            date_from, date_to = nearest_to_start_first, nearest_to_end_last

        config["date_from_transformed"], config["date_to_transformed"] = date_from, date_to
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
