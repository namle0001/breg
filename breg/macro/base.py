from breg.runtime import RuntimeContext


class Macro:
    _runtime_context: RuntimeContext

    def __init__(self, context: RuntimeContext = None):
        self._runtime_context = context

    def set_context(self, context: RuntimeContext) -> None:
        self._runtime_context = context

    def get_context(self) -> RuntimeContext:
        return self._runtime_context
