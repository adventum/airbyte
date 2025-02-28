#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import logging
import sys

from airbyte_cdk.entrypoint import launch
from source_appmetrica_logs_api import SourceAppmetricaLogsApi

logger = logging.getLogger("airbyte")

if __name__ == "__main__":
    source = SourceAppmetricaLogsApi()
    launch(source, sys.argv[1:])
