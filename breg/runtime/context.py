from typing import Type
from breg.core.database import Database
from breg.core.network import Session as NetworkSession
from breg.core.filesystem import Filesystem
from breg.config.config import Configuration
from breg.config.env import Environment

from breg.processor.base import Processor as BaseProcessor
from breg.processor.context import ProcessorContext

from .registry import ProcessorRegistry, ProcessorType


class RuntimeContext:
    _project_fs: Filesystem
    _inst_fs: Filesystem
    _env: Environment
    _config: Configuration

    _processor_context: ProcessorContext
    _processor_registry: ProcessorRegistry

    def __init__(
        self,
        project_fs: Filesystem = None,
        inst_fs: Filesystem = None,
        config: Configuration = None,
        env: Environment = None,
    ):
        self._project_fs = project_fs or Filesystem()
        self._inst_fs = inst_fs or Filesystem()
        self._env = None
        self._config = None
        self._processor_registry = ProcessorRegistry()
        self._processor_context = ProcessorContext()

        self.initialize_settings(config or Configuration(), env or Environment())

    def initialize_settings(
        self, config: Configuration = None, env: Environment = None
    ):
        if config is not None:
            self._config = config
            self._processor_context.config = self._config
        if env is not None:
            self._env = env
            self._processor_context.env = self._env

    def initialize_cores(self, db: Database = None, net_session: NetworkSession = None):
        if db is not None:
            self._processor_context.database = db
        if net_session is not None:
            self._processor_context.session = net_session

    def initialize_processors(self, processors: list[ProcessorType] = None):
        if processors is not None:
            for processor in processors:
                self._processor_registry.register(processor(self._processor_context))

    def reload_processors(self, processors: list[ProcessorType] | ProcessorType = None):
        if processors is not None:
            for processor in processors:
                if self._processor_registry.contains(processor):
                    self._processor_registry.unregister(processor)
                self._processor_registry.register(processor(self._processor_context))
        else:
            old_processors = self._processor_registry.keys()
            self._processor_registry.clear()
            for processor in old_processors:
                self._processor_registry.register(processor(self._processor_context))

    def get_processor[T: BaseProcessor](self, typ: Type[T]) -> T:
        return self._processor_registry.get(typ)

    def project_fs(self) -> Filesystem:
        return self._project_fs

    def inst_fs(self) -> Filesystem:
        return self._inst_fs

    def env(self) -> Environment:
        return self._env

    def config(self) -> Configuration:
        return self._config

    def processor_context(self) -> ProcessorContext:
        return self._processor_context

    def processor_registry(self) -> ProcessorRegistry:
        return self._processor_registry
