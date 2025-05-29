#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#


from abc import ABC
from datetime import datetime, timedelta
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple, Dict

import requests
from .auth import CredentialsCraftAuthenticator
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from random import randint
from .utils import (
    get_yesterday_datetime,
    difference_in_days_between_two_datetimes,
)
import json


# Basic full refresh stream
class ComagicStream(HttpStream, ABC):
    url_base = "https://dataapi.comagic.ru/v2.0"
    http_method = "POST"

    def __init__(
        self,
        access_token: str,
        config: Mapping[str, Any] = {},
    ):
        super().__init__(authenticator=None)
        self.config = config
        self.access_token = access_token
        self.records_offset = 10000

    def next_page_token(
        self, response: requests.Response
    ) -> Optional[Mapping[str, Any]]:
        if not response:
            return {"offset": 0}
        last_response_records_len = len(response.json()["result"]["data"])
        if (
            last_response_records_len < 1
            or last_response_records_len < self.records_offset
        ):
            return None
        last_request_data = json.loads(response.request.body)
        return {"offset": last_request_data["params"]["offset"] + self.records_offset}

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = {
            "jsonrpc": "2.0",
            "id": randint(1000000, 999999999),
            "params": {
                "access_token": self.access_token,
                "offset": next_page_token["offset"] if next_page_token else 0,
                "limit": self.records_offset,
                "date_from": self.config["prepared_date_range"]["date_from"],
                "date_till": self.config["prepared_date_range"]["date_to"],
            },
        }
        return data

    def parse_response(
        self, response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        try:
            return map(self.add_constants_to_record, response.json()["result"]["data"])
        except Exception as ex:
            print('bad_url', response.url)
            print('bad_body', response.request.body)
            print('bad_response', response.text)
            raise Exception(f"There was an error while parsing response: {ex}")

    def path(self, **kwargs) -> str:
        return ""

    def add_constants_to_record(self, record):
        constants = {
            "__productName": self.config.get("product_name"),
            "__clientName": self.config.get("client_name"),
        }
        constants.update(json.loads(self.config.get("custom_json", "{}")))
        record.update(constants)
        return record

    def get_json_schema(self):
        schema = super().get_json_schema()
        extra_properties = ["__productName", "__clientName"]
        custom_keys = json.loads(self.config.get("custom_json", "{}")).keys()
        extra_properties.extend(custom_keys)
        for key in extra_properties:
            schema["properties"][key] = {"type": ["null", "string"]}

        return schema


class CallLegsReport(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.communications_report",
        }
        data.update(stream_specific_data)
        return data


class CallsReport(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.calls_report",
        }
        data["params"].update(
            {
                "fields": [
                    "id",
                    "start_time",
                    "finish_time",
                    "virtual_phone_number",
                    "is_transfer",
                    "finish_reason",
                    "direction",
                    "source",
                    "communication_number",
                    "communication_page_url",
                    "communication_id",
                    "communication_type",
                    "is_lost",
                    "cpn_region_id",
                    "cpn_region_name",
                    "wait_duration",
                    "total_wait_duration",
                    "lost_call_processing_duration",
                    "talk_duration",
                    "clean_talk_duration",
                    "total_duration",
                    "postprocess_duration",
                    "ua_client_id",
                    "ym_client_id",
                    "sale_date",
                    "sale_cost",
                    "search_query",
                    "search_engine",
                    "referrer_domain",
                    "referrer",
                    "entrance_page",
                    "gclid",
                    "yclid",
                    "ymclid",
                    "ef_id",
                    "channel",
                    "site_id",
                    "site_domain_name",
                    "campaign_id",
                    "campaign_name",
                    "visit_other_campaign",
                    "visitor_id",
                    "person_id",
                    "visitor_type",
                    "visitor_session_id",
                    "visits_count",
                    "visitor_first_campaign_id",
                    "visitor_first_campaign_name",
                    "visitor_city",
                    "visitor_region",
                    "visitor_country",
                    "visitor_device",
                    "last_answered_employee_id",
                    "last_answered_employee_full_name",
                    "last_answered_employee_rating",
                    "first_answered_employee_id",
                    "first_answered_employee_full_name",
                    "scenario_id",
                    "scenario_name",
                    "call_api_external_id",
                    "call_api_request_id",
                    "contact_phone_number",
                    "contact_full_name",
                    "contact_id",
                    "utm_source",
                    "utm_medium",
                    "utm_term",
                    "utm_content",
                    "utm_campaign",
                    "openstat_ad",
                    "openstat_campaign",
                    "openstat_service",
                    "openstat_source",
                    "eq_utm_source",
                    "eq_utm_medium",
                    "eq_utm_term",
                    "eq_utm_content",
                    "eq_utm_campaign",
                    "eq_utm_referrer",
                    "eq_utm_expid",
                    "attributes",
                    "call_records",
                    "voice_mail_records",
                    "tags",
                    "visitor_custom_properties",
                    "employees",
                    "scenario_operations",
                ],
            },
        )
        data.update(stream_specific_data)
        return data


class CampaignDailyStat(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.campaign_daily_stat",
        }
        data["params"].update(
            {
                "site_id": self.config["site_id"],
            },
        )
        data.update(stream_specific_data)
        return data


class ChatMessagesReport(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.chat_messages_report",
        }
        data.update(stream_specific_data)
        data["params"].update(
            {"site_id": self.config["site_id"], "chat_id": self.config["chat_id"]},
        )
        return data


class ChatsReport(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.chats_report",
        }
        data.update(stream_specific_data)
        return data


class CommunicationsReport(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.communications_report",
        }
        data.update(stream_specific_data)
        return data


class CtAcSummaryReport(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.ct_ac_summary_report",
        }
        data.update(stream_specific_data)
        data["params"].update(
            {"site_id": self.config["site_id"]},
        )
        return data


class CtSummaryReport(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.ct_summary_report",
        }
        data.update(stream_specific_data)
        return data


class EmployeeStat(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.employee_stat",
        }
        data.update(stream_specific_data)
        return data


class FinancialCallLegsReport(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.financial_call_legs_report",
        }
        data.update(stream_specific_data)
        return data


class GoalsReport(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.goals_report",
        }
        data.update(stream_specific_data)
        return data


class OfflineMessagesReport(ComagicStream):
    primary_key = "id"

    def request_body_json(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> Optional[Mapping]:
        data = (
            super().request_body_json(next_page_token=next_page_token, **kwargs).copy()
        )
        stream_specific_data = {
            "method": "get.offline_messages_report",
        }
        data["params"].update(
            {
                "fields": [
                    "id",
                    "date_time",
                    "text",
                    "communication_number",
                    "communication_page_url",
                    "communication_type",
                    "communication_id",
                    "ua_client_id",
                    "ym_client_id",
                    "sale_date",
                    "sale_cost",
                    "status",
                    "process_time",
                    "form_type",
                    "search_query",
                    "search_engine",
                    "referrer_domain",
                    "referrer",
                    "entrance_page",
                    "gclid",
                    "yclid",
                    "ymclid",
                    "ef_id",
                    "channel",
                    "employee_id",
                    "employee_full_name",
                    "employee_answer_message",
                    "employee_comment",
                    "site_id",
                    "site_domain_name",
                    "group_id",
                    "group_name",
                    "campaign_id",
                    "campaign_name",
                    "visit_other_campaign",
                    "visitor_id",
                    "visitor_name",
                    "visitor_phone_number",
                    "visitor_email",
                    "person_id",
                    "visitor_type",
                    "visitor_session_id",
                    "visits_count",
                    "visitor_first_campaign_id",
                    "visitor_first_campaign_name",
                    "visitor_city",
                    "visitor_region",
                    "visitor_country",
                    "visitor_device",
                    "utm_source",
                    "utm_medium",
                    "utm_term",
                    "utm_content",
                    "utm_campaign",
                    "openstat_ad",
                    "openstat_campaign",
                    "openstat_service",
                    "openstat_source",
                    "eq_utm_source",
                    "eq_utm_medium",
                    "eq_utm_term",
                    "eq_utm_content",
                    "eq_utm_campaign",
                    "eq_utm_referrer",
                    "eq_utm_expid",
                    "segments",
                    "visitor_custom_properties",
                    "tags",
                    "attributes",
                ],
            },
        )
        data.update(stream_specific_data)
        return data


# Source
class SourceComagic(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        """
        :param config:  the user-input config object conforming to the connector's spec.json
        :param logger:  logger object
        :return Tuple[bool, any]: (True, None) if the input config can be used to connect to the API successfully, (False, error) otherwise.
        """
        config = self.transform_config(config)
        date_range = config["prepared_date_range"]

        if not date_range.get("date_from") or not date_range.get("date_to"):
            return (
                False,
                "For automatic yesterday datetimes leave date_from AND date_to blank."
                "You can't leave blank only one field of them.",
            )

        if (
            difference_in_days_between_two_datetimes(
                date_range["date_from"], date_range["date_to"]
            )
            > 90
        ):
            return False, "Max value of requested date interval is 90 days."

        if (
            difference_in_days_between_two_datetimes(
                date_range["date_from"], date_range["date_to"]
            )
            < 0
        ):
            return False, "You must swap date_from and date_to."

        if config.get("custom_json"):
            try:
                json.loads(config["custom_json"])
            except Exception as e:
                return False, f"custom_json parse error: {e}"
            if not isinstance(json.loads(config["custom_json"]), dict):
                return (
                    False,
                    'Custom JSON must be JSON object like {"abc": "edf", "grf": "123"}. Only first-level object properties allowed.',
                )

        try:
            stream = self.streams(config)[0]
            stream_json = stream.request_body_json().copy()
            stream_json["params"]["limit"] = 1
            stream_json["params"]["date_from"] = get_yesterday_datetime()[0]
            stream_json["params"]["date_till"] = get_yesterday_datetime()[1]
            test_response = requests.post(
                stream.url_base + stream.path(), json=stream_json
            )
            if test_response.json().get("error"):
                return False, str(test_response.json()["error"])
            else:
                return True, None
        except Exception as e:
            return False, e

    @staticmethod
    def get_credentials(config: Mapping[str, Any]) -> Dict[str, str]:
        credentials: Dict[str, Any] = config["credentials"]
        auth_type: str = credentials["auth_type"]
        if auth_type == "access_token_auth":
            return {"login": credentials["login"], "password": credentials["password"]}
        if auth_type == "credentials_craft_auth":
            authenticator = CredentialsCraftAuthenticator(
                credentials_craft_host=credentials["credentials_craft_host"],
                credentials_craft_token=credentials["credentials_craft_token"],
                credentials_craft_token_id=credentials["credentials_craft_token_id"]
            )
            token_data: Dict[str, str] = authenticator.token
            return {"login": token_data["login"], "password": token_data["password"]}
        else:
            raise Exception(f"Unsupported auth type: {auth_type}")

    def get_access_token(self, login: str, password: str) -> str:
        login_data = requests.post(
            "https://dataapi.comagic.ru/v2.0",
            json={
                "jsonrpc": "2.0",
                "method": "login.user",
                "id": randint(1000000, 999999999),
                "params": {"login": login, "password": password},
            },
        ).json()
        return login_data["result"]["data"]["access_token"]

    @staticmethod
    def prepare_config_datetime(config: Mapping[str, Any]) -> Mapping[str, Any]:
        date_range = config["date_range"]
        range_type = config["date_range"]["date_range_type"]
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        config_date_format: str = "%Y-%m-%d"

        prepared_range = {}
        if range_type == "custom_date":
            prepared_range["date_from"] = date_range["date_from"]
            prepared_range["date_to"] = date_range["date_to"]
        elif range_type == "from_start_date_to_today":
            prepared_range["date_from"] = date_range["date_from"]
            if date_range["should_load_today"]:
                prepared_range["date_to"] = today
            else:
                prepared_range["date_to"] = today - timedelta(days=1)
        elif range_type == "last_n_days":
            prepared_range["date_from"] = today - timedelta(days=date_range["last_days_count"])
            if date_range.get("should_load_today", False):
                prepared_range["date_to"] = today
            else:
                prepared_range["date_to"] = today - timedelta(days=1)
        else:
            raise ValueError("Invalid date_range_type")

        if isinstance(prepared_range["date_from"], datetime):
            prepared_range["date_from"] = prepared_range["date_from"].strftime(config_date_format)

        if isinstance(prepared_range["date_to"], datetime):
            prepared_range["date_to"] = prepared_range["date_to"].strftime(config_date_format)

        config["prepared_date_range"] = prepared_range
        return config

    def transform_config(self, user_config) -> MutableMapping[str, Any]:
        config = user_config.copy()
        config = self.prepare_config_datetime(config)
        if not config.get("custom_json"):
            config["custom_json"] = "{}"
        return config

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        """
        :param config: A Mapping of the user input configuration as defined in the connector spec.
        """
        credentials: Dict[str, str] = self.get_credentials(config)
        access_token = self.get_access_token(credentials["login"], credentials["password"])
        transformed_config = self.transform_config(config)
        return [
            CallLegsReport(config=transformed_config, access_token=access_token),
            CallsReport(config=transformed_config, access_token=access_token),
            CampaignDailyStat(config=transformed_config, access_token=access_token),
            ChatsReport(config=transformed_config, access_token=access_token),
            CommunicationsReport(config=transformed_config, access_token=access_token),
            CtAcSummaryReport(config=transformed_config, access_token=access_token),
            CtSummaryReport(config=transformed_config, access_token=access_token),
            GoalsReport(config=transformed_config, access_token=access_token),
            OfflineMessagesReport(config=transformed_config, access_token=access_token),
            # Need specific chat_id
            ### ChatMessagesReport(config=transformed_config, access_token=access_token),
            # {'jsonrpc': '2.0', 'id': 987331442, 'error': {'code': -32602, 'message': 'You need at least one of the following components to access this method: call_center', 'data': {'mnemonic': 'method_component_disabled', 'field': None, 'value': None, 'params': {'components': 'call_center'}, 'extended_helper': None}}}
            ### EmployeeStat(config=transformed_config, access_token=access_token),
            # {'jsonrpc': '2.0', 'id': 25507699, 'error': {'code': -32003, 'message': 'Permission denied', 'data': {'mnemonic': 'forbidden', 'field': None, 'value': None, 'params': {}, 'extended_helper': None}}}
            ### FinancialCallLegsReport(config=transformed_config, access_token=access_token),
        ]
