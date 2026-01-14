"""Configuration options for bootstrapping the user interface."""

from enum import StrEnum
from pathlib import Path


class UIOption(StrEnum):
    """User interface options."""

    INTERACTIVE_CONSOLE = "interactive_console"


class BootstrapOption:
    """Configuration options for bootstrapping the user interface."""

    USER_INTERFACE: str

    PROJECT_DIR: Path
    CONFIG_FILE: Path
    ENV_FILE: Path

    def __init__(self) -> None:
        self.USER_INTERFACE = None
        self.PROJECT_DIR = None
        self.CONFIG_FILE = Path("breg.conf")
        self.ENV_FILE = Path(".env")
