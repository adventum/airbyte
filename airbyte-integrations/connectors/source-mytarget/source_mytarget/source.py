#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#

from datetime import datetime, timedelta
from logging import Logger
from typing import Any, List, Mapping, Tuple, Dict

import requests
from airbyte_cdk.models import ConnectorSpecification
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator, HttpAuthenticator
from source_mytarget.streams import (
    Banners,
    BannersStatistics,
    Campaigns,
    CampaignsStatistics,
    IncrementalStatisticsMixin,
    ObjectStream,
    PackagesPads,
    PadsTrees,
)
from .auth import CredentialsCraftAuthenticator


# Source
class SourceMytarget(AbstractSource):
    obj_streams_classes: List[ObjectStream] = [
        Campaigns,
        Banners,
        PadsTrees,
        PackagesPads,
    ]
    stat_streams_classes: List[IncrementalStatisticsMixin] = [
        CampaignsStatistics,
        BannersStatistics,
    ]

    def check_connection(self, logger, config) -> Tuple[bool, any]:
        config = self.prepare_config(config)
        auth = self.get_auth(config)

        if isinstance(auth, CredentialsCraftAuthenticator):
            auth_conn_check = auth.check_connection()
            if not auth_conn_check[0]:
                return auth_conn_check

        prepared_date_range: Dict[str, Any] = config["prepared_date_range"]
        if (
            not prepared_date_range.get("date_from")
            or not prepared_date_range.get("date_to")
        ):
            return False, "You must specify date_range in connector specification."

        for obj_stream_class in self.obj_streams_classes:
            obj_stream = obj_stream_class(authenticator=auth, config=config)
            if obj_stream.use_included_fields:
                obj_stream.fields_to_include = config.get(
                    obj_stream.included_fields_property_name(), []
                )
            else:
                obj_stream.fields_to_include = []
            obj_stream.page_size = 1

            if obj_stream.primary_key not in obj_stream.fields:
                return (
                    False,
                    f"Fields for stream {obj_stream.name} must contain '{obj_stream.primary_key}' field.",
                )

            test_response_data = requests.get(
                obj_stream.url_base + obj_stream.path(),
                headers=auth.get_auth_header(),
                params=obj_stream.request_params(),
            ).json()

            if test_response_data.get("error"):
                return False, test_response_data["error"].get(
                    "message", str(test_response_data)
                )

        return True, None

    def get_auth(self, config: Mapping[str, Any]) -> HttpAuthenticator:
        if config["credentials"]["auth_type"] == "access_token_auth":
            return TokenAuthenticator(config["credentials"]["access_token"])
        elif config["credentials"]["auth_type"] == "credentials_craft_auth":
            return CredentialsCraftAuthenticator(
                credentials_craft_host=config["credentials"]["credentials_craft_host"],
                credentials_craft_token=config["credentials"][
                    "credentials_craft_token"
                ],
                credentials_craft_token_id=config["credentials"][
                    "credentials_craft_token_id"
                ],
            )
        else:
            raise Exception(
                "Invalid Auth type. Available: access_token_auth and credentials_craft_auth"
            )

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
            prepared_range["date_from"] = today - timedelta(
                days=date_range["last_days_count"]
            )
            if date_range.get("should_load_today", False):
                prepared_range["date_to"] = today
            else:
                prepared_range["date_to"] = today - timedelta(days=1)
        else:
            raise ValueError("Invalid date_range_type")

        if isinstance(prepared_range["date_from"], datetime):
            prepared_range["date_from"] = prepared_range["date_from"].strftime(
                config_date_format
            )

        if isinstance(prepared_range["date_to"], datetime):
            prepared_range["date_to"] = prepared_range["date_to"].strftime(
                config_date_format
            )

        config["prepared_date_range"] = prepared_range
        return config

    def spec(self, logger: Logger) -> ConnectorSpecification:
        spec = super().spec(logger)
        properties = spec.connectionSpecification["properties"]
        init_obj_streams = [s(config={}) for s in self.obj_streams_classes]
        for property_order, obj_stream in enumerate(init_obj_streams, len(properties)):
            if obj_stream.use_included_fields:
                properties.update(
                    {
                        obj_stream.included_fields_property_name(): {
                            "title": f"{obj_stream.object_name_plural.title()} Included Fields",
                            "description": f"Comma-separated fields names that will be included "
                            f'in {obj_stream.object_name_plural.title()} stream schema. "{obj_stream.primary_key}" field is required! Leave empty if you'
                            f" want to load all {obj_stream.object_name_plural.title()} fields."
                            f" See available schema fields: "
                            f'<a href="https://target.my.com/doc/api/ru/object/{obj_stream.object_name.title()}">'
                            f"{obj_stream.object_name.title()} docs</a>",
                            "type": "string",
                            "pattern": "^$|^(\\w+,?)+\\w+$",
                            "examples": ["id,field1,field2,field3"],
                            "order": property_order,
                        }
                    }
                )

        return spec

    def prepare_config(self, config: Mapping[str, Any]) -> Mapping[str, Any]:
        config = self.prepare_config_datetime(config)
        for obj_stream in [s(config={}) for s in self.obj_streams_classes]:
            splitted_included_fields = list(
                filter(
                    None,
                    config.get(obj_stream.included_fields_property_name(), "").split(
                        ","
                    ),
                )
            )
            config.update(
                {obj_stream.included_fields_property_name(): splitted_included_fields}
            )

        return config

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        config = self.prepare_config(config)
        auth = self.get_auth(config)
        return [
            *[
                obj_stream(
                    authenticator=auth,
                    config=config,
                    fields_to_include=config.get(
                        obj_stream.included_fields_property_name(), []
                    ),
                )
                for obj_stream in self.obj_streams_classes
            ],
            *[
                stat_stream(
                    authenticator=auth,
                    config=config,
                    date_from=config["prepared_date_range"]["date_from"],
                    date_to=config["prepared_date_range"]["date_to"],
                )
                for stat_stream in self.stat_streams_classes
            ],
        ]
