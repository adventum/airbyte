from .base_stream import UisStream

from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple


class VisitorSessionsReport(UisStream):
    """
    TODO: Change class name to match the table/data source this stream corresponds to.
    """
    cursor_field = "start_date"

    primary_key = "employee_id"

    def path(self, **kwargs) -> str:

        return "employees"

    def stream_slices(self, stream_state: Mapping[str, Any] = None, **kwargs) -> Iterable[Optional[Mapping[str, any]]]:

        raise NotImplementedError("Implement stream slices or delete this method!")
