#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_sendsay import SourceSendsay

if __name__ == "__main__":
    source = SourceSendsay()
    launch(source, sys.argv[1:])
