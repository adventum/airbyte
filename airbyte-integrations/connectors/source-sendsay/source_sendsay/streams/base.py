from abc import ABC, abstractmethod
from typing import Any, Mapping, MutableMapping, Optional

import pendulum
import requests
from airbyte_cdk.sources.streams.http import HttpStream


class SendsayStream(HttpStream, ABC):
    url_base = "https://api.sendsay.ru/general/api/v100/json/"
    http_method = "POST"

    def __init__(
        self,
        login: str,
        session: str,
        time_from: pendulum.DateTime | None = None,
        time_to: pendulum.DateTime | None = None,
    ) -> None:
        super().__init__(authenticator=None)
        self._login = login
        self._session = session
        self._time_from = time_from
        self._time_to = time_to

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        return None

    @property
    @abstractmethod
    def action_name(self) -> str:
        """Name of action in sendsay api"""
        ...

    @abstractmethod
    def request_body_json(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> MutableMapping[str, Any]:
        return {
            "action": self.action_name,
            "session": self._session,
        }

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

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> MutableMapping[str, Any]:
        return {}  # Body params only
