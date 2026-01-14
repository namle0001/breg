from .option import BootstrapOption

from breg.config.parser import load_configuration, load_environment
from breg.ui.interactive_console import InteractiveConsoleSession
from breg.core.filesystem import Filesystem
from pathlib import Path


def bootstrap(option: BootstrapOption, extra_args: list[str] | None = None) -> None:
    """Bootstrap the interactive console user interface.

    Args:
        option (BootstrapOption): Configuration options for bootstrapping.
        extra_args (list[str] | None, optional): Additional arguments for bootstrapping. Defaults to None.
    """
    project_fs = Filesystem(option.PROJECT_DIR)
    inst_fs = Filesystem(
        Path(
            __file__
        ).parent.parent.parent  # Point to the root directory of the project
    )  # Warning: __file__ differs as the file calling it changes
    config = load_configuration(project_fs.base() / option.CONFIG_FILE)
    env = load_environment(project_fs.base() / option.ENV_FILE)
    console = InteractiveConsoleSession(
        project_fs=project_fs, inst_fs=inst_fs, config=config, env=env
    )

    if extra_args is None:
        extra_args = []
    if "autoauth" in extra_args:
        if not console.validate_token():
            print("Access token is invalid or expired. Please update your token.")
            return
        console.authenticate_and_reload()

    if "noloaddb" not in extra_args:
        console.load_db()

    console.initialize_namespace()
    console.start_session()
