#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from setuptools import find_packages, setup

MAIN_REQUIREMENTS = ["airbyte-cdk>=4.3, <5", "pendulum>=2.1, <3", "uncurl"]

TEST_REQUIREMENTS = [
    "pytest~=6.2",
    "pytest-mock~=3.6.1",
    "source-acceptance-test",
]

setup(
    name="source_wordstat",
    description="Source implementation for Wordstat.",
    author="Airbyte",
    author_email="contact@airbyte.io",
    packages=find_packages(),
    install_requires=MAIN_REQUIREMENTS,
    package_data={"": ["*.json", "*.yaml", "schemas/*.json", "schemas/shared/*.json"]},
    extras_require={
        "tests": TEST_REQUIREMENTS,
    },
)
