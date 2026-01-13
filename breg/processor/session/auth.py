from urllib.parse import parse_qs, urlparse

from breg.config.config import auth_to_http_config, target_to_http_config
from breg.core.network import HTTP, Session
from breg.exception.network import NetworkException

from ..base import Processor


class Authenticator(Processor):
    def validate_access_token(self) -> bool:
        request = HTTP(auth_to_http_config(self._context.config))
        self.attach_token(request)
        response = request.get(
            self._context.config.AUTH_SERVICE_PATH,
            query={
                self._context.config.AUTH_SERVICE_QUERY_SERVICE_NAME: self._context.config.TARGET_SERVICE
            },
        )

        return response.status() == 302  # Check for redirection

    def authenticate(self) -> Session:
        ticket = self._retrieve_ticket()
        if not ticket:
            raise NetworkException("Authentication failed: No ticket found.")

        session = self._create_session(ticket)
        session.remove_cookie(self._context.config.AUTH_SERVICE_TOKEN_NAME)
        session.get(self._context.config.TARGET_SERVICE_AUTH_PATH)

        return session

    def is_authenticated(self, http: HTTP) -> bool:
        response = http.get(self._context.config.TARGET_SERVICE_AUTH_PATH)
        if self._context.config.AUTH_SERVICE_HOSTNAME in response.get_header(
            "Location", ""
        ):
            return False
        return True

    def attach_token(self, http: HTTP) -> None:
        http.set_cookie(
            self._context.config.AUTH_SERVICE_TOKEN_NAME, self._context.env.ACCESS_TOKEN
        )

    def _retrieve_ticket(self) -> str:
        request = HTTP(auth_to_http_config(self._context.config))
        self.attach_token(request)
        response = request.get(
            self._context.config.AUTH_SERVICE_PATH,
            query={
                self._context.config.AUTH_SERVICE_QUERY_SERVICE_NAME: self._context.config.TARGET_SERVICE
            },
        )

        if response.get_header("Location") is None:
            raise NetworkException(
                f"Authentication failed: No redirection URL found. HTTP {response.status()}"
            )

        ticket = parse_qs(urlparse(response.get_header("Location")).query).get(
            self._context.config.AUTH_SERVICE_QUERY_RESPONSE_TICKET_NAME, [None]
        )[0]

        return ticket

    def _create_session(self, ticket: str) -> Session:
        request = HTTP(target_to_http_config(self._context.config))
        response = request.get(
            self._context.config.TARGET_SERVICE_AUTH_PATH,
            query={self._context.config.TARGET_SERVICE_TICKET_NAME: ticket},
        )

        if response.status() >= 500 and response.status() < 600:
            raise NetworkException(
                f"Authentication failed: Server error with status code {response.status()}."
            )

        session_id = response.get_cookie(
            self._context.config.TARGET_SERVICE_SESSION_NAME
        )

        if not session_id:
            raise NetworkException(
                f"Authentication failed: No session id found in the response. HTTP {response.status()}"
            )

        return Session.from_http(request, session_id.value)
