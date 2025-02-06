from .base_stream import UisStream

from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple


class Communications(UisStream):

    state_checkpoint_interval = None

    @property
    def cursor_field(self) -> str:

        return []

    def get_updated_state(self, current_stream_state: MutableMapping[str, Any], latest_record: Mapping[str, Any]) -> Mapping[str, Any]:

        return {}
