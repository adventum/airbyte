from __future__ import annotations

import time
from abc import ABC
from datetime import date
from typing import Type, Mapping, Any, Dict, List, Iterable, Optional, Iterator

import requests
from airbyte_cdk.models import SyncMode
from airbyte_cdk.sources.streams import Stream
from requests.exceptions import ChunkedEncodingError, JSONDecodeError

from source_wildberries_ads.schemas.autostat import AdsAutoStat
from source_wildberries_ads.schemas.campaigns import AdsCampaign
from source_wildberries_ads.schemas.cost_history import AdsCostHistoryStat
from source_wildberries_ads.schemas.fullstat import AdsFullStat
from source_wildberries_ads.schemas.seacatstat import AdsSeaCatStat
from source_wildberries_ads.schemas.words import AdsWordsStat
from source_wildberries_ads.types import WildberriesCredentials, IsSuccess, Message, SchemaT
from source_wildberries_ads.utils import chunks


def check_ads_stream_connection(credentials: WildberriesCredentials, campaign_id: int | None) -> tuple[IsSuccess, Optional[Message]]:
    if campaign_id:
        url = f"https://advert-api.wb.ru/adv/v1/stat/words?id={campaign_id}"
    else:
        url = "https://advert-api.wb.ru/adv/v1/promotion/count"
    headers = {"Authorization": credentials["api_key"]}
    try:
        response = requests.get(url, headers=headers)
        if 200 <= response.status_code < 300:
            return True, None
        elif response.status_code == 400:
            if campaign_id:
                return False, f"Campaign not found by campaign ID. Response status code: {response.status_code}"
            return False, f"Response status code: {response.status_code}. Body: {response.text}"
        elif response.status_code == 401:
            return False, f"Invalid ads API key. Response status code: {response.status_code}. Body: {response.text}"
        else:
            return False, f"Response status code: {response.status_code}. Body: {response.text}"
    except Exception as e:
        return False, str(e)


def get_campaign_ids(headers: dict, only_campaign_type: int = None) -> Iterator[int]:
    attempts_count = 0
    while attempts_count < 3:
        try:
            response = requests.get("https://advert-api.wb.ru/adv/v1/promotion/count", headers=headers)
        except ChunkedEncodingError:
            time.sleep(20)
            continue
        if response.status_code == 200:
            if records := response.json().get("adverts"):
                for campaign_group in records:
                    if only_campaign_type and only_campaign_type != campaign_group.get("type"):
                        continue
                    for campaign in campaign_group.get("advert_list", []):
                        yield campaign["advertId"]
            return
        elif response.status_code == 204:
            return
        elif response.status_code > 500:
            time.sleep(20)
            continue
        elif response.status_code in (408, 429):
            attempts_count += 1
            if attempts_count < 3:
                time.sleep(20)  # Wait for Wildberries rate limits
            else:
                raise Exception(f"Failed to get campaigns from Wildberries API after 3 attempts due to rate limits")
        else:
            raise Exception(f"Status code: {response.status_code}. Body: {response.text}")


class AdsStream(Stream, ABC):
    SCHEMA: Type[SchemaT] = NotImplemented
    URL: str = NotImplemented
    RATE_LIMIT: int = NotImplemented  # requests/min

    def __init__(self, credentials: WildberriesCredentials, campaign_id: int | None):
        self.credentials = credentials
        self.campaign_id = campaign_id
        self.campaigns_ids: list[int] = []

    @property
    def primary_key(self) -> None:
        return None

    def get_json_schema(self) -> Mapping[str, Any]:
        return self.SCHEMA.schema()

    @property
    def url(self) -> str:
        return self.URL + f"?id={self.campaign_id}"

    @property
    def timeout(self) -> float:
        return 60 / self.RATE_LIMIT

    @property
    def headers(self) -> Dict:
        return {"Authorization": self.credentials["api_key"]}

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_slice: Mapping[str, Any] = None,
        stream_state: Mapping[str, Any] = None,
    ) -> Iterable[Mapping[str, Any]]:
        if self.campaign_id:
            yield from self._get_campaign_data()
            return

        self._get_campaigns()
        for campaign_id in self.campaigns_ids:
            print(f"Running {self.__class__.__name__} for campaign #{campaign_id}")
            self.campaign_id = campaign_id
            time.sleep(self.timeout)
            yield from self._get_campaign_data()

    def _get_campaigns(self) -> None:
        for campaign_id in get_campaign_ids(headers=self.headers):
            self.campaigns_ids.append(campaign_id)

    def _get_campaign_data(self) -> Iterable[Mapping[str, Any]]:
        attempts_count = 0
        while attempts_count < 3:
            try:
                response = requests.get(self.url, headers=self.headers)
            except ChunkedEncodingError:
                print(f"Chunked EncodingError, sleeping for 20 sec...")
                time.sleep(20)
                continue
            if response.status_code == 200:
                try:
                    if record := response.json():
                        yield self.SCHEMA(**record).dict()
                except JSONDecodeError:
                    pass
                return
            elif response.status_code == 204:
                return
            elif response.status_code > 500:
                print(f"{response.status_code} error, sleeping for 20 sec...")
                time.sleep(20)
                continue
            elif response.status_code in (408, 429):
                attempts_count += 1
                if attempts_count < 3:
                    print(f"{response.status_code} error, sleeping for 20 sec...")
                    time.sleep(20)  # Wait for Wildberries rate limits
                else:
                    raise Exception(f"Failed to load data from Wildberries API after 3 attempts due to rate limits")
            else:
                raise Exception(f"Status code: {response.status_code}. Body: {response.text}")


class WordsStatStream(AdsStream):
    SCHEMA: Type[AdsWordsStat] = AdsWordsStat
    URL: str = "https://advert-api.wb.ru/adv/v1/stat/words"
    RATE_LIMIT: int = 240


class FullStatStream(AdsStream):
    SCHEMA: Type[AdsFullStat] = AdsFullStat
    URL: str = "https://advert-api.wb.ru/adv/v1/fullstat"
    RATE_LIMIT: int = 10

    def __init__(self, credentials: WildberriesCredentials, campaign_id: int | None, date_from: date | None, date_to: date | None):
        super().__init__(credentials, campaign_id)
        self.date_from = date_from
        self.date_to = date_to

    @property
    def url(self) -> str:
        url = self.URL + f"?id={self.campaign_id}"
        if self.date_from:
            url += f"&begin={self.date_from.strftime('%Y-%m-%d')}"
        if self.date_to:
            url += f"&end={self.date_to.strftime('%Y-%m-%d')}"
        return url


class AutoStatStream(AdsStream):
    SCHEMA: Type[AdsAutoStat] = AdsAutoStat
    URL: str = "https://advert-api.wb.ru/adv/v1/auto/stat"
    RATE_LIMIT: int = 10

    def _get_campaigns(self) -> None:
        for campaign_id in get_campaign_ids(headers=self.headers, only_campaign_type=8):  # Автоматическая кампания
            self.campaigns_ids.append(campaign_id)


class SeaCatStatStream(AdsStream):
    SCHEMA: Type[AdsSeaCatStat] = AdsSeaCatStat
    URL: str = "https://advert-api.wb.ru/adv/v1/seacat/stat"
    RATE_LIMIT: int = 60


class AdsCampaignStream(Stream):
    SCHEMA: Type[AdsCampaign] = AdsCampaign
    URL: str = "https://advert-api.wb.ru/adv/v1/promotion/adverts"

    def __init__(self, credentials: WildberriesCredentials):
        self.credentials = credentials
        self.campaigns_ids: list[int] = []

    @property
    def primary_key(self) -> None:
        return None

    def get_json_schema(self) -> Mapping[str, Any]:
        return self.SCHEMA.schema()

    @property
    def headers(self) -> Dict:
        return {"Authorization": self.credentials["api_key"]}

    def _get_campaigns(self) -> None:
        for campaign_id in get_campaign_ids(headers=self.headers):
            self.campaigns_ids.append(campaign_id)

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_slice: Mapping[str, Any] = None,
        stream_state: Mapping[str, Any] = None,
    ) -> Iterable[Mapping[str, Any]]:
        self._get_campaigns()
        for chunk in chunks(self.campaigns_ids, 50):
            attempts_count = 0
            while attempts_count < 3:
                try:
                    response = requests.post(self.URL, json=chunk, headers=self.headers)
                except ChunkedEncodingError:
                    time.sleep(20)
                    continue
                if response.status_code == 200:
                    if records := response.json():
                        for record in records:
                            yield self.SCHEMA(**record).dict()
                    break
                elif response.status_code == 204:
                    break
                elif response.status_code > 500:
                    time.sleep(20)
                    continue
                elif response.status_code in (408, 429):
                    attempts_count += 1
                    if attempts_count < 3:
                        time.sleep(20)  # Wait for Wildberries rate limits
                    else:
                        raise Exception(f"Failed to load data from Wildberries API after 3 attempts due to rate limits")
                else:
                    raise Exception(f"Status code: {response.status_code}. Body: {response.text}")


class AdsCostHistoryStream(Stream):
    SCHEMA: Type[AdsCostHistoryStat] = AdsCostHistoryStat
    URL: str = "https://advert-api.wb.ru/adv/v1/upd"

    def __init__(self, credentials: WildberriesCredentials, date_from: date, date_to: date):
        self.credentials = credentials
        self.date_from = date_from
        self.date_to = date_to

    @property
    def primary_key(self) -> None:
        return None

    def get_json_schema(self) -> Mapping[str, Any]:
        return self.SCHEMA.schema()

    @property
    def url(self) -> str:
        return self.URL + f"?from={self.date_from.strftime('%Y-%m-%d')}&to={self.date_to.strftime('%Y-%m-%d')}"

    @property
    def headers(self) -> Dict:
        return {"Authorization": self.credentials["api_key"]}

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_slice: Mapping[str, Any] = None,
        stream_state: Mapping[str, Any] = None,
    ) -> Iterable[Mapping[str, Any]]:
        attempts_count = 0
        while attempts_count < 3:
            try:
                response = requests.get(self.url, headers=self.headers)
            except ChunkedEncodingError:
                time.sleep(20)
                continue
            if response.status_code == 200:
                try:
                    if records := response.json():
                        for record in records:
                            yield self.SCHEMA(**record).dict()
                except JSONDecodeError:
                    pass
                return
            elif response.status_code == 204:
                return
            elif response.status_code > 500:
                time.sleep(20)
                continue
            elif response.status_code in (408, 429):
                attempts_count += 1
                if attempts_count < 3:
                    time.sleep(20)  # Wait for Wildberries rate limits
                else:
                    raise Exception(f"Failed to load data from Wildberries API after 3 attempts due to rate limits")
            else:
                raise Exception(f"Status code: {response.status_code}. Body: {response.text}")
