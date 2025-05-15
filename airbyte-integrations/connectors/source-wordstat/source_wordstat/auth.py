from typing import Any
import re

import uncurl
from requests.auth import AuthBase


class HeadersAuthenticator(AuthBase):
    """Authenticator that uses browser request headers"""

    def __init__(self, curl_request: str):
        self.curl_request = curl_request
        self.headers: dict[str, Any] = {}
        self.cookies: dict[str, Any] = {}

        """Firefox has different format that can be parsed with uncurl"""
        if "Mozilla" in self.curl_request:
            ctx = uncurl.parse_context(self.curl_request)
            self.cookies = ctx.cookies
            self.headers = ctx.headers
            return

        """Fetch headers from curl"""
        # Chrome and Safari can't be parsed by uncurl
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
                cookies = re.findall(r"'([^']*)'", line)[0].strip()
                cookies_list = cookies.split(";")
                for cookie in cookies_list:
                    key, value = cookie.split("=")[0], "".join(cookie.split("=")[1:])
                    key, value = key.strip(), value.strip()
                    self.cookies[key] = value
