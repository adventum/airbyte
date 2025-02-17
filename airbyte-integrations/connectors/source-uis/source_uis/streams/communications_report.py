from .stream_fields import communications_report
from .base_stream import UisStream

from datetime import datetime


class CommunicationsReport(UisStream):
    primary_key: str = "id"
    api_endpoint: str = "get.communications_report"

    def __init__(
        self,
        access_token: str,
        date_from: datetime,
        date_to: datetime,
    ):
        super().__init__(access_token, date_from, date_to, self.api_endpoint, communications_report)

    def path(self, *args, **kwargs) -> str:
        return ""
