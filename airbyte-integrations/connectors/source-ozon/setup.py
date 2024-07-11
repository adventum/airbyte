#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from setuptools import find_packages, setup

MAIN_REQUIREMENTS = [
    "airbyte-cdk~=0.80",
    "pydantic~=1.10",
    "requests~=2.31",
]

TEST_REQUIREMENTS = [
    "pytest~=6.2",
    "pytest-mock~=3.6.1",
]

setup(
    name="source_ozon",
    description="Source implementation for Ozon.",
    author="Oleg Denisov",
    author_email="o.denisov@adventum.ru",
    packages=find_packages(),
    install_requires=MAIN_REQUIREMENTS,
    package_data={"": ["*.json", "*.yaml", "schemas/*.json", "schemas/shared/*.json"]},
    extras_require={
        "tests": TEST_REQUIREMENTS,
    },
)
