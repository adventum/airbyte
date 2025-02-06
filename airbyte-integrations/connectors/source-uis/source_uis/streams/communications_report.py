from .base_stream import UisStream

from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple


class CommunicationsReport(UisStream):

    primary_key = "customer_id"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        """

        """
        return "customers"
