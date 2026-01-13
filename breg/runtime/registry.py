from typing import Type

from breg.processor.base import Processor
from breg.processor.exec import Executor as ExecProcessor
from breg.processor.fetch import Fetcher as FetchProcessor
from breg.processor.plan import SchedulePlanner as PlannerProcessor
from breg.processor.session import RoundMananger

ProcessorType = Type[Processor]


class ProcessorTypes:
    PLANNER = PlannerProcessor
    EXECUTOR = ExecProcessor
    FETCHER = FetchProcessor
    ROUND_MANAGER = RoundMananger


class ProcessorRegistry:
    _registry: dict[Type[Processor], "RegistryEntry[Processor]"] = {}

    def register[T: Processor](self, entry: T) -> None:
        newEntry = RegistryEntry(
            typ=type(entry),
            obj=entry,
        )
        self._registry[newEntry.typ] = newEntry

    def unregister[T: Processor](self, typ: Type[T]) -> None:
        if typ in self._registry:
            del self._registry[typ]

    def clear(self) -> None:
        self._registry.clear()

    def get[T: Processor](self, typ: type[T]) -> T:
        result = self._registry.get(typ, None)
        if result is None:
            raise KeyError(f"Registry entry '{typ}' not found.")
        return result.obj

    def contains[T: Processor](self, typ: Type[T]) -> bool:
        return typ in self._registry

    def keys(self) -> list[type[Processor]]:
        return list(self._registry.keys())

    def values(self) -> list[Processor]:
        return [entry.obj for entry in self._registry.values()]

    def items(self) -> list[tuple[type[Processor], Processor]]:
        return [(key, entry.obj) for key, entry in self._registry.items()]


class RegistryEntry[T: Processor]:
    typ: Type[T]
    obj: T

    def __init__(self, typ: Type[T], obj: T) -> None:
        self.typ = typ
        self.obj = obj
