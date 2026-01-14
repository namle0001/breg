"""Base class for all macros."""

from breg.runtime import RuntimeContext


class Macro:
    """Base class for all macros."""

    _runtime_context: RuntimeContext

    def __init__(self, context: RuntimeContext = None):
        """Initialize the Macro.

        Args:
            context (RuntimeContext, optional): The runtime context for the macro. Defaults to None.
        """
        self._runtime_context = context

    def set_context(self, context: RuntimeContext) -> None:
        """Set the runtime context for the macro.

        Args:
            context (RuntimeContext): The runtime context to set for the macro.
        """
        self._runtime_context = context

    def get_context(self) -> RuntimeContext:
        """Get the runtime context for the macro.

        Returns:
            RuntimeContext: The runtime context for the macro.
        """
        return self._runtime_context
