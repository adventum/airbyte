#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

from unittest.mock import MagicMock

from source_adriver.source import SourceAdriver


def test_check_connection(mocker):
    source = SourceAdriver()
    logger_mock, config_mock = MagicMock(), MagicMock()
    assert source.check_connection(logger_mock, config_mock) == (True, None)


def test_streams(mocker):
    source = SourceAdriver()
    config_mock = MagicMock()
    streams = source.streams(config_mock)
    # TODO: replace this with your streams number
    expected_streams_number = 2
    assert len(streams) == expected_streams_number
