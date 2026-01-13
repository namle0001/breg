from argparse import ArgumentParser
from pathlib import Path

from .option import BootstrapOption, UIOption
from breg.bootstrap.interactive_console import (
    bootstrap as interactive_console_bootstrap,
)


def bootstrap():
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--project-dir", required=True, help="Path to the project directory"
    )
    parser.add_argument("-c", "--config", help="Path to the configuration file")
    parser.add_argument("-e", "--env", help="Path to the environment file")
    parser.add_argument(
        "-i", action="store_true", help="Start interactive console after bootstrapping"
    )
    parser.add_argument(
        "--ui-option", choices=["interactive_console"], help="User interface option"
    )
    parser.add_argument("extra_args", nargs="*")

    args = parser.parse_args()

    option = BootstrapOption()

    option.PROJECT_DIR = Path(args.project_dir)
    option.CONFIG_FILE = args.config or option.CONFIG_FILE
    option.ENV_FILE = args.env or option.ENV_FILE
    extra_args = args.extra_args

    if args.ui_option == UIOption.INTERACTIVE_CONSOLE or args.i:
        option.USER_INTERFACE = UIOption.INTERACTIVE_CONSOLE

    match option.USER_INTERFACE:
        case UIOption.INTERACTIVE_CONSOLE:
            interactive_console_bootstrap(option, extra_args=extra_args)
        case _:
            raise ValueError("No valid user interface option provided")


if __name__ == "__main__":
    bootstrap()
