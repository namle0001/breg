from enum import StrEnum

from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from typing import Any
from urllib.parse import urlencode

from breg.config.config import HTTPConfiguration


class ContentType(StrEnum):
    FORM_URLENCODED = "application/x-www-form-urlencoded"
    MULTIPART_FORM_DATA = "multipart/form-data"
    JSON = "application/json"


class HTTP:
    _config: HTTPConfiguration
    _headers: dict[str, Any]
    _cookies: dict[str, str]

    _last_connection: HTTPConnection | HTTPSConnection = None
    _last_response: HTTPResponse = None

    def __init__(
        self,
        config: HTTPConfiguration,
        headers: dict[str, Any] = None,
        cookies: dict[str, str] = None,
    ):
        self._config = config
        self._headers = headers if headers is not None else {}
        self._cookies = cookies if cookies is not None else {}

        self.set_header("User-Agent", config.USER_AGENT)
        self.set_header("Host", config.HOSTNAME)

    def request(
        self,
        method: str,
        path: str | list[str],
        body: bytes = None,
        query: dict = None,
        fragment: str = None,
        headers: dict[str, Any] = None,
    ) -> HTTPResponse:
        query_string: str | None = None
        fragment_string: str | None = None
        if query:
            query_string = urlencode(query)
        if fragment:
            fragment_string = fragment

        if isinstance(path, list):
            path = "/".join(s.strip("/") for s in path)
        full_path = f"{path}"

        if query_string:
            full_path += f"?{query_string}"
        if fragment_string:
            full_path += f"#{fragment_string}"

        cp_headers = self._headers.copy()
        if headers:
            cp_headers.update(headers)
        if self._cookies:
            cookie_header = "; ".join(
                f"{key}={value}" for key, value in self._cookies.items()
            )
            cp_headers["Cookie"] = cookie_header

        connection_class = HTTPSConnection if self._config.HTTPS else HTTPConnection
        connection = connection_class(self._config.HOSTNAME, self._config.PORT)

        connection.request(method, full_path, body, cp_headers)
        response = connection.getresponse()

        self._last_connection = connection
        self._last_response = response

        return response

    def get(
        self,
        path: str | list[str],
        query: dict = None,
        fragment: str = None,
        headers: dict[str, Any] = None,
    ) -> HTTPResponse:
        return self.request(
            "GET", path, query=query, fragment=fragment, headers=headers
        )

    def post(
        self,
        path: str | list[str],
        body: bytes,
        query: dict = None,
        fragment: str = None,
        headers: dict[str, Any] = None,
        content_type: "ContentType" = None,
    ) -> HTTPResponse:
        if content_type is not None:
            if headers is None:
                headers = {}
            else:
                headers = headers.copy()
            headers["Content-Type"] = content_type.value
        return self.request(
            "POST", path, body, query=query, fragment=fragment, headers=headers
        )

    def add_header(self, key: str, value: str) -> None:
        self._headers[key] = value

    def remove_header(self, key: str) -> Any:
        return self._headers.pop(key, None)

    def get_headers(self) -> dict[str, Any]:
        return self._headers

    def get_header(self, key: str) -> str | None:
        return self._headers.get(key)

    def set_header(self, key: str, value: str) -> None:
        self.remove_header(key)
        self.add_header(key, value)

    def clear_headers(self) -> None:
        self._headers = []

    def set_cookie(self, key: str, value: str) -> None:
        self._cookies[key] = value

    def get_cookie(self, key: str) -> str | None:
        return self._cookies.get(key)

    def remove_cookie(self, key: str) -> None:
        if key in self._cookies:
            del self._cookies[key]


class Session(HTTP):
    _session_token: str
    additional_data: dict[str, Any] = {}

    def __init__(
        self,
        config: HTTPConfiguration,
        session_token: str = "",
        session_name: str = "JSESSIONID",
    ):
        super().__init__(config)
        self._session_token = session_token
        if session_token:
            self.set_cookie(session_name, session_token)

    @classmethod
    def from_http(
        cls, http: HTTP, session_token: str, session_name: str = "JSESSIONID"
    ) -> "Session":
        return cls(http._config, session_token, session_name)


def parse_cookies(cookie_str: str) -> dict[str, str]:
    """Parses a cookie string into a dictionary of cookies.

    Args:
        cookie_str (str): The cookie string to parse.

    Returns:
        dict[str, str]: A dictionary of cookie key-value pairs.
    """
    cookies = {}
    cookie_pairs = cookie_str.split(";")
    for pair in cookie_pairs:
        if "=" in pair:
            key, value = pair.strip().split("=", 1)
            cookies[key] = value
    return cookies


def parse_set_cookie_headers(
    set_cookie_headers: list[str],
) -> dict[str, str]:
    """Parses a list of 'Set-Cookie' headers into a dictionary of cookies.

    Args:
        set_cookie_headers (list[str]): The list of 'Set-Cookie' header strings to parse.

    Returns:
        dict[str, str]: A dictionary of cookie key-value pairs.
    """
    cookies = {}
    for header in set_cookie_headers:
        parts = header.split(";")
        if parts:
            key_value = parts[0]
            if "=" in key_value:
                key, value = key_value.strip().split("=", 1)
                cookies[key] = value
    return cookies
