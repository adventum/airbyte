#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import json
import datetime
from datetime import datetime
from typing import Dict, Generator

from .auth import get_authenticator, CredentialsCraftAuthenticator, ProfitbaseAuthenticator
from .streams import House, Projects, Property, Statuses, History, ProfitBaseStream

from airbyte_cdk.models import (
    AirbyteCatalog,
    AirbyteConnectionStatus,
    AirbyteMessage,
    AirbyteRecordMessage,
    AirbyteStream,
    ConfiguredAirbyteCatalog,
    Status,
    Type,
)

from airbyte_cdk.sources import Source
from airbyte_cdk.logger import AirbyteLogger
from airbyte_cdk.sources.utils.schema_helpers import ResourceSchemaLoader
from airbyte_cdk.sources.streams.core import package_name_from_class
from airbyte_cdk.models import SyncMode

"""
Important: The airbyte schema will have fewer fields than in reality,
because the received fields from the API will be processed on the dbt side
"""

streams_classes_mapping = {
    "house": House,
    "projects": Projects,
    "property": Property,
    "statuses": Statuses,
    "history": History
}


# Получение даты из конфига, преобразование их к нужному виду
def process_date(config: json) -> dict[str: any]:
    date_range = config.get("date_range")
    range_type = config.get("date_range").get("date_range_type")
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    prepared_range = {}
    if date_range:
        if range_type == "custom_date":
            prepared_range["date_from"] = date_range.get("date_from")
            prepared_range["date_to"] = date_range.get("date_to")

        elif range_type == "from_date_from_to_today":
            prepared_range["date_from"] = date_range.get("date_from")

        elif range_type == "last_n_days":
            prepared_range["date_from"] = today - datetime.timedelta(days=date_range.get("last_days"))

            if date_range["should_load_today"]:
                prepared_range["date_to"] = today

            else:
                prepared_range["date_to"] = today - datetime.timedelta(days=1)
        else:
            raise ValueError("Invalid date_range_type")
    return prepared_range


class SourceProfitbase(Source):

    def __init__(self):
        self.schema_loader = ResourceSchemaLoader(package_name_from_class(self.__class__))

    def check(self, logger: AirbyteLogger, config: json) -> AirbyteConnectionStatus:
        """
        Проверяет, можно ли использовать предоставленную конфигурацию для успешного подключения к интеграции
        """
        try:
            # api_key = config.get("api_key")
            # account_number = config.get("account_number")
            # authenticator = ProfitbaseAuthenticator(api_key=api_key, account_number=account_number)

            authenticator = get_authenticator(config)
            access_token = authenticator.token

            if not access_token:
                raise ValueError("Access token не был получен, это из-за некорректных вводимых данных/"
                                 "ваш IP не в списке Whitelist ProfitBase ")

            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"Произошла ошибка: {str(e)}")

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:
        streams = []
        for stream_name in ["house", "projects", "property", "statuses", "history"]:
            json_schema = self.schema_loader.get_schema(stream_name)
            streams.append(AirbyteStream(
                name=stream_name,
                json_schema=json_schema,
                supported_sync_modes=[SyncMode.full_refresh, SyncMode.incremental]
            ))

        return AirbyteCatalog(streams=streams)

    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:

        account_number: str = config.get("account_number")
        crm: str = config.get("crm")
        authenticator: ProfitbaseAuthenticator | CredentialsCraftAuthenticator = get_authenticator(config)

        auth_token: str = authenticator.token

        for configured_stream in catalog.streams:
            stream_name = configured_stream.stream.name

            stream_class = streams_classes_mapping.get(stream_name)
            if stream_class:
                stream: ProfitBaseStream = stream_class(auth_token=auth_token, account_number=account_number)
                date: dict[str: any] = process_date(config)

                offset = 99
                while True:
                    # Стрим history использует POST запрос, в отличии от других,
                    # поэтому другая обработка запроса
                    if stream_name == "history":
                        property_ids = config.get("history_stream").get("property_ids")
                        house_ids = config.get("history_stream").get("house_ids")
                        # date_from = config.get("history_stream").get("date_from")
                        # date_to = config.get("history_stream").get("date_to")
                        date_from = date.get("date_from")
                        date_to = date.get("date_to")
                        deal_id = config.get("history_stream").get("dealId")

                        # Здесь get_data отправляет POST запрос,т.к переопределена в streams
                        data = stream.get_data(
                            property_ids=property_ids,
                            house_ids=house_ids,
                            date_from=date_from,
                            date_to=date_to,
                            deal_id=deal_id
                        )["response"]

                    else:
                        # Для других стримов с GET запросом: projects, house и тд
                        data = stream.get_data(offset, crm)["data"] if stream_name != "projects" \
                                                               else stream.get_data(offset, crm)

                        if stream_name == "statuses":
                            data = stream.get_data(offset, crm)["data"]["customStatuses"]

                    if not data:
                        break

                    for record in data:
                        yield AirbyteMessage(
                            type=Type.RECORD,
                            record=AirbyteRecordMessage(
                                stream=stream_name,
                                data=record,
                                emitted_at=int(datetime.now().timestamp()) * 1000
                            ),
                        )

                    logger.info(f"Page with offset {offset} was loaded. Stream name - {stream_name}")

                    # Это нужно для того, чтобы другие стримы, не имеющие offset не парсились бесконечно
                    if stream_name != "property":
                        break
                    offset += 100
            else:
                logger.error(f"Stream {stream_name} not supported.")
