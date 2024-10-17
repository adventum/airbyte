#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#


import logging
import shutil
from datetime import datetime
from typing import Iterator, Mapping, MutableMapping

from airbyte_cdk.models import AirbyteMessage
from airbyte_cdk.models import ConfiguredAirbyteCatalog, ConfiguredAirbyteStream, SyncMode
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator
from airbyte_cdk.sources.utils.schema_helpers import InternalConfig

from .aggregated_data_streams.streams import (
    AggregateDataYandexMetrikaReport,
)
from .auth import CredentialsCraftAuthenticator
from .exceptions import ConfigInvalidError
from .raw_data_streams.exceptions import MissingChunkIdsError
from .raw_data_streams.stream import YandexMetrikaRawDataStream
from .raw_data_streams.threads import (
    PreprocessedSlicePartThreadsController,
    YandexMetrikaRawSliceMissingChunksObserver,
)
from .utils import get_config_date_range

logger = logging.getLogger("airbyte")
CONFIG_DATE_FORMAT = "%Y-%m-%d"


class SourceYandexMetrika(AbstractSource):

    @staticmethod
    def preprocess_raw_stream_slice(
        stream_instance: YandexMetrikaRawDataStream,
        stream_slice: Mapping[str, any],
        check_log_request_ability: bool = False,
    ) -> tuple[list[Mapping[str, any]], str]:
        logger.info(
            f"Preprocessing raw stream slice {stream_slice} for stream {stream_instance.name}..."
        )

        preprocessor = stream_instance.preprocessor
        is_request_on_server, request_id = preprocessor.check_if_log_request_already_on_server(
            stream_slice
        )
        if is_request_on_server:
            logger.info(f"Log request {request_id} already on server.")
        else:
            logger.info(f"Log request was not found on server, creating it.")
            if check_log_request_ability:
                is_request_available, request_ability_msg = preprocessor.check_log_request_ability(
                    stream_slice
                )
                if not is_request_available:
                    raise Exception(request_ability_msg)

            request_id = preprocessor.create_log_request(stream_slice)
        preprocessed_slice = preprocessor.wait_for_log_request_processed(
            log_request_id=request_id, stream_slice=stream_slice
        )
        return [
            {
                "date_from": preprocessed_slice["date_from"],
                "date_to": preprocessed_slice["date_to"],
                "log_request_id": preprocessed_slice["log_request_id"],
                "part": part,
            }
            for part in preprocessed_slice["processed_parts"]
        ], preprocessed_slice["log_request_id"]

    @staticmethod
    def postprocess_raw_stream_slice(
        stream_instance: YandexMetrikaRawDataStream, stream_slice, log_request_id: str
    ):
        preprocessor = stream_instance.preprocessor
        if stream_instance.clean_slice_after_successfully_loaded:
            logger.info(f"clean_slice_after_successfully_loaded {stream_slice}")
            preprocessor.clean_log_request(log_request_id=log_request_id)

    def read(
        self,
        logger: logging.Logger,
        config: Mapping[str, any],
        catalog: ConfiguredAirbyteCatalog,
        state: MutableMapping[str, any] = None,
    ) -> Iterator[AirbyteMessage]:
        yield from super().read(logger, config, catalog, state)

        # Remove tmp folder
        try:
            shutil.rmtree("output", ignore_errors=True)
        except:
            pass

        logger.info(f"Finished syncing {self.name}")
        yield from []

    def _read_full_refresh(
        self,
        logger: logging.Logger,
        stream_instance: Stream,
        configured_stream: ConfiguredAirbyteStream,
        internal_config: InternalConfig,
    ) -> Iterator[AirbyteMessage]:
        if isinstance(stream_instance, YandexMetrikaRawDataStream):
            raw_slices = stream_instance.stream_slices(
                sync_mode=SyncMode.full_refresh, cursor_field=configured_stream.cursor_field
            )
            logger.debug(
                f"Processing raw stream slices for {configured_stream.stream.name}",
                extra={"stream_slices": raw_slices},
            )
            logger.info(f"Raw slices: {raw_slices}")
            for raw_slice in raw_slices:
                logger.info(f"Current raw slice: {raw_slice}")
                preprocessed_slices, log_request_id = self.preprocess_raw_stream_slice(
                    stream_instance=stream_instance,
                    stream_slice=raw_slice,
                    check_log_request_ability=stream_instance.check_log_requests_ability,
                )
                logger.info(f"Current preprocessed slices: {preprocessed_slices}")
                completed_chunks_observer = YandexMetrikaRawSliceMissingChunksObserver(
                    expected_chunks_ids=[
                        chunk["part"]["part_number"] for chunk in preprocessed_slices
                    ]
                )

                threads_controller = PreprocessedSlicePartThreadsController(
                    stream_instance=stream_instance,
                    raw_slice=raw_slice,
                    preprocessed_slices_batch=preprocessed_slices,
                    multithreading_threads_count=stream_instance.multithreading_threads_count,
                    completed_chunks_observer=completed_chunks_observer,
                )
                logger.info("Threads controller created")
                logger.info("Run threads process, get into main loop")

                threads_controller.process_threads()

                if completed_chunks_observer.is_missing_chunks():
                    raise MissingChunkIdsError(
                        f"Missing chunks {completed_chunks_observer.missing_chunks} for raw slice {raw_slice}",
                    )
                else:
                    logger.info(
                        "YandexMetrikaRawSliceMissingChunksObserver test completed with no exceptions. "
                        f"completed_chunks_observer.missing_chunks result: {completed_chunks_observer.missing_chunks}"
                    )

                self.postprocess_raw_stream_slice(
                    stream_instance=stream_instance,
                    stream_slice=raw_slice,
                    log_request_id=log_request_id,
                )

                for thread in threads_controller.threads:
                    records_generator = thread.records_generator()
                    yield from (
                        self._get_message(record, stream_instance) for record in records_generator
                    )
            yield from []
        else:
            yield from super()._read_full_refresh(
                logger, stream_instance, configured_stream, internal_config
            )

    def check_connection(self, logger, config) -> tuple[bool, any]:
        """Check connection"""

        """Check auth"""
        auth = self.get_auth(config)
        if isinstance(auth, CredentialsCraftAuthenticator):
            auth.check_connection(raise_exception=True)

        try:
            streams = self.streams(config, init_for_test=True)
        except ConfigInvalidError as ex:
            return False, str(ex)

        """Check streams exists"""
        if not streams:
            return False, "No streams available"

        """Check names"""
        if len([stream.name for stream in streams]) != len({stream.name for stream in streams}):
            return (
                False,
                "All streams must have unique names! Try adding your own stream names for hits and visits streams",
            )

        """Check connection for first stream"""
        stream = streams[0]

        if isinstance(stream, YandexMetrikaRawDataStream):
            preprocessor = stream.preprocessor
            if stream.check_log_requests_ability:
                can_replicate_all_slices, message = preprocessor.check_stream_slices_ability()
                if not can_replicate_all_slices:
                    return can_replicate_all_slices, message

        elif isinstance(stream, AggregateDataYandexMetrikaReport):
            test_response = stream.make_test_request()
            test_response_data = test_response.json()
            if test_response_data.get("errors"):
                return (
                    False,
                    f"Stream #({stream.name}) error: "
                    + test_response_data.get("message"),
                )

        return True, None

    def transform_config(self, raw_config: dict[str, any]) -> Mapping[str, any]:
        date_from, date_to = get_config_date_range(raw_config)

        raw_config["prepared_date_range"] = {
            "date_from": datetime.fromisoformat(date_from.isoformat()),  # lazy pendulum to datetime conversion
            "date_to": datetime.fromisoformat(date_to.isoformat()),
        }
        raw_config["counter_id"] = int(raw_config["counter_id"])
        return raw_config

    def get_auth(self, config: Mapping[str, any]) -> TokenAuthenticator:
        if config["credentials"]["auth_type"] == "access_token_auth":
            return TokenAuthenticator(config["credentials"]["access_token"], auth_method="OAuth")
        elif config["credentials"]["auth_type"] == "credentials_craft_auth":
            return CredentialsCraftAuthenticator(
                credentials_craft_host=config["credentials"]["credentials_craft_host"],
                credentials_craft_token=config["credentials"]["credentials_craft_token"],
                credentials_craft_token_id=config["credentials"]["credentials_craft_token_id"],
                check_connection=True,
                raise_exception_on_check=True,
            )
        else:
            raise Exception(
                "Неверный типа авторизации. Доступные: access_token_auth и credentials_craft_auth"
            )

    @staticmethod
    def format_field_name_map(
        field_name_map_old_format: list[dict[str, any]] | None
    ) -> dict[str, str]:
        """Get values that needs to be replaced and their replacements"""
        return (
            {item["old_value"]: item["new_value"] for item in field_name_map_old_format}
            if field_name_map_old_format
            else {}
        )

    def streams(self, config: Mapping[str, any], init_for_test: bool = False) -> list[Stream]:
        """Get streams"""

        """Process config and get auth"""
        config = self.transform_config(config)
        auth = self.get_auth(config)

        """Add raw data streams"""
        raw_data_streams = []
        for stream_config in config.get("raw_data_hits_visits_report", []):
            stream = YandexMetrikaRawDataStream(
                stream_config=stream_config,
                authenticator=auth,
                counter_id=config["counter_id"],
                date_from=config["prepared_date_range"]["date_from"],
                date_to=config["prepared_date_range"]["date_to"],
                log_source=stream_config["report_type"],
                created_for_test=init_for_test,
                field_name_map=self.format_field_name_map(stream_config.get("field_name_map")),
            )

            raw_data_streams.append(stream)

        """Add aggregated streams"""
        aggregated_data_streams = []
        for stream_config in config.get("aggregated_reports", []):
            stream = AggregateDataYandexMetrikaReport(
                authenticator=auth,
                counter_id=config["counter_id"],
                stream_config=stream_config,
                date_from=config["prepared_date_range"]["date_from"],
                date_to=config["prepared_date_range"]["date_to"],
                field_name_map=self.format_field_name_map(config.get("field_name_map")),
            )
            aggregated_data_streams.append(stream)
        return [*raw_data_streams, *aggregated_data_streams]
