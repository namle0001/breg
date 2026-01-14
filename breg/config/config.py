"""Configuration module for the application."""

from dataclasses import dataclass
from typing import TypedDict


@dataclass
class Configuration:
    """General configuration for the application."""

    CONFIG_NAME: str = None
    CONFIG_VERSION: str = None

    PORT: int = None
    HTTPS: bool = None

    USER_AGENT: str = None

    AUTH_SERVICE: str = None
    AUTH_SERVICE_HOSTNAME: str = None
    AUTH_SERVICE_PATH: str = None
    AUTH_SERVICE_URL: str = None
    AUTH_SERVICE_TOKEN_NAME: str = None
    AUTH_SERVICE_QUERY_SERVICE_NAME: str = None
    AUTH_SERVICE_QUERY_RESPONSE_TICKET_NAME: str = None

    TARGET_SERVICE: str = None
    TARGET_SERVICE_HOSTNAME: str = None
    TARGET_SERVICE_PATH: str = None
    TARGET_SERVICE_URL: str = None
    TARGET_SERVICE_AUTH_PATH: str = None
    TARGET_SERVICE_TICKET_NAME: str = None
    TARGET_SERVICE_SESSION_NAME: str = None

    TARGET_FETCH_ROUNDS_PATH: str = None
    TARGET_FETCH_SEEDS_PATH: str = None
    TARGET_SWITCH_ROUND_PATH: str = None
    TARGET_SWITCH_SEED_PATH: str = None
    TARGET_REGISTER_PATH: str = None
    TARGET_UNREGISTER_PATH: str = None
    TARGET_FETCH_ENROLLMENTS_PATH: str = None
    TARGET_FETCH_COURSES_PATH: str = None
    TARGET_FETCH_CLASSES_PATH: str = None

    ROUND_NAME: str = None
    SEED_NAME: str = None
    COURSE_CODE_NAME: str = None
    COURSE_ID_NAME: str = None
    CLASS_ID_NAME: str = None
    ENROLLMENT_ID_NAME: str = None

    DB_SQLITE_CACHE_PATH: str = None
    DB_SQLITE_ENROLLMENT_PATH: str = None

    def ensure_types(self) -> None:
        """Ensure that all configuration attributes have the correct types."""
        self.PORT = int(self.PORT)
        self.HTTPS = bool(self.HTTPS)


class AuthServiceConfig(TypedDict):
    name: str
    hostname: str
    path: str
    url: str
    token_name: str
    query_service_name: str
    query_response_ticket_name: str


class TargetServiceConfig(TypedDict):
    name: str
    hostname: str
    path: str
    url: str
    auth_path: str
    ticket_name: str
    session_name: str

    fetch_rounds_path: str
    fetch_seeds_path: str
    switch_round_path: str
    switch_seed_path: str
    register_path: str
    unregister_path: str
    fetch_enrollments_path: str
    fetch_courses_path: str
    fetch_classes_path: str


class NetworkNameConfig(TypedDict):
    round: str
    seed: str
    course_code: str
    course_id: str
    class_id: str
    enrollment_id: str


class DbSqliteConfig(TypedDict):
    cache_path: str
    enrollment_path: str


class DatabaseConfig(TypedDict):
    sqlite: DbSqliteConfig


class NameConfig(TypedDict):
    network: NetworkNameConfig


class ServiceConfig(TypedDict):
    auth: AuthServiceConfig
    target: TargetServiceConfig


class NewConfig(TypedDict):
    config_name: str
    config_version: str
    port: int
    https: bool
    user_agent: str

    service: ServiceConfig
    network: NameConfig
    database: DatabaseConfig


class HTTPConfiguration:
    """HTTP-specific configuration for network communication."""

    HOSTNAME: str
    PORT: int
    HTTPS: bool
    USER_AGENT: str

    def __init__(
        self,
        HOSTNAME: str = None,
        PORT: int = None,
        HTTPS: bool = None,
        USER_AGENT: str = None,
    ):
        self.HOSTNAME = HOSTNAME
        self.PORT = PORT
        self.HTTPS = HTTPS
        self.USER_AGENT = USER_AGENT

    @classmethod
    def from_auth(cls, config: Configuration) -> "HTTPConfiguration":
        return auth_to_http_config(config)

    @classmethod
    def from_target(cls, config: Configuration) -> "HTTPConfiguration":
        return target_to_http_config(config)


def auth_to_http_config(config: Configuration) -> HTTPConfiguration:
    """Convert general configuration to HTTP configuration for the auth service.

    Args:
        config (Configuration): The general configuration object.

    Returns:
        HTTPConfiguration: The general configuration object.
    """
    return HTTPConfiguration(
        HOSTNAME=config.AUTH_SERVICE_HOSTNAME,
        PORT=config.PORT,
        HTTPS=config.HTTPS,
        USER_AGENT=config.USER_AGENT,
    )


def target_to_http_config(config: Configuration) -> HTTPConfiguration:
    """Convert general configuration to HTTP configuration for the target service.

    Args:
        config (Configuration): The general configuration object.

    Returns:
        HTTPConfiguration: The general configuration object.
    """
    return HTTPConfiguration(
        HOSTNAME=config.TARGET_SERVICE_HOSTNAME,
        PORT=config.PORT,
        HTTPS=config.HTTPS,
        USER_AGENT=config.USER_AGENT,
    )
