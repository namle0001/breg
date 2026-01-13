from .context import ProcessorContext


class Processor:
    _context: ProcessorContext

    def __init__(self, context: ProcessorContext = None) -> None:
        self._context = context

    def set_context(self, context: ProcessorContext) -> None:
        self._context = context

    def get_context(self) -> ProcessorContext:
        return self._context
