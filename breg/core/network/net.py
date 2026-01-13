from typing import Any
from urllib.parse import urlencode

from requests import Request as LibRequest
from requests import Session as LibSession

from threading import Lock

from breg.config.config import HTTPConfiguration

from .type import ContentType, LibReqResponse, Response


class HTTP:
    _config: HTTPConfiguration
    _headers: dict[str, Any]
    _cookies: dict[str, str]

    _lock: Lock

    _last_request: LibRequest
    _last_response: Response

    def __init__(
        self,
        config: HTTPConfiguration,
        headers: dict[str, Any] = None,
        cookies: dict[str, str] = None,
    ):
        self._config = config
        self._headers = headers if headers is not None else {}
        self._cookies = cookies if cookies is not None else {}

        self._lock = Lock()
        self._last_request = None
        self._last_response = None

        self.set_header("User-Agent", config.USER_AGENT)
        self.set_header("Host", config.HOSTNAME)

    def request(
        self,
        method: str,
        path: str | list[str],
        body: Any = None,
        query: dict = None,
        fragment: str = None,
        headers: dict[str, Any] = None,
        follow_redirects: bool = False,
    ) -> Response:
        query_string: str | None = None
        fragment_string: str | None = None
        if query:
            query_string = urlencode(query)
        if fragment:
            fragment_string = fragment

        if isinstance(path, list):
            path = "/".join(s.strip("/") for s in path)
        full_path = f"{path.strip('/')}"

        if query_string:
            full_path += f"?{query_string}"
        if fragment_string:
            full_path += f"#{fragment_string}"

        cp_headers = self._headers.copy()
        if headers:
            cp_headers.update(headers)

        url = ""
        if self._config.HTTPS:
            url += "https://"
        else:
            url += "http://"
        url += self._config.HOSTNAME
        if self._config.PORT not in (80, 443) and self._config.PORT is not None:
            url += f":{self._config.PORT}"
        url += f"/{full_path}"

        request = None
        with self._lock:
            request = LibRequest(
                method=method,
                url=url,
                headers=cp_headers,
                cookies=self._cookies,
                data=body,
            )

        prepared_request = request.prepare()

        response = None
        with LibSession() as session:
            response = LibReqResponse(
                session.send(prepared_request, allow_redirects=follow_redirects)
            )

        with self._lock:
            self._last_request = prepared_request
            self._last_response = response

        return response

    def get(
        self,
        path: str | list[str],
        query: dict = None,
        fragment: str = None,
        headers: dict[str, Any] = None,
        follow_redirects: bool = False,
    ) -> Response:
        return self.request(
            "GET",
            path,
            query=query,
            fragment=fragment,
            headers=headers,
            follow_redirects=follow_redirects,
        )

    def post(
        self,
        path: str | list[str],
        body: Any,
        query: dict = None,
        fragment: str = None,
        headers: dict[str, Any] = None,
        content_type: "ContentType" = None,
    ) -> Response:
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
        with self._lock:
            self._headers[key] = value

    def remove_header(self, key: str) -> Any:
        with self._lock:
            return self._headers.pop(key, None)

    def get_headers(self) -> dict[str, Any]:
        with self._lock:
            return self._headers.copy()

    def get_header(self, key: str) -> str | None:
        with self._lock:
            return self._headers.get(key)

    def set_header(self, key: str, value: str) -> None:
        self.remove_header(key)
        self.add_header(key, value)

    def clear_headers(self) -> None:
        with self._lock:
            self._headers = {}

    def set_cookie(self, key: str, value: str) -> None:
        with self._lock:
            self._cookies[key] = value

    def get_cookie(self, key: str) -> str | None:
        with self._lock:
            return self._cookies.get(key)

    def remove_cookie(self, key: str) -> None:
        with self._lock:
            if key in self._cookies:
                del self._cookies[key]

    def get_lock(self) -> Lock:
        return self._lock


class Session(HTTP):
    _session_token: str
    additional_data: dict[str, Any]

    def __init__(
        self,
        config: HTTPConfiguration,
        session_token: str = "",
        session_name: str = "JSESSIONID",
    ):
        super().__init__(config)
        self._session_token = session_token
        self.additional_data = {}
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
