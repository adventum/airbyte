#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_bigo_ads import SourceBigoAds

if __name__ == "__main__":
    source = SourceBigoAds()
    launch(source, sys.argv[1:])
