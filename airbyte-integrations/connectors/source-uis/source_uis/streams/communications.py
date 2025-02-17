import json
import requests

from airbyte_cdk.sources.streams.core import package_name_from_class
from airbyte_cdk.sources.utils.schema_helpers import ResourceSchemaLoader

from datetime import datetime
from typing import Any, Iterable, Mapping, MutableMapping

from .base_stream import UisStream


class Communications(UisStream):
    primary_key = "report_id"
    api_endpoint = "get.communications"

    def __init__(
        self,
        access_token: str,
        date_from: datetime,
        date_to: datetime,
        report_id: int,
        fields: list[str],
    ):
        self.report_id = report_id
        self.fields = fields
        super().__init__(access_token, date_from, date_to, self.api_endpoint, self.fields)

    def path(self, *args, **kwargs) -> str:
        return ""

    @property
    def name(self) -> str:
        return f"communication_{str(self.report_id)}"

    def get_json_schema(self) -> Mapping[str, any]:
        schema = ResourceSchemaLoader(
            package_name_from_class(self.__class__)
        ).get_schema("communications")
        for field in self.fields:
            schema["properties"][field] = {"type": ["null", "string"]}
        return schema

    def request_body_json(
        self, stream_state: Mapping[str, any], stream_slice: Mapping[str, any] = None, next_page_token: Mapping[str, Any] = None
    ) -> MutableMapping[str, Any]:
        body: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": self.random_request_id,
            "method": self.api_endpoint,
            "params": {
                "access_token": self.access_token,
                "date_from": self.date_from,
                "date_till": self.date_to,
                "fields": self.fields,
                "report_id": int(self.report_id),
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
                        # We add report_id, because the stream needs a primary_key, so we add it
                        record = record | {"report_id": self.report_id}
                        yield record

        except json.JSONDecodeError as e:
            print("JSON parsing error:", e)
