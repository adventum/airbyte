from datetime import datetime

from .stream_fields import visitor_sessions_report
from .base_stream import UisStream


class VisitorSessionsReport(UisStream):
    primary_key = "id"
    api_endpoint = "get.visitor_sessions_report"

    def __init__(
        self,
        access_token: str,
        date_from: datetime,
        date_to: datetime,
    ):
        super().__init__(access_token, date_from, date_to, self.api_endpoint, visitor_sessions_report)

    def path(self, *args, **kwargs) -> str:
        return ""

