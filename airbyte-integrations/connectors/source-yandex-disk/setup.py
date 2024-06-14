#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from setuptools import find_packages, setup

MAIN_REQUIREMENTS = [
    # "airbyte-cdk~=0.1.56",
    "airbyte-cdk~=0.2",
    "pandas~=1.5.0",
    "openpyxl~=3.0.10",
    # "pyyaml~=5.3.1",
]

TEST_REQUIREMENTS = [
    "pytest~=6.1",
    "pytest-mock~=3.6.1",
    "source-acceptance-test",
]

setup(
    name="source_yandex_disk",
    description="Source implementation for Yandex Disk.",
    author="Airbyte",
    author_email="contact@airbyte.io",
    packages=find_packages(),
    install_requires=MAIN_REQUIREMENTS,
    package_data={"": ["*.json", "*.yaml", "schemas/*.json", "schemas/shared/*.json"]},
    extras_require={
        "tests": TEST_REQUIREMENTS,
    },
)
