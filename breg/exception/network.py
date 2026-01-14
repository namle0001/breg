"""Module defining custom exceptions for network-related errors."""


class NetworkException(Exception):
    """Base exception for network-related errors."""


class UnauthorizedException(NetworkException):
    """Exception raised for unauthorized access (HTTP 401)."""


class NotFoundException(NetworkException):
    """Exception raised when a resource is not found (HTTP 404)."""


class ServerErrorException(NetworkException):
    """Exception raised for server errors (HTTP 5xx)."""


class NetworkSoftFailException(NetworkException):
    """Exception raised for ambiguous network failures which cannot be determined as success or failure."""
