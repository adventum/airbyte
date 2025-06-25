#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_fraudscore import SourceFraudscore

if __name__ == "__main__":
    source = SourceFraudscore()
    launch(source, sys.argv[1:])
