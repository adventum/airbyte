#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping, Optional, List
from xmlrpc import client

import pendulum
from airbyte_cdk.sources.streams.core import StreamData, Stream
from airbyte_protocol.models import SyncMode


class SapeXMLStream(Stream, ABC):
    url_base = "https://api.sape.ru/xmlrpc/?rtb=1"
    base_path = "sape"

    def __init__(
        self,
        client_: client.ServerProxy,
        start_date: pendulum.Date | None = None,
        end_date: pendulum.Date | None = None,
    ):
        super().__init__()
        self._client: client.ServerProxy = client_
        self._start_date: pendulum.Date | None = start_date
        self._end_date: pendulum.Date | None = end_date

    @abstractmethod
    def path(self, *args, **kwargs) -> str: ...

    @abstractmethod
    def args(self) -> list[Any] | None:
        """
        Function arguments in list
        Airbyte standard dicts can't be used because of xmlrpc
        """

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: Optional[List[str]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        stream_state: Optional[Mapping[str, Any]] = None,
    ) -> Iterable[StreamData]:
        func = getattr(
            getattr(self._client, self.base_path),
            self.path(),
        )
        if args := self.args() is not None:
            data = func(*args)
        else:
            data = func()

        yield from data
