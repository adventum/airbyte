from typing import Any

from requests.auth import AuthBase


class HeadersAuthenticator(AuthBase):
    """Authenticator that uses browser request headers"""

    def __init__(self, curl_request: str):
        self.curl_request = curl_request
        self.headers: dict[str, Any] = {}
        self.cookies: dict[str, Any] = {}

        """Fetch headers from curl"""
        for line in self.curl_request.split("\\"):
            line = line.replace("\n", "").strip()
            if line.startswith("-H"):
                header: str = line.split("-H")[1]
                header = header.replace("\\", "").replace("'", "")
                header_name, header_value = header.split(": ")
                header_name = header_name.strip()
                header_value = header_value.strip()

                # These two will be added later
                if header_name not in ["Referer", "Content-Length"]:
                    self.headers[header_name] = header_value
            if line.startswith("-b"):
                cookies_list = line.split("-b")[1].strip().split(";")
                for cookie in cookies_list:
                    key, value = cookie.split("=")[0], "".join(cookie.split("=")[1:])
                    key = key.strip()
                    self.cookies[key] = value
