#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
# ¬


from setuptools import find_packages, setup

MAIN_REQUIREMENTS = ["airbyte-cdk>=4.3, <5.0", "pendulum>=2.1, <3", "pandas>=2.2.0, <3.0.0", "unidecode"]

TEST_REQUIREMENTS = [
    "pytest~=6.2",
    "pytest-mock~=3.6.1",
    "source-acceptance-test",
]

setup(
    name="source_sipuni",
    description="Source implementation for Sipuni.",
    author="Airbyte",
    author_email="contact@airbyte.io",
    packages=find_packages(),
    install_requires=MAIN_REQUIREMENTS,
    package_data={"": ["*.json", "*.yaml", "schemas/*.json", "schemas/shared/*.json"]},
    extras_require={
        "tests": TEST_REQUIREMENTS,
    },
)
