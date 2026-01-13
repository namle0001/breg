"""Environment variables module."""

from dataclasses import dataclass


@dataclass
class Environment:
    """Environment variables"""

    ACCESS_TOKEN: str = None
