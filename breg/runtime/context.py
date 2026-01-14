"""Runtime context module"""

from breg.core.database import Database
from breg.core.network import Session as NetworkSession
from breg.core.filesystem import Filesystem
from breg.config.config import Configuration
from breg.config.env import Environment

from breg.processor.base import Processor as BaseProcessor
from breg.processor.context import ProcessorContext

from .registry import ProcessorRegistry, ProcessorType


class RuntimeContext:
    """The runtime context for the system"""

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
        """Initialize the runtime context.

        Args:
            project_fs (Filesystem, optional): The project filesystem. Defaults to None.
            inst_fs (Filesystem, optional): The installation filesystem. Defaults to None.
            config (Configuration, optional): The configuration settings. Defaults to None.
            env (Environment, optional): The environment settings. Defaults to None.
        """
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
        """Initialize the configuration and environment settings.

        Args:
            config (Configuration, optional): The configuration settings. Defaults to None.
            env (Environment, optional): The environment settings. Defaults to None.
        """
        if config is not None:
            self._config = config
            self._processor_context.config = self._config
        if env is not None:
            self._env = env
            self._processor_context.env = self._env

    def initialize_cores(self, db: Database = None, net_session: NetworkSession = None):
        """Initialize the core components

        Args:
            db (Database, optional): The database instance. Defaults to None.
            net_session (NetworkSession, optional): The network session instance. Defaults to None.
        """
        if db is not None:
            self._processor_context.database = db
        if net_session is not None:
            self._processor_context.session = net_session

    def initialize_processors(self, processors: list[ProcessorType] = None):
        """Initialize the processors.

        Args:
            processors (list[ProcessorType], optional): The list of processor types to initialize. Defaults to None.
        """
        if processors is not None:
            for processor in processors:
                self._processor_registry.register(processor(self._processor_context))

    def reload_processors(self, processors: list[ProcessorType] | ProcessorType = None):
        """Reload the processors.
        If the list of processors is provided, only those processors will be reloaded.
        Otherwise, all processors will be reloaded.

        Args:
            processors (list[ProcessorType] | ProcessorType, optional): The list of processor types to reload. Defaults to None.
        """
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

    def get_processor[T: BaseProcessor](self, typ: type[T]) -> T:
        """Get a processor by its type.

        Returns:
            T: The processor instance.
        """
        return self._processor_registry.get(typ)

    def project_fs(self) -> Filesystem:
        """Get the project filesystem.

        Returns:
            Filesystem: The project filesystem instance.
        """
        return self._project_fs

    def inst_fs(self) -> Filesystem:
        """Get the installation filesystem.

        Returns:
            Filesystem: The installation filesystem instance.
        """
        return self._inst_fs

    def env(self) -> Environment:
        """Get the environment settings.

        Returns:
            Environment: The environment settings instance.
        """
        return self._env

    def config(self) -> Configuration:
        """Get the configuration settings.

        Returns:
            Configuration: The configuration settings instance.
        """
        return self._config

    def processor_context(self) -> ProcessorContext:
        """Get the processor context.

        Returns:
            ProcessorContext: The processor context instance.
        """
        return self._processor_context

    def processor_registry(self) -> ProcessorRegistry:
        """Get the processor registry.

        Returns:
            ProcessorRegistry: The processor registry instance.
        """
        return self._processor_registry
