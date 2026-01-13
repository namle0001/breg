import IPython
from typing import Callable
import importlib.util

from uuid import uuid4

from breg.core.database import SQLite
from breg.core.filesystem.filesystem import Filesystem
from breg.core.network.net import Session as NetworkSession
from breg.config.config import Configuration
from breg.config.env import Environment
from breg.macro.session import SessionMacro
from breg.runtime.context import RuntimeContext
from breg.macro import (
    CacheMacro,
    ExecuteMacro,
    FetchAndSaveMacro,
    PlanMacro,
    ThreadedExecuteMacro,
)

from breg.processor import (
    Authenticator,
    Executor,
    Fetcher,
    RoundMananger,
    SchedulePlanner,
)
from breg.type.data import ClassCache

from .format import format_classes_schedules


class InteractiveConsoleSession:
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
        IPython.start_ipython(user_ns=self._namespace.copy())

    def validate_token(self) -> bool:
        return Authenticator(
            context=self._runtime_context.processor_context()
        ).validate_access_token()

    def execute_script(
        self, script_path: str, entry_func: str = "main", *args, **kwargs
    ) -> None:
        path = self._runtime_context.project_fs().path(script_path)
        if not path.exists():
            # Attempt to look for built-in scripts
            path = self._runtime_context.inst_fs().path("template/script", script_path)
        if not path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")

        module_name = f"__script_{path.name}_{uuid4().hex}__"
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)

        for key, value in self._namespace.items():
            setattr(module, key, value)

        spec.loader.exec_module(module)

        return getattr(module, entry_func)(*args, **kwargs)

    def authenticate_and_reload(self) -> None:
        self.authenticate()
        self.reload()

    def authenticate(self) -> NetworkSession | None:
        old_session = self._runtime_context.processor_context().session
        self._runtime_context.initialize_cores(
            net_session=Authenticator(
                context=self._runtime_context.processor_context()
            ).authenticate()
        )
        return old_session

    def load_db(self) -> None:
        config = self._runtime_context.config()
        filesystem = self._runtime_context.project_fs()
        self._runtime_context.initialize_cores(
            db=SQLite(
                filesystem.path(config.DB_SQLITE_CACHE_PATH),
                filesystem.path(config.DB_SQLITE_ENROLLMENT_PATH),
            )
        )

    def reload(self) -> None:
        self._runtime_context.reload_processors()

    def print_schedules(
        self, class_caches: list[ClassCache], tablefmt: str = "simple_grid"
    ) -> None:
        formatted = format_classes_schedules(class_caches, tablefmt=tablefmt)
        print(formatted)

    ## Configuration and Environment Management Methods

    def setconf(self, key: str, value: str) -> None:
        if not hasattr(self._runtime_context.config, key):
            raise AttributeError(f"Configuration has no attribute '{key}'")
        setattr(self._runtime_context.config, key, value)

    def getconf(self, key: str) -> str:
        if not hasattr(self._runtime_context.config, key):
            raise AttributeError(f"Configuration has no attribute '{key}'")
        return getattr(self._runtime_context.config, key)

    def setenv(self, key: str, value: str) -> None:
        if not hasattr(self._runtime_context.env, key):
            raise AttributeError(f"Environment has no attribute '{key}'")
        setattr(self._runtime_context.env, key, value)

    def getenv(self, key: str) -> str:
        if not hasattr(self._runtime_context.env, key):
            raise AttributeError(f"Environment has no attribute '{key}'")
        return getattr(self._runtime_context.env, key)


class MacroManager:
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
        return self._cache

    def cfetch(self) -> FetchAndSaveMacro:
        return self._fetch_and_save

    def plan(self) -> PlanMacro:
        return self._plan

    def execute(self) -> ExecuteMacro:
        return self._execute

    def texecute(self) -> ThreadedExecuteMacro:
        return self._threaded_execute

    def session(self) -> SessionMacro:
        return self._session


class Namespace(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def import_namespace(
        self,
        namespace: object,
        object_instance: object | None = None,
        only_callable: bool = False,
        ignore_protected: bool = True,
        ignore_private: bool = True,
        ignore_dunder: bool = True,
        inject_self: bool = False,
    ) -> None:
        if inject_self:
            self.inject(
                "self", object_instance if object_instance is not None else namespace
            )

        dir(namespace)
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

    def inject(self, name: str, value: object) -> None:
        self[name] = value

    def inject_method(
        self,
        method: Callable | list[Callable],
        method_name: str | None = None,
        object_instance: object | None = None,
    ) -> None:
        if isinstance(method, list):
            for m in method:
                self.inject_method(m)
            return
        if object_instance is not None:
            method = method.__get__(object_instance, object_instance.__class__)

        self[method_name or method.__name__] = method

    def withdraw_method(
        self,
        method: Callable | str | list[Callable | str],
    ) -> Callable | None:
        if isinstance(method, list):
            for m in method:
                self.withdraw_method(m)
            return

        if isinstance(method, str):
            return self.pop(method)

        return self.pop(name for name, m in self.items() if m == method)

    def has_method(self, method: Callable | staticmethod | str) -> bool:
        if isinstance(method, str):
            return method in self

        return any(m == method for m in self.values())
