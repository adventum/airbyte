#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from abc import ABC
from typing import Any, Mapping, MutableMapping, Optional

import requests
from airbyte_cdk.sources.streams.http import HttpStream


class YandexRealtyStream(HttpStream, ABC):
    url_base = "https://api.realty.yandex.net/2.0/"

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        return None

    @property
    def state(self) -> MutableMapping[str, Any]:
        """Get connector state (default from HttpStream)"""
        cursor = self.get_cursor()
        if cursor:
            return cursor.get_stream_state()  # type: ignore
        return self._state

    @state.setter
    def state(self, value: MutableMapping[str, Any]) -> None:
        """Set empty state as in old connectors"""
        value = {}
        cursor = self.get_cursor()
        if cursor:
            cursor.set_initial_state(value)
        self._state = value
