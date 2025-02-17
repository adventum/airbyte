import json
import random
import requests

from abc import ABC
from datetime import datetime
from typing import Any, Iterable, Mapping, MutableMapping, Optional

from airbyte_cdk.sources.streams.http import HttpStream


class UisStream(HttpStream, ABC):

    url_base: str = "https://dataapi.uiscom.ru/v2.0"
    http_method: str = "POST"
    api_endpoint: str | None = None

    def __init__(
        self,
        access_token: str,
        date_from: datetime,
        date_to: datetime,
        api_endpoint: str | None = None,
        stream_fields: list[str] | None = None,
    ):
        super().__init__()
        self.access_token = access_token
        self.date_from = date_from
        self.date_to = date_to
        self.random_request_id = self.create_random_request_id()
        self.api_endpoint = api_endpoint
        self.stream_fields = stream_fields

    @staticmethod
    def create_random_request_id():
        request_id = ''.join(str(random.randint(0, 9)) for _ in range(32))
        return request_id

    def request_body_json(
        self, stream_state: Mapping[str, any], stream_slice: Mapping[str, any] = None, next_page_token: Mapping[str, Any] = None
    ) -> MutableMapping[str, Any]:
        """
        Override this method in a child class
        if a different request body is needed in the new stream
        """
        body: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": self.random_request_id,
            "method": self.api_endpoint,
            "params": {
                "access_token": self.access_token,
                "date_from": self.date_from,
                "date_till": self.date_to,
                "fields": self.stream_fields,
            }
        }
        return body

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        """
        returns an iterable containing each record in the response
        """
        try:
            data = json.loads(response.text)
            if "error" in data:
                raise Exception(
                    f"Status code 200, but there are an API ERROR: {data['error']}. "
                    f"List of UIS errors: "
                    f"https://www.uiscom.ru/academiya/spravochnyj-centr/dokumentatsiya-api/data_api/"
                )
            else:
                result = data.get("result").get("data")
                for record in result:
                    if not record:
                        continue
                    else:
                        yield record

        except json.JSONDecodeError as e:
            print("JSON parsing error:", e)

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def request_headers(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> Mapping[str, Any]:
        return {
            "Content-Type": "application/json; charset=UTF-8"
        }
