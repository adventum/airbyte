#
# Copyright (c) 2024 Airbyte, Inc., all rights reserved.
#
import functools
from abc import ABC
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import requests
from airbyte_cdk.sources.streams.http import HttpStream


# Basic full refresh stream
class Bitrix24CrmStream(HttpStream, ABC):
    """Base stream for bitrix24"""

    primary_key = "ID"

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

    @functools.lru_cache()
    def get_json_schema(self) -> Mapping[str, Any]:
        schema = super().get_json_schema()
        try:
            response_data = requests.get(
                self.url_base + self.path(), params=self.request_params(None)
            ).json()
            sample_data_keys = response_data["result"][0].keys()
        except Exception as e:
            raise e
        # except Exception:
        #     raise Exception(
        #         f"Schema sample request failed for stream {self.__class__.__name__}"
        #     )

        for key in sample_data_keys:
            schema["properties"][key] = {"type": ["null", "string"]}

        return schema


class ObjectListStream(Bitrix24CrmStream, ABC):
    """Base for bitrix24 object list endpoints"""

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        last_response_data = response.json()
        if last_response_data.get("next"):
            return {"next": last_response_data.get("next")}
        return None

    def request_params(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> MutableMapping[str, Any]:
        params = super().request_params(next_page_token)
        extended_params = {
            "filter[>=DATE_CREATE]": self.config["date_from"],
            "filter[<=DATE_CREATE]": self.config["date_to"],
        }
        params.update(extended_params)
        return params
