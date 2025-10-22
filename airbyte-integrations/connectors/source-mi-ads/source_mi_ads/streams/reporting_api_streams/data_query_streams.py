from typing import Optional, Mapping, Any, Iterable
import pendulum
import requests

from ..base_stream import MiAdsStream
from ...auth import MiAdsAuthenticator
from .mappings import AdType, Dimension, ad_type_mapper, dimension_mapper


class DataQueryInterfaceOneStream(MiAdsStream):
    # https://global.e.mi.com/doc/reporting_api_guide.html#_1-interface-1

    primary_key = None
    http_method = "POST"
    page_size = 1000

    def path(self, *args, **kwargs) -> str:
        return "data/queryData"

    def __init__(
        self,
        authenticator: MiAdsAuthenticator,
        time_from: pendulum.DateTime,
        time_to: pendulum.DateTime,
        ad_type: AdType,
        dimensions: list[Dimension],
        account_ids: list[int] | None = None,
        ad_campaign_ids: list[int] | None = None,
    ):
        super().__init__(authenticator, time_from, time_to)
        self._ad_type = ad_type
        self._dimensions = dimensions
        self._account_ids = account_ids
        self._ad_campaign_ids = ad_campaign_ids
        self._page = 1

    def request_body_json(
        self,
        stream_state: Optional[Mapping[str, Any]],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Optional[Mapping[str, Any]]:
        data = {
            "page": self._page,
            "pageSize": self.page_size,
            "AdType": ad_type_mapper[self._ad_type],
            "dimensions": [dimension_mapper[d] for d in self._dimensions],
            "begin": self._time_from.in_tz("UTC").format("YYYY-MM-DDTHH:mm:ss.SSS[Z]"),
            "end": self._time_to.in_tz("UTC").format("YYYY-MM-DDTHH:mm:ss.SSS[Z]"),
            "lang": "en_US",
        }
        if self._account_ids:
            data["accountIds"] = self._account_ids
        if self._ad_campaign_ids:
            data["adCampaignIds"] = self._ad_campaign_ids
        # TODO: some more parameters may be added here
        return data

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        if response.json()["result"]["current"] < response.json()["result"]["pages"]:
            self._page += 1
            # Actually not used, just indicates that stream is not yet finished
            return {"page": self._page}
        return None

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        yield from response.json()["result"]["records"]
