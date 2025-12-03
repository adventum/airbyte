#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_yandex_realty import SourceYandexRealty

if __name__ == "__main__":
    source = SourceYandexRealty()
    launch(source, sys.argv[1:])
