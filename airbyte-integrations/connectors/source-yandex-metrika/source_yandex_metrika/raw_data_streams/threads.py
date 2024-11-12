import logging
import os
import queue
from queue import Queue
from threading import Lock, Thread
from typing import Mapping, TypeVar, Iterable

import pandas as pd
from airbyte_cdk.models import SyncMode
from airbyte_cdk.utils.traced_exception import AirbyteTracedException

from ..source import YandexMetrikaRawDataStream

logger = logging.getLogger("airbyte")


class LogMessagesPoolConsumer:
    def log_info(self, message: str):
        logger.info(f"({self.__class__.__name__}) - {message}")


class YandexMetrikaRawSliceMissingChunksObserver:
    def __init__(self, expected_chunks_ids: list[int]):
        self._actually_loaded_chunk_ids = []
        self._expected_chunks_ids = expected_chunks_ids

    @property
    def missing_chunks(self) -> list[int]:
        missing_chunk_ids = []
        for expected_chunk_id in self._expected_chunks_ids:
            if expected_chunk_id not in self._actually_loaded_chunk_ids:
                missing_chunk_ids.append(expected_chunk_id)

        return missing_chunk_ids

    def is_missing_chunks(self) -> bool:
        return bool(self.missing_chunks)

    def add_actually_loaded_chunk_id(self, chunk_id: int) -> None:
        self._actually_loaded_chunk_ids.append(chunk_id)


class PreprocessedSlicePartProcessorThread(Thread, LogMessagesPoolConsumer):
    def __init__(
        self,
        name: str,
        stream_slice: Mapping[str, any],
        stream_instance: YandexMetrikaRawDataStream,
        lock: Lock,
        completed_chunks_observer: "YandexMetrikaRawSliceMissingChunksObserver",
    ):
        Thread.__init__(self, name=name, daemon=True)
        self.stream_slice = stream_slice
        self.stream_instance: YandexMetrikaRawDataStream = stream_instance
        self.completed = False
        self.records_count = 0
        self.lock = lock
        self.completed_chunks_observer = completed_chunks_observer
        self.filename: str | None = None

    def records_generator(self) -> Iterable[Mapping[str, any]]:
        try:
            with open(self.filename, "r") as input_f:
                df_reader = pd.read_csv(input_f, chunksize=5000, delimiter="\t")
                for chunk in df_reader:
                    with self.lock:
                        records: list[dict] = [
                            data for data in chunk.to_dict("records")
                        ]
                        for record in records:
                            self.stream_instance.replace_keys(record)
                            # Replace Nan values
                            record = {
                                key: value if not pd.isna(value) else None
                                for key, value in record.items()
                            }
                            self.records_count += 1
                            yield record
            del input_f
            del df_reader
        except AirbyteTracedException as e:
            logger.info(self.name, "exception", e)
            raise e
        except Exception as e:
            logger.info(self.name, "exception", e)
            logger.exception(
                f"Encountered an exception while reading stream {self.stream_instance.name}"
            )
            display_message = self.stream_instance.get_error_display_message(e)
            if display_message:
                raise AirbyteTracedException.from_exception(
                    e, message=display_message
                ) from e
            raise e
        finally:
            logger.info(f"Remove file {self.filename} for slice {self.stream_slice}")
            os.remove(self.filename)
            logger.info(f"Finished syncing {self.stream_instance.name}")

    def process_log_request(self):
        try:
            filename = next(
                self.stream_instance.read_records(
                    sync_mode=SyncMode.full_refresh,
                    stream_slice=self.stream_slice,
                )
            )
        except Exception:
            logger.info(
                f"Failed to get file for stream slice {self.stream_slice.values()}"
            )
            return

        self.filename = filename
        self.completed_chunks_observer.add_actually_loaded_chunk_id(
            self.stream_slice["part"]["part_number"]
        )

    def run(self):
        self.log_info(
            f"Run processor thread instance {self.name} with slice {self.stream_slice}"
        )
        self.process_log_request()
        self.log_info(
            f"End processing thread {self.name} (slice {self.stream_slice}) with {self.records_count} records"
        )


_T = TypeVar("_T")


class CustomQueue(Queue):
    def get(self, block: bool = True, timeout: float | None = None) -> _T:
        logger.info("current_queue_items", list(self.queue))
        return super().get(block, timeout)


class PreprocessedSlicePartThreadsController(LogMessagesPoolConsumer):
    def __init__(
        self,
        stream_instance: YandexMetrikaRawDataStream,
        preprocessed_slices_batch: list[Mapping[str, any]],
        raw_slice: Mapping[str, any],
        completed_chunks_observer: "YandexMetrikaRawSliceMissingChunksObserver",
        multithreading_threads_count: int = 1,
    ):
        self.raw_slice = raw_slice
        self.current_stream_slices = CustomQueue()
        self.stream_instance: YandexMetrikaRawDataStream = stream_instance
        self.completed_chunks_observer = completed_chunks_observer

        self.threads: list[PreprocessedSlicePartProcessorThread] = []
        self.lock = Lock()
        for slice in preprocessed_slices_batch:
            thread_name = "Thread-" + self.stream_instance.name + "-" + str(slice)
            self.threads.append(
                PreprocessedSlicePartProcessorThread(
                    name=thread_name,
                    stream_slice=slice,
                    stream_instance=self.stream_instance,
                    lock=self.lock,
                    completed_chunks_observer=self.completed_chunks_observer,
                )
            )

        self.multithreading_threads_count = multithreading_threads_count

    def process_threads(self):
        threads_queue = queue.Queue()

        for thread in self.threads:
            threads_queue.put(thread)

        running_threads = []
        while not threads_queue.empty() or len(running_threads) > 0:
            for thread in running_threads:
                if not thread.is_alive():
                    running_threads.remove(thread)

            if (
                len(running_threads) < self.multithreading_threads_count
                and not threads_queue.empty()
            ):
                thread: Thread = threads_queue.get()
                thread.start()
                running_threads.append(thread)

        for thread in self.threads:
            thread.join()
