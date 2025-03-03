#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_sber_escrow import SourceSberEscrow

if __name__ == "__main__":
    source = SourceSberEscrow()
    launch(source, sys.argv[1:])
