#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_mi_ads import SourceMiAds

if __name__ == "__main__":
    source = SourceMiAds()
    launch(source, sys.argv[1:])
