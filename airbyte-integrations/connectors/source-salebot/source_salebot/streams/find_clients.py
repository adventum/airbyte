from typing import Optional, Mapping, Any, Iterable, Literal
import requests

from .base_stream import SalebotStream


class FindClients(SalebotStream):
    primary_key = None
    http_method = "POST"

    def __init__(
        self,
        api_key: str,
        q: str,
        include_all: bool = False,
        search_in: Literal["client", "order"] = "client",
    ) -> None:
        super().__init__(api_key, None, None)
        self._q = q
        self._include_all = include_all
        self._search_in = search_in

    def path(self, *args, **kwargs) -> str:
        return self._api_key + "/find_clients"

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        return None

    def request_body_json(
        self, next_page_token: Optional[Mapping[str, Any]] = None, *args, **kwargs
    ) -> Optional[Mapping[str, Any]]:
        data = {
            "q": self._q,
            "include_all": self._include_all,
        }
        # Client is default and i am not sure that this is a correct value
        # Order is correct for sure by api docs
        if self._search_in == "order":
            data["search_in"] = "order"
        return data

    def parse_response(
        self, response: requests.Response, *args, **kwargs
    ) -> Iterable[Mapping[str, Any]]:
        yield from ({"client_id": id_} for id_ in response.json()["client_ids"])
