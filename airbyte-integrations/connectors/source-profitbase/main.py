#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_profitbase import SourceProfitbase

if __name__ == "__main__":
    source = SourceProfitbase()
    launch(source, sys.argv[1:])
