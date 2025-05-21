import time
from datetime import datetime
from logging import getLogger

import requests

from .types import Authenticator

logger = getLogger("airbyte")

DATE_FORMAT = "%Y-%m-%d"


class ReportCreator:
    def __init__(
        self,
        publisher_id: str,
        campaign_ids: list[str],
        report_endpoint: str,
        msk_date_from: datetime,
        msk_date_to: datetime,
        traffic_source: str = "total",
        authenticator: Authenticator = None,
    ):
        self.publisher_id = publisher_id
        self.campaign_ids = campaign_ids
        self.report_endpoint = report_endpoint
        self.msk_date_from = msk_date_from
        self.msk_date_to = msk_date_to
        self.traffic_source = traffic_source
        self.authenticator = authenticator
        self.report_id = None
        self.auth_headers = self.authenticator.get_auth_header()

    def create_report(self) -> str:
        url = (
            f"https://promopages.yandex.ru/api/promo/v1/reports/{self.report_endpoint}"
        )
        payload = {
            "publisherId": self.publisher_id,
            "campaignIds": self.campaign_ids,
            "mskDateFrom": datetime.strftime(self.msk_date_from, DATE_FORMAT),
            "mskDateTo": datetime.strftime(self.msk_date_to, DATE_FORMAT),
            "trafficSource": self.traffic_source,
        }
        logger.info(f"Creating report {payload}...")
        response = requests.post(url, json=payload, headers=self.auth_headers)
        response.raise_for_status()
        logger.info(f"Report {response.text} created")
        self.report_id = response.json().get("reportId")
        return self.report_id

    def wait_for_report(self) -> None:
        url = f"https://promopages.yandex.ru/api/promo/v1/reports/{self.report_id}"
        params = {"format": "json"}
        logger.info(f"Waiting for report {self.report_id}...")
        while True:
            latest_response = requests.get(
                url,
                params=params,
                headers=self.auth_headers,
                stream=True,
            )
            match latest_response.status_code:
                case 202:
                    logger.info(f"Report {self.report_id} is ready")
                    return
                case 429:
                    logger.info("Too many requests. Waiting 20 seconds...")
                    time.sleep(20)
                case _:
                    latest_response.raise_for_status()
                    # Raise exceptions if status directs to error
                    logger.info(
                        f"Report {self.report_id} is not ready yet. Waiting 40 seconds..."
                    )
                    time.sleep(40)
