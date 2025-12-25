import IPython
from typing import Callable

from breg.core.network.net import Session as NetworkSession
from breg.config.config import Configuration
from breg.config.env import Environment
from breg.processor.session import Authenticator as AuthProcessor, RoundMananger
from breg.processor.exec import Executor as ExecProcessor
from breg.processor.fetch import Fetcher as FetchProcessor


class InteractiveConsoleSession:
    _network_session: NetworkSession = None
    _config: Configuration = None
    _env: Environment = None

    _namespace: "Namespace" = None

    _exec_processor: ExecProcessor = None
    _fetch_processor: FetchProcessor = None
    _round_manager: RoundMananger = None

    def __init__(self, config: Configuration, env: Environment):
        self._config = config
        self._env = env

    def initialize_namespace(self) -> None:
        self._namespace = Namespace()

        self._namespace.bind_namespace(
            InteractiveConsoleSession,
            object_instance=self,
            only_callable=False,
            ignore_protected=False,
        )

    def start_session(self):
        IPython.start_ipython(user_ns=self._namespace)

    def fetcher(self) -> FetchProcessor:
        return self._fetch_processor

    def authenticate_and_reload(self) -> None:
        self.authenticate()
        self.reload()

    def authenticate(self) -> NetworkSession | None:
        old_session = self._network_session
        self._network_session = AuthProcessor(self._config, self._env).authenticate()
        return old_session

    def reload(self) -> None:
        self._exec_processor = ExecProcessor(
            self._network_session,
            self._config,
        )
        self._fetch_processor = FetchProcessor(
            self._network_session,
            self._config,
        )
        self._round_manager = RoundMananger(
            self._network_session,
            self._config,
        )

    def setconf(self, key: str, value: str) -> None:
        if not hasattr(self._config, key):
            raise AttributeError(f"Configuration has no attribute '{key}'")
        setattr(self._config, key, value)

    def getconf(self, key: str) -> str:
        if not hasattr(self._config, key):
            raise AttributeError(f"Configuration has no attribute '{key}'")
        return getattr(self._config, key)

    def setenv(self, key: str, value: str) -> None:
        if not hasattr(self._env, key):
            raise AttributeError(f"Environment has no attribute '{key}'")
        setattr(self._env, key, value)

    def getenv(self, key: str) -> str:
        if not hasattr(self._env, key):
            raise AttributeError(f"Environment has no attribute '{key}'")
        return getattr(self._env, key)


class Namespace(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def bind_namespace(
        self,
        namespace: object,
        object_instance: object | None = None,
        only_callable: bool = False,
        ignore_protected: bool = True,
        ignore_private: bool = True,
        ignore_dunder: bool = True,
    ) -> None:
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
