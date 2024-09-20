#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import json
from datetime import datetime
from typing import Dict, Generator

from .auth import ProfitbaseAuthenticator
from .streams import House, Projects, Property, Statuses, History

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


class SourceProfitbase(Source):

    def __init__(self):
        self.schema_loader = ResourceSchemaLoader(package_name_from_class(self.__class__))

    def check(self, logger: AirbyteLogger, config: json) -> AirbyteConnectionStatus:
        """
        Проверяет, можно ли использовать предоставленную конфигурацию для успешного подключения к интеграции
        """
        try:
            api_key = config.get("api_key")
            account_number = config.get("account_number")
            authenticator = ProfitbaseAuthenticator(api_key=api_key, account_number=account_number)

            access_token = authenticator.raw_token

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

        api_key = config.get("api_key")
        account_number = config.get("account_number")
        crm = config.get("crm")
        authenticator = ProfitbaseAuthenticator(api_key=api_key, account_number=account_number)

        auth_token = authenticator.raw_token

        for configured_stream in catalog.streams:
            stream_name = configured_stream.stream.name

            stream_class = streams_classes_mapping.get(stream_name)
            if stream_class:
                stream = stream_class(auth_token=auth_token, account_number=account_number)

                offset = 99
                while True:
                    # Стрим history использует POST запрос, в отличии от других,
                    # поэтому другая обработка запроса
                    if stream_name == "history":
                        property_ids = config.get("history_stream").get("property_ids")
                        house_ids = config.get("history_stream").get("house_ids")
                        date_from = config.get("history_stream").get("date_from")
                        date_to = config.get("history_stream").get("date_to")
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
