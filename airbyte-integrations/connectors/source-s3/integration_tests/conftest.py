#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#

import json
import os
import time
from pathlib import Path
from typing import Any, Iterable, List, Mapping
from zipfile import ZipFile

import docker
import pytest
import requests  # type: ignore[import]
from airbyte_cdk import AirbyteLogger
from docker.errors import APIError
from netifaces import AF_INET, ifaddresses, interfaces
from requests.exceptions import ConnectionError  # type: ignore[import]

logger = AirbyteLogger()
TMP_FOLDER = "/tmp/test_minio_source_s3"
if not os.path.exists(TMP_FOLDER):
    os.makedirs(TMP_FOLDER)


def get_local_ip() -> str:
    all_interface_ips: List[str] = []
    for iface_name in interfaces():
        all_interface_ips += [i["addr"] for i in ifaddresses(iface_name).setdefault(AF_INET, [{"addr": None}]) if i["addr"]]
    logger.info(f"detected interface IPs: {all_interface_ips}")
    for ip in sorted(all_interface_ips):
        if not ip.startswith("127."):
            return ip

    assert False, "not found an non-localhost interface"


@pytest.fixture(scope="session")
def minio_credentials() -> Mapping[str, Any]:
    config_template = Path(__file__).parent / "config_minio.template.json"
    assert config_template.is_file() is not None, f"not found {config_template}"
    config_file = Path(__file__).parent / "config_minio.json"
    config_file.write_text(config_template.read_text().replace("<local_ip>", get_local_ip()))
    credentials = {}
    with open(str(config_file)) as f:
        credentials = json.load(f)
    return credentials


@pytest.fixture(scope="session", autouse=True)
def minio_setup(minio_credentials: Mapping[str, Any]) -> Iterable[None]:

    with ZipFile("./integration_tests/minio_data.zip") as archive:
        archive.extractall(TMP_FOLDER)
    client = docker.from_env()
    # Minio should be attached to non-localhost interface.
    # Because another test container should have direct connection to it
    local_ip = get_local_ip()
    logger.debug(f"minio settings: {minio_credentials}")
    try:
        container = client.containers.run(
            image="minio/minio:RELEASE.2021-10-06T23-36-31Z",
            command=f"server {TMP_FOLDER}",
            name="ci_test_minio",
            auto_remove=True,
            volumes=[f"/{TMP_FOLDER}/minio_data:/{TMP_FOLDER}"],
            detach=True,
            ports={"9000/tcp": (local_ip, 9000)},
        )
    except APIError as err:
        if err.status_code == 409:
            for container in client.containers.list():
                if container.name == "ci_test_minio":
                    logger.info("minio was started before")
                    break
        else:
            raise

    check_url = f"http://{local_ip}:9000/minio/health/live"
    checked = False
    for _ in range(120):  # wait 1 min
        time.sleep(0.5)
        logger.info(f"try to connect to {check_url}")
        try:
            data = requests.get(check_url)
        except ConnectionError as err:
            logger.warn(f"minio error: {err}")
            continue
        if data.status_code == 200:
            checked = True
            logger.info("Run a minio/minio container...")
            break
        else:
            logger.info(f"minio error: {data.response.text}")
    if not checked:
        assert False, "couldn't connect to minio!!!"

    yield
    # this minio container was not finished because it is needed for all integration adn acceptance tests
