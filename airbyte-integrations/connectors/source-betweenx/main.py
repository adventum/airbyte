#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_betweenx import SourceBetweenx

if __name__ == "__main__":
    source = SourceBetweenx()
    launch(source, sys.argv[1:])
