from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from requests import Response as LibResponse


class ContentType(StrEnum):
    FORM_URLENCODED = "application/x-www-form-urlencoded"
    MULTIPART_FORM_DATA = "multipart/form-data"
    JSON = "application/json"


@dataclass(frozen=True)
class Cookie:
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
    @abstractmethod
    def status(self) -> int:
        pass

    @abstractmethod
    def ok(self) -> bool:
        pass

    @abstractmethod
    def reason(self) -> str:
        pass

    @abstractmethod
    def get_headers(self) -> dict[str, str]:
        pass

    @abstractmethod
    def get_header(self, key: str, default: str | None = None) -> str | None:
        pass

    @abstractmethod
    def text(self) -> str:
        pass

    @abstractmethod
    def json(self) -> Any:
        pass

    @abstractmethod
    def raw(self) -> bytes:
        pass

    @abstractmethod
    def get_cookie(self, name: str) -> Cookie | None:
        pass

    @abstractmethod
    def get_cookies(self) -> dict[str, Cookie]:
        pass


class LibReqResponse(Response):
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
