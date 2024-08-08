import logging
from abc import ABC

import requests
from airbyte_cdk.sources.streams.http import HttpStream

logger = logging.getLogger(__name__)


class YandexMetrikaStream(HttpStream, ABC):
    """
    Base for Yandex metrika streams
    Contains some base functions
    """

    def __init__(self, field_name_map: dict[str, str]):
        super().__init__(authenticator=None)
        self.field_name_map: dict[str, str] = field_name_map

    def replace_keys(self, data: dict[str, any]) -> None:
        """Replace all keys by field_name_map in given dict"""
        for key, value in self.field_name_map.items():
            if key in data:
                data[value] = data.pop(key)

    def make_test_request(self):
        test_params = self.request_params()
        test_params["limit"] = 1
        headers = self._authenticator.get_auth_header()
        return requests.get(self.url_base + self.path(), params=test_params, headers=headers)
