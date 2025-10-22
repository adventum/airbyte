from typing import Any
import re
import shlex
from typing import Dict

from requests.auth import AuthBase


class HeadersAuthenticator(AuthBase):
    """Authenticator that uses browser request headers"""

    def __init__(self, curl_request: str):
        self.curl_request = curl_request
        self.headers: dict[str, Any] = self.extract_headers_from_curl(
            self.curl_request, include_cookies=True
        )

    def __call__(self, request):
        request.headers = self.headers
        return request

    @staticmethod
    def extract_headers_from_curl(
        curl_cmd: str, include_cookies: bool = True
    ) -> Dict[str, str]:
        """Gpt-based cookie parser"""
        # Убираем POSIX-переносы строк: "\" + перевод строки
        normalized = re.sub(r"\\\s*\n", " ", curl_cmd)

        # Разбиваем по shell-правилам: учитываются кавычки и экранирование
        tokens = shlex.split(normalized, posix=True)

        headers: Dict[str, str] = {}
        i = 0
        while i < len(tokens):
            t = tokens[i]
            # -H / --header 'Name: value' или 'Name;' (пустой header)
            if t in ("-H", "--header") and i + 1 < len(tokens):
                raw = tokens[i + 1].strip()

                # Если точка с запятой и нет двоеточия — это пустой заголовок (curl "Empty;")
                # см. everything.curl.dev
                if raw.endswith(";") and ":" not in raw:
                    name, value = raw[:-1], ""
                else:
                    # Обычный случай: делим по первому двоеточию
                    if ":" in raw:
                        name, value = raw.split(":", 1)
                    else:
                        name, value = raw, ""

                headers[name.strip()] = value.strip()
                i += 2
                continue

            # -b / --cookie превращаем в заголовок Cookie (именно так curl его и шлёт)
            # см. CURLOPT_COOKIE
            if include_cookies and t in ("-b", "--cookie") and i + 1 < len(tokens):
                cookie_str = tokens[i + 1].strip()
                headers["Cookie"] = cookie_str
                i += 2
                continue

            i += 1

        return headers
