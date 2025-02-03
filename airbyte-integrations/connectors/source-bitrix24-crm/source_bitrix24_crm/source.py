#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#
import functools
import logging
import queue
from abc import ABC
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams.http import HttpStream

from .utils import get_config_date_range


# Basic full refresh stream
class Bitrix24CrmStream(HttpStream, ABC):
    """Base stream for bitrix24"""

    def __init__(self, config: Mapping[str, Any]):
        super().__init__(authenticator=None)
        self.config = config

    @property
    def url_base(self) -> str:
        return self.config["webhook_endpoint"]

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        return None

    def request_params(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> MutableMapping[str, Any]:
        params = {"select[]": ["*", "UF_*"]}
        if next_page_token:
            params["start"] = next_page_token["next"]
        return params

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        yield from response.json()["result"]


class ObjectListStream(Bitrix24CrmStream, ABC):
    """Base for bitrix24 object list endpoints"""

    primary_key = "ID"

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        last_response_data = response.json()
        if last_response_data.get("next"):
            return {"next": last_response_data.get("next")}
        else:
            return None

    @functools.lru_cache()
    def get_json_schema(self) -> Mapping[str, Any]:
        schema = super().get_json_schema()
        try:
            response_data = requests.get(
                self.url_base + self.path(), params=self.request_params()
            ).json()
            sample_data_keys = response_data["result"][0].keys()
        except Exception:
            raise Exception("Schema sample request returns bad data")

        for key in sample_data_keys:
            schema["properties"][key] = {"type": ["null", "string"]}

        return schema

    def request_params(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> MutableMapping[str, Any]:
        params = super().request_params(next_page_token=next_page_token, **kwargs)
        extended_params = {
            "filter[>=DATE_CREATE]": self.config["date_from"],
            "filter[<=DATE_CREATE]": self.config["date_to"],
        }
        params.update(extended_params)
        return params


class Leads(ObjectListStream):
    @functools.cached_property
    def fields(self) -> list[str]:
        """List of fields to request in response params select[]"""
        request = requests.get(self.url_base + "crm.lead.fields")
        return list(request.json()["result"].keys())

    def path(self, **kwargs) -> str:
        return "crm.lead.list"

    def request_params(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> MutableMapping[str, Any]:
        return super().request_params(next_page_token=next_page_token, **kwargs) | {
            "select[]": self.fields
        }


class Deals(ObjectListStream):
    def path(self, **kwargs) -> str:
        return "crm.deal.list"


class LeadsStatuses(Bitrix24CrmStream):
    primary_key = "STATUS_ID"

    def path(self, **kwargs) -> str:
        return "crm.status.list"

    def request_params(self, *args, **kwargs) -> MutableMapping[str, Any]:
        return {"filter[ENTITY_ID]": "SOURCE"}


class DealsStatuses(Bitrix24CrmStream):
    primary_key = "ID"

    def __init__(self, config: Mapping[str, Any]):
        super().__init__(config)
        self.deals_categories = queue.LifoQueue()
        self.init_request_passed = False
        self.current_category = None

    def path(self, **kwargs) -> str:
        if not self.init_request_passed:
            return "crm.dealcategory.list"
        return "crm.dealcategory.stage.list"

    def next_page_token(
        self, response: requests.Response, **kwargs
    ) -> Optional[Mapping[str, Any]]:
        if self.deals_categories.empty() and not self.init_request_passed:
            self.deals_categories.put({"ID": "0", "NAME": "Default"})
            for category in response.json()["result"]:
                self.deals_categories.put(category)
            self.init_request_passed = True
        try:
            self.current_category = self.deals_categories.get(block=False)
            return self.current_category
        except queue.Empty:
            self.current_category = None
            return None

    def request_params(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> MutableMapping[str, Any]:
        if not self.init_request_passed:
            return {"select[]": ["ID", "NAME"]}
        else:
            return {"entityTypeId": self.current_category["ID"]}

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        if not self.init_request_passed:
            return []
        stages = []
        for category_stage in response.json()["result"]:
            category_stage.update(
                {
                    "CATEGORY_ID": self.current_category["ID"],
                    "CATEGORY_NAME": self.current_category["NAME"],
                }
            )
        return stages


class SourceBitrix24Crm(AbstractSource):
    def check_connection(
        self, logger: logging.Logger, config: Mapping[str, Any]
    ) -> Tuple[bool, Optional[Any]]:
        leads_statuses_stream = self.streams(config)[-1]
        try:
            stream_params = leads_statuses_stream.request_params()
            test_response = requests.get(
                leads_statuses_stream.url_base + leads_statuses_stream.path(),
                params=stream_params,
            )
            if test_response.status_code != 200:
                return False, test_response.text
            else:
                return True, None
        except Exception as e:
            return False, e

    def streams(self, config: Mapping[str, Any]) -> List[Bitrix24CrmStream]:
        start_date, end_date = get_config_date_range(config)
        config["date_from"] = start_date.replace(hour=0, minute=0, second=0).strftime(
            "%Y/%m/%dT%H:%M:%S"
        )
        config["date_to"] = end_date.replace(hour=23, minute=59, second=59).strftime(
            "%Y/%m/%dT%H:%M:%S"
        )
        return [
            Leads(config),
            Deals(config),
            DealsStatuses(config),
            LeadsStatuses(config),
        ]
