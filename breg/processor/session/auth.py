from urllib.parse import parse_qs, urlparse

from breg.config.config import Configuration, auth_to_http_config, target_to_http_config
from breg.config.env import Environment
from breg.core.network.net import HTTP, Session, parse_set_cookie_headers
from breg.exception.network import NetworkException


class Authenticator:
    _config: Configuration
    _env: Environment

    def __init__(self, config: Configuration, env: Environment) -> None:
        self._config = config
        self._env = env

    def authenticate(self) -> Session:
        retrieve_ticket_request = HTTP(auth_to_http_config(self._config))
        retrieve_ticket_request.set_cookie(
            self._config.AUTH_SERVICE_TOKEN_NAME, self._env.ACCESS_TOKEN
        )
        response = retrieve_ticket_request.get(
            self._config.AUTH_SERVICE_PATH,
            query={
                self._config.AUTH_SERVICE_QUERY_SERVICE_NAME: self._config.TARGET_SERVICE
            },
        )

        if response.getheader("Location") is None:
            raise NetworkException(
                f"Authentication failed: No redirection URL found. HTTP {response.getcode()}"
            )

        ticket = parse_qs(urlparse(response.getheader("Location")).query).get(
            self._config.AUTH_SERVICE_QUERY_RESPONSE_TICKET_NAME, [None]
        )[0]

        if not ticket:
            raise NetworkException(
                "Authentication failed: No ticket found in the redirection URL."
            )

        http = HTTP(target_to_http_config(self._config))
        res = http.get(
            self._config.TARGET_SERVICE_AUTH_PATH,
            query={self._config.TARGET_SERVICE_TICKET_NAME: ticket},
        )

        if res.getcode() >= 500 and res.getcode() < 600:
            raise NetworkException(
                f"Authentication failed: Server error with status code {res.getcode()}."
            )
        if not res.getheader("Set-Cookie"):
            raise NetworkException(
                f"Authentication failed: No 'Set-Cookie' header found in the response. HTTP {res.getcode()}"
            )

        session_token = parse_set_cookie_headers(
            [header[1] for header in res.getheaders() if header[0] == "Set-Cookie"]
        ).get(self._config.TARGET_SERVICE_SESSION_NAME)

        if not session_token:
            raise NetworkException(
                f"Authentication failed: No session token found in the response. HTTP {res.getcode()}"
            )

        session = Session.from_http(http, session_token)
        session.get(self._config.TARGET_SERVICE_AUTH_PATH)
        return session
