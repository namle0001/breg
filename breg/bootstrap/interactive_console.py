from .option import BootstrapOption

from breg.config.parser import load_configuration, load_environment
from breg.ui.interactive_console import InteractiveConsoleSession


def bootstrap(option: BootstrapOption) -> None:
    config = load_configuration(option.CONFIG_FILE)
    env = load_environment(option.ENV_FILE)
    console = InteractiveConsoleSession(config, env)

    console.authenticate_and_reload()

    console.initialize_namespace()
    console.start_session()
