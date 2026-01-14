"""Defines types and interfaces for network operations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from requests import Response as LibResponse


class ContentType(StrEnum):
    """Enumeration of common HTTP content types."""

    FORM_URLENCODED = "application/x-www-form-urlencoded"
    MULTIPART_FORM_DATA = "multipart/form-data"
    JSON = "application/json"


@dataclass(frozen=True)
class Cookie:
    """Represents an HTTP cookie."""

    name: str = ""
    value: str = ""
    domain: str = ""
    expires: str | int | None = None
    http_only: bool = False
    max_age: int | None = None
    partitioned: bool = False
    path: str = ""
    samesite: str = ""
    secure: bool = False


class Response(ABC):
    """Abstract base class for HTTP responses."""

    @abstractmethod
    def status(self) -> int:
        """Returns the HTTP status code of the response.

        Returns:
            int: The HTTP status code.
        """
        pass

    @abstractmethod
    def ok(self) -> bool:
        """Returns True if the HTTP response status code indicates success.

        Returns:
            bool: True if the response is successful, False otherwise.
        """
        pass

    @abstractmethod
    def reason(self) -> str:
        """Returns the reason phrase of the HTTP response.

        Returns:
            str: The reason phrase of the HTTP response.
        """
        pass

    @abstractmethod
    def get_headers(self) -> dict[str, str]:
        """Returns the headers of the HTTP response.

        Returns:
            dict[str, str]: The headers of the HTTP response.
        """
        pass

    @abstractmethod
    def get_header(self, key: str, default: str | None = None) -> str | None:
        """Returns the value of a specific header from the HTTP response.

        Args:
            key (str): The header key.
            default (str | None, optional): The default value to return if the header is not found. Defaults to None.

        Returns:
            str | None: The value of the specified header, or the default value if not found.
        """
        pass

    @abstractmethod
    def text(self) -> str:
        """Returns the response body as a string.

        Returns:
            str: The response body as a string.
        """
        pass

    @abstractmethod
    def json(self) -> Any:
        """Returns the response body parsed as JSON.

        Returns:
            Any: The response body parsed as JSON.
        """
        pass

    @abstractmethod
    def raw(self) -> bytes:
        """Returns the raw response body as bytes.

        Returns:
            bytes: The raw response body as bytes.
        """
        pass

    @abstractmethod
    def get_cookie(self, name: str) -> Cookie | None:
        """Returns a specific cookie from the HTTP response.

        Args:
            name (str): The name of the cookie.

        Returns:
            Cookie | None: The cookie with the specified name, or None if not found.
        """
        pass

    @abstractmethod
    def get_cookies(self) -> dict[str, Cookie]:
        """Returns all cookies from the HTTP response.

        Returns:
            dict[str, Cookie]: A dictionary of all cookies from the HTTP response.
        """
        pass


class LibReqResponse(Response):
    """Concrete implementation of the Response interface using the requests library."""

    _response: LibResponse
    _cookies: dict[str, Cookie] | None = None

    def __init__(self, response: LibResponse) -> None:
        self._response = response

    def status(self) -> int:
        return self._response.status_code

    def ok(self) -> bool:
        return self._response.ok

    def reason(self) -> str:
        return self._response.reason

    def get_headers(self) -> dict[str, str]:
        return self._response.headers

    def get_header(self, key: str, default: str | None = None) -> str | None:
        return self._response.headers.get(key, default)

    def text(self) -> str:
        return self._response.text

    def json(self) -> Any:
        return self._response.json()

    def raw(self) -> bytes:
        return self._response.content

    def get_cookie(self, name: str) -> Cookie | None:
        return self.get_cookies().get(name, None)

    def get_cookies(self) -> dict[str, Cookie]:
        if self._cookies is not None:
            return self._cookies

        cookies: dict[str, Cookie] = {}
        for jar_cookie in self._response.cookies:
            cookies[jar_cookie.name] = Cookie(
                name=jar_cookie.name,
                value=jar_cookie.value,
                domain=jar_cookie.domain,
                expires=jar_cookie.expires,
                http_only=jar_cookie._rest.get("HttpOnly", False)
                if getattr(jar_cookie, "_rest") is dict
                else False,
                max_age=None,
                partitioned=jar_cookie._rest.get("Partitioned", False)
                if getattr(jar_cookie, "_rest") is dict
                else False,
                path=jar_cookie.path,
                samesite=jar_cookie._rest.get("SameSite", "")
                if getattr(jar_cookie, "_rest") is dict
                else "",
                secure=jar_cookie.secure,
            )

        self._cookies = cookies
        return cookies
