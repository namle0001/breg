"""Interactive Console Session Module"""

import concurrent.futures
import importlib.util
from typing import Any, Callable, Literal, TypedDict
from uuid import uuid4

import IPython

from breg.config.config import Configuration
from breg.config.env import Environment
from breg.core.database import SQLite
from breg.core.filesystem.filesystem import Filesystem
from breg.core.network.net import Session as NetworkSession
from breg.macro import (
    CacheMacro,
    ExecuteMacro,
    FetchAndSaveMacro,
    PlanMacro,
    ThreadedExecuteMacro,
)
from breg.macro.session import SessionMacro
from breg.processor import (
    Authenticator,
    Executor,
    Fetcher,
    RoundMananger,
    SchedulePlanner,
)
from breg.runtime.context import RuntimeContext
from breg.type.data import ClassCache, Round

from .format import format_classes_schedules, format_rounds, format_seeds


class InteractiveConsoleSession:
    """Interactive Console Session Class"""

    _runtime_context: RuntimeContext
    _macro_manager: "MacroManager"
    _namespace: "Namespace"

    def __init__(
        self,
        config: Configuration,
        env: Environment,
        project_fs: Filesystem,
        inst_fs: Filesystem,
    ) -> None:
        self._runtime_context = RuntimeContext(
            project_fs=project_fs,
            inst_fs=inst_fs,
            config=config,
            env=env,
        )
        self._macro_manager = MacroManager(self._runtime_context)
        self._runtime_context.initialize_processors(
            [SchedulePlanner, Executor, Fetcher, RoundMananger]
        )

    def initialize_namespace(self) -> None:
        """Initialize the interactive console namespace."""
        self._namespace = Namespace()

        self._namespace.import_namespace(
            InteractiveConsoleSession,
            object_instance=self,
            only_callable=True,
            # inject_self=True,  # DEBUG
        )

        self._namespace.import_namespace(
            MacroManager,
            object_instance=self._macro_manager,
            only_callable=True,
        )

    def start_session(self):
        """Start the interactive console session."""
        IPython.start_ipython(user_ns=self._namespace.copy())

    def validate_token(self) -> bool:
        """Validate the access token.

        Returns:
            bool: True if the access token is valid, False otherwise.
        """
        return Authenticator(
            context=self._runtime_context.processor_context()
        ).validate_access_token()

    class ScriptInfo(TypedDict):
        """TypedDict for script information.

        Attributes:
            script_path (str): The path to the script file.
            entry_func (str): The entry function to execute in the script.
            background (bool): Whether to run the script in the background.
        """

        script_path: str
        entry_func: str
        background: bool

    def execute_script(
        self, script_info: ScriptInfo, *args, **kwargs
    ) -> Any | concurrent.futures.Future:
        """Execute a script based on the provided script information.
        If 'background' is set to True, the script will be executed in a separate thread.

        Args:
            script_info (ScriptInfo): Information about the script to execute.

        Raises:
            FileNotFoundError: If the script file is not found.

        Returns:
            Any | concurrent.futures.Future: The result of the script execution or a Future if run in the background.
        """
        script_info.setdefault("entry_func", "main")
        script_info.setdefault("background", False)

        path = self._runtime_context.project_fs().path(script_info["script_path"])
        if not path.exists():
            # Attempt to look for built-in scripts
            path = self._runtime_context.inst_fs().path(
                "template/script", script_info["script_path"]
            )
        if not path.exists():
            raise FileNotFoundError(
                f"Script file not found: {script_info['script_path']}"
            )

        module_name = f"__script_{path.name}_{uuid4().hex}__"
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)

        for key, value in self._namespace.items():
            setattr(module, key, value)

        entrypoint = getattr(module, script_info["entry_func"])

        spec.loader.exec_module(module)
        if script_info["background"]:
            return concurrent.futures.ThreadPoolExecutor().submit(
                entrypoint, *args, **kwargs
            )
        else:
            return entrypoint(*args, **kwargs)

    def authenticate(self) -> NetworkSession | None:
        """Authenticate and initialize a new network session.

        Returns:
            NetworkSession | None: The previous network session before re-authentication if any.
        """
        old_session = self._runtime_context.processor_context().session
        self._runtime_context.initialize_cores(
            net_session=Authenticator(
                context=self._runtime_context.processor_context()
            ).authenticate()
        )
        return old_session

    def load_db(self) -> None:
        """Load the SQLite databases for cache and enrollment."""
        config = self._runtime_context.config()
        filesystem = self._runtime_context.project_fs()
        self._runtime_context.initialize_cores(
            db=SQLite(
                filesystem.path(config.DB_SQLITE_CACHE_PATH),
                filesystem.path(config.DB_SQLITE_ENROLLMENT_PATH),
            )
        )

    def reload(self) -> None:
        """Reload all processors in the runtime context."""
        self._runtime_context.reload_processors()

    ## Display Methods

    def print_schedules(
        self, class_caches: list[ClassCache], tablefmt: str = "simple_grid"
    ) -> None:
        """Print formatted class schedules.

        Args:
            class_caches (list[ClassCache]): List of class caches to format and print.
            tablefmt (str, optional): Table format for printing. Defaults to "simple_grid".
        """
        formatted = format_classes_schedules(class_caches, tablefmt=tablefmt)
        print(formatted)

    def print_rounds(
        self,
        rounds: list[Round],
        tablefmt: str = "simple_grid",
        limit: int = 10,
        sort: Literal["asc", "desc"] = "asc",
    ) -> None:
        """Print formatted rounds.
        The rows are truncated and then sorted based on its appearance in the list.
        Entry which appears earlier in the list is being later in a timeline (bigger timestamp).
        The default sort order will reverse the whole list.

        Args:
            rounds (list[Round]): List of rounds to format and print.
            tablefmt (str, optional): Table format for printing. Defaults to "simple_grid".
            limit (int, optional): Maximum number of rounds to print. Defaults to 10.
            sort (Literal["asc", "desc"], optional): Sort order for rounds. Defaults to "asc".
        """
        formatted = format_rounds(rounds, tablefmt=tablefmt, sort=sort, limit=limit)
        print(formatted)

    def print_seeds(self, seeds: list[Round], tablefmt: str = "simple_grid") -> None:
        """Print formatted seeds.

        Args:
            seeds (list[Round]): List of seeds to format and print.
            tablefmt (str, optional): Table format for printing. Defaults to "simple_grid".
        """
        formatted = format_seeds(seeds, tablefmt=tablefmt)
        print(formatted)

    ## Configuration and Environment Management Methods

    def setconf(self, key: str, value: str) -> None:
        """Set a configuration value.

        Args:
            key (str): Configuration key to set.
            value (str): Value to set for the configuration key.

        Raises:
            AttributeError: If the configuration key does not exist.
        """
        if not hasattr(self._runtime_context.config, key):
            raise AttributeError(f"Configuration has no attribute '{key}'")
        setattr(self._runtime_context.config, key, value)

    def getconf(self, key: str) -> str:
        """Get a configuration value.

        Args:
            key (str): Configuration key to get.

        Raises:
            AttributeError: If the configuration key does not exist.

        Returns:
            str: Value of the configuration key.
        """
        if not hasattr(self._runtime_context.config, key):
            raise AttributeError(f"Configuration has no attribute '{key}'")
        return getattr(self._runtime_context.config, key)

    def setenv(self, key: str, value: str) -> None:
        """Set an environment variable.

        Args:
            key (str): Environment variable key to set.
            value (str): Value to set for the environment variable.

        Raises:
            AttributeError: If the environment variable key does not exist.
        """
        if not hasattr(self._runtime_context.env, key):
            raise AttributeError(f"Environment has no attribute '{key}'")
        setattr(self._runtime_context.env, key, value)

    def getenv(self, key: str) -> str:
        """Get an environment variable.

        Args:
            key (str): Environment variable key to get.

        Raises:
            AttributeError: If the environment variable key does not exist.

        Returns:
            str: Value of the environment variable.
        """
        if not hasattr(self._runtime_context.env, key):
            raise AttributeError(f"Environment has no attribute '{key}'")
        return getattr(self._runtime_context.env, key)


class MacroManager:
    """Macro Manager Class"""

    _cache: CacheMacro
    _fetch_and_save: FetchAndSaveMacro
    _plan: PlanMacro
    _execute: ExecuteMacro
    _threaded_execute: ThreadedExecuteMacro
    _session: SessionMacro

    def __init__(self, runtime_context: RuntimeContext):
        self._cache = CacheMacro(runtime_context)
        self._fetch_and_save = FetchAndSaveMacro(runtime_context)
        self._plan = PlanMacro(runtime_context)
        self._execute = ExecuteMacro(runtime_context)
        self._threaded_execute = ThreadedExecuteMacro(runtime_context)
        self._session = SessionMacro(runtime_context)

    def cache(self) -> CacheMacro:
        """Get the CacheMacro"""
        return self._cache

    def cfetch(self) -> FetchAndSaveMacro:
        """Get the FetchAndSaveMacro"""
        return self._fetch_and_save

    def plan(self) -> PlanMacro:
        """Get the PlanMacro"""
        return self._plan

    def execute(self) -> ExecuteMacro:
        """Get the ExecuteMacro"""
        return self._execute

    def texecute(self) -> ThreadedExecuteMacro:
        """Get the ThreadedExecuteMacro"""
        return self._threaded_execute

    def session(self) -> SessionMacro:
        """Get the SessionMacro"""
        return self._session


class Namespace(dict):
    """Namespace Class"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def import_namespace(
        self,
        namespace: Any,
        object_instance: Any | None = None,
        only_callable: bool = False,
        ignore_protected: bool = True,
        ignore_private: bool = True,
        ignore_dunder: bool = True,
        inject_self: bool = False,
    ) -> None:
        """Import attributes from a given namespace into the current namespace instance.

        Args:
            namespace (object): The namespace object to import attributes from.
            object_instance (object | None, optional): The instance of the object to bind methods to. Defaults to None.
            only_callable (bool, optional): Whether to import only callable attributes. Defaults to False.
            ignore_protected (bool, optional): Whether to ignore protected attributes (starting with a single underscore). Defaults to True.
            ignore_private (bool, optional): Whether to ignore private attributes (starting with double underscores but not ending with double underscores). Defaults to True.
            ignore_dunder (bool, optional): Whether to ignore dunder (double underscore) attributes. Defaults to True.
            inject_self (bool, optional): Whether to inject the object_instance or namespace as 'self'. Defaults to False.
        """
        if inject_self:
            self.inject(
                "self", object_instance if object_instance is not None else namespace
            )

        for attr_name in dir(namespace):
            attr = getattr(namespace, attr_name)
            if only_callable and not callable(attr):
                continue

            if (
                (
                    ignore_protected
                    and attr_name.startswith("_")
                    and not attr_name.startswith("__")
                )
                or (
                    ignore_private
                    and attr_name.startswith("__")
                    and not attr_name.endswith("__")
                )
                or (
                    ignore_dunder
                    and attr_name.startswith("__")
                    and attr_name.endswith("__")
                )
            ):
                continue

            if isinstance(attr, type):
                continue

            if callable(attr) and object_instance is not None:
                self.inject_method(
                    attr,
                    method_name=attr_name,
                    object_instance=object_instance,
                )
            else:
                self.inject(
                    attr_name,
                    getattr(object_instance, attr_name) if object_instance else attr,
                )

    def inject(self, name: str, value: Any) -> None:
        """Inject a value into the namespace.

        Args:
            name (str): The name of the value to inject.
            value (object): The value to inject.
        """
        self[name] = value

    def inject_method(
        self,
        method: Callable | list[Callable],
        method_name: str | None = None,
        object_instance: Any | None = None,
    ) -> None:
        """Inject a method into the namespace.
        Binds the method to the given object instance if provided.

        Args:
            method (Callable | list[Callable]): The method or list of methods to inject.
            method_name (str | None, optional): The name to use for the injected method. Defaults to None.
            object_instance (object | None, optional): The instance to bind the method to. Defaults to None.
        """
        if isinstance(method, list):
            for m in method:
                self.inject_method(m)
            return
        if object_instance is not None:
            method = method.__get__(object_instance, object_instance.__class__)

        self[method_name or method.__name__] = method

    def withdraw(self, name: str | list[str] | Any | list[Any]) -> None:
        """Withdraw a value from the namespace.

        Args:
            name (str | list[str] | Any | list[Any]): The name or list of names of the values to withdraw, or the value(s) themselves.
        """
        if isinstance(name, list):
            for n in name:
                self.withdraw(n)
            return

        if isinstance(name, str):
            self.pop(name, None)
            return

        for key, value in list(self.items()):
            if value == name:
                self.pop(key)
                return

    def contains(self, name: str | Any) -> bool:
        """Check if the namespace contains a value.

        Args:
            name (str | Any): The name of the value or the value itself to check.

        Returns:
            bool: True if the value is in the namespace, False otherwise.
        """
        if isinstance(name, str):
            return name in self

        return any(value == name for value in self.values())
