from enum import StrEnum
from pathlib import Path


class UIOption(StrEnum):
    INTERACTIVE_CONSOLE = "interactive_console"


class BootstrapOption:
    USER_INTERFACE: str = None

    PROJECT_DIR: Path = None
    CONFIG_FILE: Path = Path("breg.conf")
    ENV_FILE: Path = Path(".env")
