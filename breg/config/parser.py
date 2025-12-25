"""Module for parsing configuration and environment data."""

from typing import TypeVar

from breg.config.config import Configuration
from breg.config.env import Environment

T = TypeVar("T")


def parse_key_value_file(file_path: str, cls: T) -> T:
    """Parse a simple key-value pair file into an instance of the given class.

    Args:
        file_path (str): Path to the key-value pair file.
        cls (T): The class type to instantiate and populate.

    Returns:
        T: An instance of the given class populated with values from the file.
    """
    obj = cls()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("#") or not line.strip():
                continue
            key, value = line.strip().split("=", 1)
            if hasattr(obj, key):
                setattr(obj, key, value)
    return obj


def load_configuration(file_path: str) -> Configuration:
    """Load configuration from a key-value pair file.

    Args:
        file_path (str): Path to the configuration file.

    Returns:
        Configuration: The loaded configuration object.
    """
    conf = parse_key_value_file(file_path, Configuration)
    conf.ensure_types()
    return conf


def load_environment(file_path: str) -> Environment:
    """Load environment variables from a key-value pair file.

    Args:
        file_path (str): Path to the environment file.

    Returns:
        Environment: The loaded environment object.
    """
    return parse_key_value_file(file_path, Environment)
