"""Module for HTTP networking functionality."""

from threading import Lock
from typing import Any
from urllib.parse import urlencode

from requests import Request as LibRequest
from requests import Session as LibSession

from breg.config.config import HTTPConfiguration

from .type import ContentType, LibReqResponse, Response


def _lock_method(lock_attr: str):
    def decorator(method):
        def wrapper(self, *args, **kwargs):
            with getattr(self, lock_attr):
                return method(self, *args, **kwargs)

        return wrapper

    return decorator


class HTTP:
    """A class for making HTTP requests with configurable headers and cookies."""

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
        """Initializes the HTTP client with the given configuration, headers, and cookies.

        Args:
            config (HTTPConfiguration): The HTTP configuration settings.
            headers (dict[str, Any], optional): Initial headers to include in requests. Defaults to None.
            cookies (dict[str, str], optional): Initial cookies to include in requests. Defaults to None.
        """
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
        """Makes an HTTP request with the specified parameters.

        Args:
            method (str): The HTTP method (e.g., 'GET', 'POST').
            path (str | list[str]): The URL path or list of path segments.
            body (Any, optional): The request body. Defaults to None.
            query (dict, optional): Query parameters to include in the URL. Defaults to None.
            fragment (str, optional): URL fragment identifier. Defaults to None.
            headers (dict[str, Any], optional): Additional headers to include in the request. Defaults to None.
            follow_redirects (bool, optional): Whether to follow HTTP redirects. Defaults to False.

        Returns:
            Response: The HTTP response.
        """
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
        """Makes a GET request to the specified path with optional query parameters, fragment, headers, and redirect behavior.

        Args:
            path (str | list[str]): The URL path or list of path segments.
            query (dict, optional): Query parameters to include in the URL. Defaults to None.
            fragment (str, optional): URL fragment identifier. Defaults to None.
            headers (dict[str, Any], optional): Additional headers to include in the request. Defaults to None.
            follow_redirects (bool, optional): Whether to follow HTTP redirects. Defaults to False.

        Returns:
            Response: The HTTP response.
        """
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
        """Makes a POST request to the specified path with the given body, optional query parameters, fragment, headers, and content type.

        Args:
            path (str | list[str]): The URL path or list of path segments.
            body (Any): The request body.
            query (dict, optional): Query parameters to include in the URL. Defaults to None.
            fragment (str, optional): URL fragment identifier. Defaults to None.
            headers (dict[str, Any], optional): Additional headers to include in the request. Defaults to None.
            content_type (ContentType, optional): The content type of the request. Defaults to None.

        Returns:
            Response: The HTTP response.
        """
        if content_type is not None:
            if headers is None:
                headers = {}
            else:
                headers = headers.copy()
            headers["Content-Type"] = content_type.value
        return self.request(
            "POST", path, body, query=query, fragment=fragment, headers=headers
        )

    @_lock_method("_lock")
    def add_header(self, key: str, value: str) -> None:
        """Adds a header to the HTTP client.

        Args:
            key (str): The header key.
            value (str): The header value.
        """
        self._headers[key] = value

    @_lock_method("_lock")
    def remove_header(self, key: str) -> Any:
        """Removes a header from the HTTP client.

        Args:
            key (str): The header key.

        Returns:
            Any: The removed header value, or None if the header was not found.
        """
        return self._headers.pop(key, None)

    @_lock_method("_lock")
    def get_headers(self) -> dict[str, Any]:
        """Gets a copy of all headers in the HTTP client.

        Returns:
            dict[str, Any]: A copy of all headers.
        """
        return self._headers.copy()

    @_lock_method("_lock")
    def get_header(self, key: str) -> str | None:
        """Gets the value of a specific header.

        Args:
            key (str): The header key.

        Returns:
            str | None: The header value, or None if the header was not found.
        """
        return self._headers.get(key)

    def set_header(self, key: str, value: str) -> None:
        """Sets the value of a specific header, replacing it if it already exists.

        Args:
            key (str): The header key.
            value (str): The header value.
        """
        self.remove_header(key)
        self.add_header(key, value)

    @_lock_method("_lock")
    def clear_headers(self) -> None:
        """Clears all headers from the HTTP client."""
        self._headers = {}

    @_lock_method("_lock")
    def set_cookie(self, key: str, value: str) -> None:
        """Sets a cookie in the HTTP client.

        Args:
            key (str): The cookie key.
            value (str): The cookie value.
        """
        self._cookies[key] = value

    @_lock_method("_lock")
    def get_cookie(self, key: str) -> str | None:
        """Gets the value of a specific cookie.

        Args:
            key (str): The cookie key.

        Returns:
            str | None: The cookie value, or None if the cookie was not found.
        """
        return self._cookies.get(key)

    @_lock_method("_lock")
    def remove_cookie(self, key: str) -> None:
        """Removes a cookie from the HTTP client.

        Args:
            key (str): The cookie key.
        """
        if key in self._cookies:
            del self._cookies[key]

    def get_lock(self) -> Lock:
        """Gets the lock used for thread-safe operations."""
        return self._lock


class Session(HTTP):
    """A class representing an HTTP session with additional session data."""

    _session_token: str
    additional_data: dict[str, Any]

    def __init__(
        self,
        config: HTTPConfiguration,
        session_token: str = "",
        session_name: str = "JSESSIONID",
    ):
        """Initializes the Session with the given configuration and session token.

        Args:
            config (HTTPConfiguration): The HTTP configuration.
            session_token (str, optional): The session token. Defaults to "".
            session_name (str, optional): The session cookie name. Defaults to "JSESSIONID".
        """
        super().__init__(config)
        self._session_token = session_token
        self.additional_data = {}
        if session_token:
            self.set_cookie(session_name, session_token)

    @classmethod
    def from_http(
        cls, http: HTTP, session_token: str, session_name: str = "JSESSIONID"
    ) -> "Session":
        """Creates a Session instance from an existing HTTP instance.

        Args:
            http (HTTP): The existing HTTP instance.
            session_token (str): The session token.
            session_name (str, optional): The session cookie name. Defaults to "JSESSIONID".

        Returns:
            Session: A new Session instance created from the given HTTP instance.
        """
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
