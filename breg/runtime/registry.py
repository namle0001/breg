""" "Registry for processor instances."""

from typing import Type

from breg.processor.base import Processor
from breg.processor.exec import Executor as ExecProcessor
from breg.processor.fetch import Fetcher as FetchProcessor
from breg.processor.plan import SchedulePlanner as PlannerProcessor
from breg.processor.session import RoundMananger

ProcessorType = Type[Processor]


class ProcessorTypes:
    """Enumeration of processor types."""

    PLANNER = PlannerProcessor
    EXECUTOR = ExecProcessor
    FETCHER = FetchProcessor
    ROUND_MANAGER = RoundMananger


class ProcessorRegistry:
    """Registry for processor instances."""

    _registry: dict[Type[Processor], "RegistryEntry[Processor]"] = {}

    def register[T: Processor](self, entry: T) -> None:
        """Register a processor instance in the registry.

        Args:
            entry (T): The processor instance to register.
        """
        newEntry = RegistryEntry(
            typ=type(entry),
            obj=entry,
        )
        self._registry[newEntry.typ] = newEntry

    def unregister[T: Processor](self, typ: Type[T]) -> None:
        """Unregister a processor instance from the registry.

        Args:
            typ (Type[T]): The type of the processor to unregister.
        """
        if typ in self._registry:
            del self._registry[typ]

    def clear(self) -> None:
        """Clear all entries from the registry."""
        self._registry.clear()

    def get[T: Processor](self, typ: type[T]) -> T:
        """Get a processor instance from the registry by its type.

        Raises:
            KeyError: If the processor type is not found in the registry.

        Returns:
            T: The processor instance.
        """
        result = self._registry.get(typ, None)
        if result is None:
            raise KeyError(f"Registry entry '{typ}' not found.")
        return result.obj

    def contains[T: Processor](self, typ: Type[T]) -> bool:
        """Check if a processor type is registered in the registry.

        Args:
            typ (Type[T]): The type of the processor to check.

        Returns:
            bool: True if the processor type is registered, False otherwise.
        """
        return typ in self._registry

    def keys(self) -> list[type[Processor]]:
        """Get a list of all registered processor types.

        Returns:
            list[type[Processor]]: A list of all registered processor types.
        """
        return list(self._registry.keys())

    def values(self) -> list[Processor]:
        """Get a list of all registered processor instances.

        Returns:
            list[Processor]: A list of all registered processor instances.
        """
        return [entry.obj for entry in self._registry.values()]

    def items(self) -> list[tuple[type[Processor], Processor]]:
        """Get a list of all registered processor types and their instances.

        Returns:
            list[tuple[type[Processor], Processor]]: A list of all registered processor types and their instances.
        """
        return [(key, entry.obj) for key, entry in self._registry.items()]


class RegistryEntry[T: Processor]:
    """Represents an entry in the processor registry."""

    typ: Type[T]
    obj: T

    def __init__(self, typ: Type[T], obj: T) -> None:
        self.typ = typ
        self.obj = obj
