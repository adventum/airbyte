#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping, Optional, List
from xmlrpc import client

from airbyte_cdk.sources.streams.core import StreamData, Stream
from airbyte_protocol.models import SyncMode


class SapeStream(Stream, ABC):
    url_base = "https://api.sape.ru/xmlrpc/"

    def __init__(self, client_: client.ServerProxy):
        super().__init__()
        self._client: client.ServerProxy = client_

    @abstractmethod
    def path(self, *args, **kwargs) -> str:
        ...

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: Optional[List[str]] = None,
        stream_slice: Optional[Mapping[str, Any]] = None,
        stream_state: Optional[Mapping[str, Any]] = None,
    ) -> Iterable[StreamData]:
        func = getattr(self._client.sape,
            self.path(stream_state=stream_state, stream_slice=stream_slice)
        )
        data = func()  # TODO: function arguments expected
        yield from data
        yield from []
