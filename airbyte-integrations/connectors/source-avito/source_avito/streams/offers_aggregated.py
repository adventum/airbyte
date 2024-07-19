from typing import Any, Iterable, Mapping, Optional

import pendulum
import requests
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator

from . import AvitoStream


class OffersAggregated(AvitoStream):
    http_method = "POST"
    primary_key = "id"

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return f"stats/v1/accounts/{self.user_id}/items"

    def __init__(
        self,
        authenticator: TokenAuthenticator,
        time_from: pendulum.datetime,
        time_to: pendulum.datetime,
        user_id: int,
        item_ids: list[int],
        period_grouping: str,
        fields: list[str]
    ):
        super().__init__(authenticator)
        self.time_from: pendulum.datetime = time_from
        self.time_to: pendulum.date = time_to
        self.user_id = user_id
        self.item_ids = item_ids
        self.period_grouping = period_grouping
        self.fields = fields

    @classmethod
    def check_config(cls, config: Mapping[str, Any]) -> tuple[bool, str]:
        for field_name in ["aggregated_offers_item_ids", "aggregated_offers_user_id", "aggregated_offers_period_grouping", "aggregated_offers_fields"]:
            if not config.get(field_name):
                return False, f"{cls.__name__} must have {field_name} value"

        return True, ""

    def request_json_body(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        """
        Request json body
        """

        data: dict[str, any] = {
            "dateFrom": self.time_from.date().isoformat(),
            "dateTo": self.time_to.date().isoformat(),
            "itemIds": self.item_ids,
            "periodGrouping": self.period_grouping,
            "fields": self.fields,
        }

        return data

    def get_json_schema(self) -> Mapping[str, Any]:
        schema = super().get_json_schema()
        for field in self.fields:
            schema["properties"][field] = {"type": ["integer", "null"]}
        return schema

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        response_json: dict[str, any] = response.json()

        if "error" in response_json:
            error_text: str = response_json["error"]["message"]
            self.logger.info(f"Request failed: {error_text}")
            raise RuntimeError("Failed to fetch data")

        if "result" not in response_json or "items" not in response_json["result"]:
            raise ValueError(response_json, response.request.body)

        for record in response_json["result"]["items"]:
            id_ = record["itemId"]
            for stat in record["stats"]:
                new_record: dict[str, any] = {
                    "id": id_,
                    "date": stat["date"],
                }
                for field in self.fields:
                    new_record[field] = stat.get(field)

                yield new_record

