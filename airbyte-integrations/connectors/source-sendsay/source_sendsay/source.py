from typing import Any, Mapping, Tuple

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from .utils import get_config_date_range
from .streams.universal_statistics import UniversalStatistics


# Source
class SourceSendsay(AbstractSource):
    url_base = "https://api.sendsay.ru/general/api/v100/json/"

    def check_connection(self, logger, config) -> Tuple[bool, Any]:
        try:
            session = self.get_session(config)
            url = f"{self.url_base}{config['login']}"
            r = requests.post(
                url,
                json={
                    "action": "pong",  # See Sendsay docs
                    "session": session,
                },
            )
            assert r.status_code == 200
            data = r.json()
            assert "sublogin" in data and data["sublogin"] == config["sublogin"]
            return True, None
        except Exception as e:
            return False, e

    def get_session(self, config) -> str:
        """Get session id used for all requests in sendsay"""
        login = config["login"]
        sub_login = config["sublogin"]
        password = config["password"]

        url = f"{self.url_base}{login}"
        r = requests.post(
            url,
            json={
                "action": "login",
                "login": login,
                "sublogin": sub_login,
                "passwd": password,
            },
        )
        return r.json()["session"]

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config["time_from_transformed"], config["time_to_transformed"] = (
            get_config_date_range(config)
        )
        # For future improvements
        return config

    def streams(self, config: Mapping[str, Any]) -> list[Stream]:
        config = self.transform_config(config)
        time_from = config["time_from_transformed"]
        time_to = config["time_to_transformed"]
        login = config["login"]
        fields = config["fields"]
        date_field = config["date_field"]
        session = self.get_session(config)
        fields = list(set(fields) | {date_field})

        universal_stat_stream = UniversalStatistics(
            login=login,
            session=session,
            fields=fields,
            date_field=date_field,
            time_from=time_from,
            time_to=time_to,
        )
        return [universal_stat_stream]
