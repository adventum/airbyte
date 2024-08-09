import itertools
import random
import time
from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional

import pendulum
import requests
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
        self.date_from: pendulum.datetime = date_from
        self.date_to: pendulum.datetime = date_to

        self.keywords: list[str] = config["keywords"]
        if not self.keywords:
            raise ValueError("Нет ключевых слов. Введите хотя бы одно")

        self.devices: list[str] = [device_translations.get(device) for device in config["devices"]]
        self.split_devices: bool = config["split_devices"]
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
        if self.split_devices:
            yield from (
                {"keyword": keyword, "devices": device}
                for keyword, device in itertools.product(self.keywords, self.devices)
            )
        else:
            yield from (
                {"keyword": keyword, "devices": ",".join(self.devices)} for keyword in self.keywords
            )

    def request_body_json(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        """Get request json"""
        data: dict[str, any] = {
            "currentDevice": stream_slice["devices"],
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

    def parse_response(
        self, response: requests.Response, stream_slice: Mapping[str, Any] = None, **kwargs
    ) -> Iterable[Mapping]:
        response_json: dict[str, any] = response.json()
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
                    record["devices"] = stream_slice["devices"]
                    yield record
