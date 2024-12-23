from typing import Optional, Mapping, Any

from .base_stream import SapeStream


class GetAvgPrices(SapeStream):
    """get_avg_prices method"""

    primary_key = None

    def path(
        self,
        *,
        stream_state: Optional[Mapping[str, Any]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> str:
        return "get_avg_prices"
