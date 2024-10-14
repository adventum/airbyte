#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_one_s import SourceOneS

if __name__ == "__main__":
    source = SourceOneS()
    launch(source, sys.argv[1:])
