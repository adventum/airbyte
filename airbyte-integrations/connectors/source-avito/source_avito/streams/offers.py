from typing import Any, Iterable, Mapping, Optional

import pendulum
import requests
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator

from . import AvitoStream


class Offers(AvitoStream):
    http_method = "GET"
    primary_key = "id"
    records_batch_size = 25
    page = 1

    def path(
        self,
        stream_state: Mapping[str, Any] = None,
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> str:
        return "core/v1/items"

    def __init__(
        self,
        authenticator: TokenAuthenticator,
        time_from: pendulum.datetime,
        time_to: pendulum.datetime,
        statuses: list[str] | None = None,
        category: int | None = None,
    ):
        super().__init__(authenticator)
        self.time_from: pendulum.datetime = time_from
        self.time_to: pendulum.date = time_to
        self.statuses = statuses
        self.category = category

        # Api for this stream does not support date_to filtering, only date_from
        # So connector should load some data from it after allowed time
        # Ids are int increment, so if id of any of the records if gte than this value
        # Then we have loaded all data and need to stop
        self.id_border: int | None = None

    @classmethod
    def check_config(cls, config: Mapping[str, Any]) -> tuple[bool, str]:
        # All fields are optional
        return True, ""

    def _load_oldest_forbidden_records(self):
        """Get records after date_from to identify self.id_border"""
        request_params = self.request_params(stream_state=None, stream_slice=None)
        request_params["updatedAtFrom"] = self.time_to.add(days=1).date().isoformat()
        request_params["page"] = 1
        request_params["per_page"] = 1

        response: requests.Response = requests.get(
            url=self.url_base + self.path(),
            headers=self.authenticator.get_auth_header(),
            params=request_params
        )
        response_json = response.json()
        ids: set[int] = {record["id"] for record in response_json["resources"]}
        self.id_border = min(ids)
        self.logger.info(f"Set id border: {self.id_border}")

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        # Sadly, Avito does not send any offer(item) timings, so we have to check create time for them separately
        response_json: dict[str, any] = response.json()
        if len(response_json["resources"]) < self.records_batch_size:
            return None

        if self.id_border is None:
            self._load_oldest_forbidden_records()

        # Loaded records later than date_to
        if self.id_border < any((record["id"] for record in response_json["resources"])):
            self.logger.info(f"Found id border in pagination")
            return None

        self.page += 1
        return {"page": self.page}

    def request_params(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        """
        Request parameters
        This stream uses request parameters, not json body
        """
        page: int = next_page_token["page"] if next_page_token else 1

        data: dict[str, any] = {
            "per_page": self.records_batch_size,
            "page": page,
            "updatedAtFrom": self.time_from.date().isoformat(),
        }
        if self.statuses:
            data["status"] = ",".join(self.statuses)

        if self.category:
            data["category"] = self.category
        self.logger.info(data)
        return data

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        response_json: dict[str, any] = response.json()

        if "error" in response_json:
            error_text: str = response_json["error"]["message"]
            self.logger.info(f"Request failed: {error_text}")
            raise RuntimeError("Failed to fetch data")

        if "resources" not in response_json:
            raise ValueError(response_json, response.request.body)

        if self.id_border is None:
            self._load_oldest_forbidden_records()

        for record in response_json["resources"]:
            if record["id"] < self.id_border:
                record["category_id"] = record["category"]["id"]
                record["category_name"] = record["category"]["name"]
                yield record
