#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#
from io import StringIO
import re
from unidecode import unidecode
import pandas as pd
import numpy as np
from abc import ABC
from hashlib import md5
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import pendulum
import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.core import package_name_from_class
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.utils.schema_helpers import ResourceSchemaLoader

from .auth import SipuniAuthenticator, CredentialsCraftAuthenticator
from .mappings import call_type_map, state_map


class SipuniStream(HttpStream, ABC):
    url_base: str = "https://sipuni.com/api/"
    http_method = "POST"

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def request_params(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        return {}

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        yield {}

    def translate_name(self, name: str):
        """Sipuni uses cyrillic column names that can cause problems when loading data"""
        name = str(name)
        name = re.sub("[^A-Za-z0-9\s]+", "", unidecode(name))
        name = name.strip()
        name = re.sub("[\s]", "_", name)
        name = re.sub("_{2,}", "_", name)
        return name.lower()


class CallStats(SipuniStream):
    primary_key = None
    date_format = "DD.MM.YYYY"

    def __init__(
        self,
        authenticator: SipuniAuthenticator,
        user: str,
        date_from: pendulum.date,
        date_to: pendulum.date,
        call_type: int = 0,
        state: int = 1,
        tree: str = "",
        show_tree_id: bool = False,
        from_number: str = "",
        to_number: str = "",
        show_numbers_ringed: bool = False,
        show_numbers_involved: bool = False,
        show_names: bool = False,
        show_outgoing_line: bool = False,
        to_answer: str = "",
        anonymous: bool = False,
        first_time: bool = False,
        show_dtmf_user_answers: bool = False,
    ):
        super().__init__(authenticator)
        self.raw_token: str = authenticator.raw_token
        self.user: str = user
        self.date_from: pendulum.date = date_from
        self.date_to: pendulum.date = date_to

        self.anonymous: bool = anonymous
        self.first_time: bool = first_time
        self.from_number: str = from_number
        self.request_state: int = state  # Airbyte CDK overrides stream.state
        self.to_answer: str = to_answer
        self.to_number: str = to_number
        self.tree: str = tree
        self.call_type: int = call_type
        self.show_tree_id: bool = show_tree_id
        self.show_numbers_ringed: bool = show_numbers_ringed
        self.show_numbers_involved: bool = show_numbers_involved
        self.show_names: bool = show_names
        self.show_outgoing_line: bool = show_outgoing_line
        self.show_dtmf_user_answers: bool = show_dtmf_user_answers

        # Caching explicitly json schema because read_records uses get_json_schema that makes extra requests
        self.stream_schema_json: dict[str, any] | None = None

    def path(
        self,
        **kwargs,
    ) -> str:
        return "statistic/export"

    def make_hash(self, date_from: pendulum.date, date_to: pendulum.date) -> str:
        # DO NOT REORDER!!! USE Sipuni api docs!!!
        hash_str = "+".join(
            map(
                str,
                [
                    int(self.anonymous),
                    int(self.show_dtmf_user_answers),
                    int(self.first_time),
                    date_from.format(self.date_format),
                    self.from_number,
                    int(self.show_names),
                    int(self.show_numbers_involved),
                    int(self.show_numbers_ringed),
                    int(self.show_outgoing_line),
                    int(self.show_tree_id),
                    self.request_state,
                    date_to.format(self.date_format),
                    self.to_answer,
                    self.to_number,
                    self.tree,
                    self.call_type,
                    self.user,
                    self.raw_token,
                ],
            )
        )
        return md5(hash_str.encode("utf-8")).hexdigest()

    def request_params(self, **kwargs) -> MutableMapping[str, Any]:
        params = {
            "user": self.user,
            "from": self.date_from.format(self.date_format),
            "to": self.date_to.format(self.date_format),
            "type": self.call_type,
            "state": self.request_state,
            "tree": self.tree,
            "showTreeId": int(self.show_tree_id),
            "fromNumber": self.from_number,
            "toNumber": self.to_number,
            "numbersRinged": int(self.show_numbers_ringed),
            "numbersInvolved": int(self.show_numbers_involved),
            "names": int(self.show_names),
            "outgoingLine": int(self.show_outgoing_line),
            "toAnswer": self.to_answer,
            "anonymous": int(self.anonymous),
            "firstTime": int(self.first_time),
            "dtmfUserAnswers": int(self.show_dtmf_user_answers),
            "hash": self.make_hash(date_from=self.date_from, date_to=self.date_to),
        }
        return params

    def make_test_request(self, **kwargs) -> requests.Response:
        date = pendulum.now().subtract(days=1).date()

        params = self.request_params(**kwargs) | {
            "from": date.format(self.date_format),
            "to": date.format(self.date_format),
            "hash": self.make_hash(date_from=date, date_to=date),
        }
        return requests.post(url=self.url_base + self.path(), params=params)

    def get_json_schema(self) -> Mapping[str, any]:
        if not self.stream_schema_json:
            schema = ResourceSchemaLoader(package_name_from_class(self.__class__)).get_schema("call_stats")

            test_response = self.make_test_request()
            if test_response.status_code > 204:
                raise Exception(f"Failed to fetch data. Response got status {test_response.status_code}")

            data = test_response.content.decode("utf-8-sig")
            df: pd.DataFrame = pd.read_csv(StringIO(data), delimiter=";", low_memory=False)
            df.rename(columns={old_name: self.translate_name(old_name) for old_name in df.columns}, inplace=True)
            types: dict[str, np.dtype] = dict(df.dtypes)
            for col_name, col_type in types.items():
                if isinstance(col_type, np.dtypes.IntDType):
                    schema["properties"][col_name] = {"type": ["null", "integer"]}
                elif isinstance(col_type, np.dtypes.BoolDType):
                    schema["properties"][col_name] = {"type": ["null", "boolean"]}
                elif (
                    isinstance(col_type, np.dtypes.Float64DType)
                    or isinstance(col_type, np.dtypes.Float16DType)
                    or isinstance(col_type, np.dtypes.Float32DType)
                ):
                    schema["properties"][col_name] = {"type": ["null", "number"]}
                else:
                    schema["properties"][col_name] = {"type": ["null", "string"]}
            self.stream_schema_json = schema
        return self.stream_schema_json

    def parse_response(self, response: requests.Response, *args, **kwargs) -> Iterable[Mapping]:
        if response.status_code > 204:
            raise Exception(f"Failed to fetch data. Response got status {response.status_code}")
        data = response.content.decode("utf-8-sig")
        df: pd.DataFrame = pd.read_csv(StringIO(data), delimiter=";", low_memory=False)
        df = df.replace(np.nan, None)
        df.rename(columns={old_name: self.translate_name(old_name) for old_name in df.columns}, inplace=True)
        yield from df.to_dict(orient="records")


# Source
class SourceSipuni(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        config = self.transform_config(config)
        auth: SipuniAuthenticator | CredentialsCraftAuthenticator = self.get_authenticator(config)
        call_stat_stream: CallStats = CallStats(
            authenticator=auth,
            user=config["user"],
            date_from=config["date_from_transformed"],
            date_to=config["date_to_transformed"],
        )
        test_response = call_stat_stream.make_test_request()
        if test_response.status_code > 204:
            return False, f"Failed to fetch data. Response got status {test_response.status_code}"

        try:
            data = test_response.content.decode("utf-8-sig")
            pd.read_csv(StringIO(data), delimiter=";", low_memory=False)
        except Exception as ex:
            return False, str(ex)
        return True, None

    @staticmethod
    def transform_config_date_range(config: Mapping[str, Any]) -> Mapping[str, Any]:
        date_range: Mapping[str, Any] = config.get("date_range", {})
        date_range_type: str = date_range.get("date_range_type")

        date_from: Optional[pendulum.datetime] = None
        date_to: Optional[pendulum.datetime] = None

        # Meaning is date but storing time since later will use time
        today_date: pendulum.datetime = pendulum.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if date_range_type == "custom_date":
            date_from = pendulum.parse(date_range["date_from"])
            date_to = pendulum.parse(date_range["date_to"])
        elif date_range_type == "from_start_date_to_today":
            date_from = pendulum.parse(date_range["date_from"])
            if date_range.get("should_load_today"):
                date_to = today_date
            else:
                date_to = today_date.subtract(days=1)
        elif date_range_type == "last_n_days":
            date_from = today_date.subtract(days=date_range.get("last_days_count"))
            if date_range.get("should_load_today"):
                date_to = today_date
            else:
                date_to = today_date.subtract(days=1)

        config["date_from_transformed"], config["date_to_transformed"] = date_from.date(), date_to.date()
        return config

    @staticmethod
    def transform_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config = SourceSipuni.transform_config_date_range(config)
        config["call_type"] = call_type_map[config["type"]]
        config["state"] = state_map[config["state"]]

        return config

    @staticmethod
    def get_authenticator(config: Mapping[str, Any]) -> SipuniAuthenticator | CredentialsCraftAuthenticator:
        """
        Get authenticator instance.

        :param config: user input configuration as defined in the connector spec.
        """
        auth_type = config["credentials"]["auth_type"]
        if auth_type == "access_token_auth":
            auth = SipuniAuthenticator(token=config["credentials"]["access_token"])
        elif auth_type == "credentials_craft_auth":
            auth = CredentialsCraftAuthenticator(
                credentials_craft_host=config["credentials"]["credentials_craft_host"],
                credentials_craft_token=config["credentials"]["credentials_craft_token"],
                credentials_craft_token_id=config["credentials"]["credentials_craft_token_id"],
            )
        else:
            raise Exception(
                f"Invalid Auth type {auth_type}. Available: access_token_auth and credentials_craft_auth",
            )
        return auth

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        config = self.transform_config(config)
        auth: SipuniAuthenticator | CredentialsCraftAuthenticator = self.get_authenticator(config)
        call_stat_stream: CallStats = CallStats(
            authenticator=auth,
            user=config["user"],
            date_from=config["date_from_transformed"],
            date_to=config["date_to_transformed"],
            call_type=config.get("call_type", 0),
            state=config.get("state", 1),
            tree=config.get("tree", ""),
            show_tree_id=config.get("show_tree_id", False),
            from_number=config.get("from_number", ""),
            to_number=config.get("to_number", ""),
            show_numbers_ringed=config.get("show_numbers_ringed", False),
            show_numbers_involved=config.get("show_numbers_involved", False),
            show_names=config.get("show_names", False),
            show_outgoing_line=config.get("show_outgoing_line", False),
            to_answer=config.get("to_answer", ""),
            anonymous=config.get("anonymous", False),
            first_time=config.get("first_time", False),
            show_dtmf_user_answers=config.get("dtmf_user_answers", False),
        )
        return [call_stat_stream]
