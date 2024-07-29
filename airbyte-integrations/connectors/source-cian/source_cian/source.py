from abc import ABC, abstractmethod
from typing import Iterable, Mapping, MutableMapping, Optional

import itertools
import pendulum
import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator
from airbyte_protocol.models import SyncMode


class CianStream(HttpStream, ABC):
    url_base = "https://public-api.cian.ru/"
    date_format: str = "%Y-%m-%d"

    @classmethod
    @abstractmethod
    def results_field(cls) -> str:
        """Cian streams have common format, but different result field"""
        raise NotImplementedError()

    def __init__(
        self,
        authenticator: TokenAuthenticator,
        date_from: pendulum.datetime,
        date_to: pendulum.datetime,
    ):
        super().__init__(authenticator)
        self.date_from: pendulum.datetime = date_from
        self.date_to: pendulum.datetime = date_to

    def request_params(
        self,
        stream_state: Mapping[str, any],
        stream_slice: Mapping[str, any] = None,
        next_page_token: Mapping[str, any] = None,
    ) -> MutableMapping[str, any]:
        return {}

    def next_page_token(self, response: requests.Response) -> Mapping[str, any] | None:
        return None

    def parse_response(self, response: requests.Response, stream_slice: Mapping[str, any] = None, **kwargs) -> Iterable[Mapping]:
        """
        :return: an iterable containing each record in the response
        """
        response_json: dict[str, any] = response.json()
        status: int = response.status_code
        if 200 <= status < 400:
            for record in response_json["result"][self.results_field]:
                record["date"] = stream_slice["load_date"]
                yield record
        else:
            error_text: str = response_json["result"]["message"]
            self.logger.info(f"Request failed with status {status}: {error_text}")
            raise RuntimeError("Failed to fetch data")


class BuilderCalls(CianStream):
    """Cian calls for building stream"""

    primary_key = "id"
    results_field = "calls"

    def __init__(
        self,
        authenticator: TokenAuthenticator,
        date_from: pendulum.datetime,
        date_to: pendulum.datetime,
        buildings_ids: list[int] | None = None,
    ):
        super().__init__(authenticator, date_from, date_to)
        self.buildings_ids: list[int] | None = buildings_ids

    def path(self, *args, **kwargs) -> str:
        return "v1/get-builder-calls/"

    def request_params(
        self, stream_slice: Mapping[str, any] = None, *args, **kwargs
    ) -> MutableMapping[str, any]:
        data: dict[str, any] = {"onDate": stream_slice["load_date"]}
        if stream_slice["building_id"] is not None:
            data["newbuildingId"] = stream_slice["building_id"]
        return data

    def stream_slices(
        self,
        *,
        sync_mode: SyncMode,
        cursor_field: list[str] | None = None,
        stream_state: Mapping[str, any] | None = None,
    ) -> Iterable[Mapping[str, any] | None]:
        # Calls stream supports all buildings (None) or only one building
        dates: list[pendulum.datetime] = [
            self.date_from.add(days=i) for i in range((self.date_to - self.date_from).days + 1)
        ]
        buildings_ids: list[int | None] = (
            self.buildings_ids if self.buildings_ids is not None else [None]
        )

        # Uses datetime isoformat date format!
        for building_id, date in itertools.product(buildings_ids, dates):
            yield {"load_date": date.isoformat(), "building_id": building_id}


class BuildingOfferStatistics(CianStream):
    """Stream for building offer statistics endpoint"""

    primary_key = "id"
    results_field = "items"

    def __init__(
        self,
        authenticator: TokenAuthenticator,
        date_from: pendulum.datetime,
        date_to: pendulum.datetime,
        buildings_ids: list[int] | None = None,
    ):
        super().__init__(authenticator, date_from, date_to)
        self.date_from: pendulum.datetime = date_from
        self.date_to: pendulum.datetime = date_to
        self.buildings_ids: list[int] | None = buildings_ids

    def path(self, *args, **kwargs) -> str:
        return "v1/get-newbuilding-offer-statistics/"

    def request_params(
        self, stream_slice: Mapping[str, any] = None, *args, **kwargs
    ) -> MutableMapping[str, any]:
        data: dict[str, any] = {"date": stream_slice["load_date"]}
        if stream_slice["buildings_ids"] is not None:
            data["newbuildingIds"] = stream_slice["buildings_ids"]
        return data

    def stream_slices(
        self,
        *,
        sync_mode: SyncMode,
        cursor_field: list[str] | None = None,
        stream_state: Mapping[str, any] | None = None,
    ) -> Iterable[Mapping[str, any] | None]:
        dates: list[pendulum.datetime] = [
            self.date_from.add(days=i) for i in range((self.date_to - self.date_from).days + 1)
        ]

        # Uses date isoformat!
        yield from (
            {"load_date": date.date().isoformat(), "buildings_ids": self.buildings_ids}
            for date in dates
        )


class SourceCian(AbstractSource):
    def check_connection(self, logger, config) -> tuple[bool, any]:
        today_date: pendulum.datetime = pendulum.now()
        try:
            test_stream = BuilderCalls(
                authenticator=self.get_auth(config), date_from=today_date, date_to=today_date
            )
            next(test_stream.read_records(
                sync_mode=SyncMode.full_refresh,
                stream_slice={"load_date": today_date.isoformat(), "building_id": None},
            ))
            return True, None
        except StopIteration:  # Just no data for today, but everything works just fine
            return True, None
        except Exception as ex:
            return False, ex

    @staticmethod
    def transform_config_date_range(config: Mapping[str, any]) -> Mapping[str, any]:
        date_range: Mapping[str, any] = config.get("date_range", {})
        date_range_type: str = date_range.get("date_range_type")

        date_from: Optional[pendulum.datetime] = None
        date_to: Optional[pendulum.datetime] = None

        # Meaning is date but storing time since later will use time
        today_date: pendulum.datetime = pendulum.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        if date_range_type == "custom_date":
            date_from = pendulum.parse(date_range["date_from"])
            date_to = pendulum.parse(date_range["date_to"])
        elif date_range_type == "from_start_date_to_today":
            date_from = pendulum.parse(date_range["date_from"])
            if date_range.get("should_load_today"):
                date_to = today_date
            else:
                date_to = today_date.subtract(days=1)
        elif date_range_type == "last_n_days":
            date_from = today_date.subtract(days=date_range.get("last_days_count"))
            if date_range.get("should_load_today"):
                date_to = today_date
            else:
                date_to = today_date.subtract(days=1)

        config["date_from_transformed"], config["date_to_transformed"] = date_from, date_to
        return config

    @staticmethod
    def transform_config(config: Mapping[str, any]) -> Mapping[str, any]:
        config = SourceCian.transform_config_date_range(config)

        if config["buildings_ids"]["buildings_ids_type"] == "all":
            config["buildings_ids"] = None
        else:
            config["buildings_ids"] = config["buildings_ids"].get("ids", [])

        return config

    @staticmethod
    def get_auth(config: Mapping[str, any]) -> TokenAuthenticator:
        return TokenAuthenticator(token=config["token"])

    def streams(self, config: Mapping[str, any]) -> list[Stream]:
        config = self.transform_config(config)
        auth = self.get_auth(config)
        return [
            BuilderCalls(
                authenticator=auth,
                date_from=config["date_from_transformed"],
                date_to=config["date_to_transformed"],
                buildings_ids=config["buildings_ids"],
            ),
            BuildingOfferStatistics(
                authenticator=auth,
                date_from=config["date_from_transformed"],
                date_to=config["date_to_transformed"],
                buildings_ids=config["buildings_ids"],
            ),
        ]
