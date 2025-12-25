"""Configuration module for the application."""


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

    def ensure_types(self):
        """Ensure that all configuration attributes have the correct types."""
        self.PORT = int(self.PORT)
        self.HTTPS = bool(self.HTTPS)


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
