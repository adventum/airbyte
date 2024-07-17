from requests.auth import AuthBase


class HeadersAuthenticator(AuthBase):
    """Authenticator that uses browser request headers"""

    def __init__(self, curl_request: str):
        self.curl_request = curl_request
        self.headers: dict[str, any] = {}

        for line in self.curl_request.split("\n"):
            if line.startswith("-H"):
                header: str = line.split("-H")[1]
                header = header.replace("\\", "").replace("'", "")
                header_name, header_value = header.split(":")
                header_name = header_name.strip()
                header_value = header_value.strip()
                if header_name not in ["Referer", "Content-Length"]:
                    self.headers[header_name] = header_value


