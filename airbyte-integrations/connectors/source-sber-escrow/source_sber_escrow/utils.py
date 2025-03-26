import os
import tempfile
from typing import Optional

import requests


class CertifiedRequests:
    def __init__(
        self,
        client_cert: Optional[str],
        client_key: Optional[str],
        ca_chain: Optional[str] = None,
    ) -> None:
        self.client_cert = client_cert
        self.client_key = client_key
        self.ca_chain = ca_chain

    def get(self, url: str, **kwargs) -> requests.Response:
        return self._make_request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self._make_request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        return self._make_request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        return self._make_request("DELETE", url, **kwargs)

    def patch(self, url: str, **kwargs) -> requests.Response:
        return self._make_request("PATCH", url, **kwargs)

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        # Certificates are installed on the system level
        if os.environ.get("REQUESTS_CA_BUNDLE"):
            return requests.request(method=method, url=url, **kwargs)

        # Try to get the certificates from the environment variables
        with (
            tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=True) as cert_temp,
            tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=True) as key_temp,
            tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=True) as ca_chain_temp,
        ):
            cert_temp.write(self.client_cert)
            key_temp.write(self.client_key)

            if self.ca_chain:
                ca_chain_temp.write(self.ca_chain)

            cert_temp.flush()
            key_temp.flush()
            ca_chain_temp.flush()

            kwargs["cert"] = (cert_temp.name, key_temp.name)
            if self.ca_chain:
                kwargs["verify"] = ca_chain_temp.name

            return requests.request(method=method, url=url, **kwargs)
