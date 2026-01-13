from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from breg.type.data import (
    ClassCache,
    CourseCache,
    Enrollment,
)


class Database(ABC):
    @abstractmethod
    def get_course_caches(
        self,
        *,
        course_code: str | list[str] = None,
        course_name: str | list[str] = None,
        course_id: str | list[str] = None,
        after: datetime = None,
    ) -> list[CourseCache]:
        pass

    @abstractmethod
    def get_all_course_caches(
        self,
    ) -> list[CourseCache]:
        pass

    @abstractmethod
    def get_complete_course_cache(
        self,
        *,
        course_code: str = None,
        course_name: str = None,
        course_id: str = None,
        after: datetime = None,
    ) -> CourseCache | None:
        pass

    @abstractmethod
    def save_course_caches(self, course_caches: list[CourseCache] | CourseCache) -> int:
        pass

    @abstractmethod
    def remove_course_caches(self, course_ids: list[int] | int) -> int:
        pass

    @abstractmethod
    def get_class_caches(
        self,
        *,
        course_code: str | list[str] = None,
        class_code: str | list[str] = None,
        class_id: str | list[str] = None,
        after: datetime = None,
        query_schedules: bool = True,
    ) -> list[ClassCache]:
        pass

    @abstractmethod
    def get_all_class_caches(
        self,
        *,
        query_schedules: bool = True,
    ) -> list[ClassCache]:
        pass

    @abstractmethod
    def get_complete_class_cache(
        self,
        *,
        course_code: str = None,
        class_code: str = None,
        class_id: str = None,
        after: datetime = None,
        query_schedules: bool = True,
    ) -> ClassCache | None:
        pass

    @abstractmethod
    def save_class_caches(self, class_caches: list[ClassCache] | ClassCache) -> int:
        pass

    @abstractmethod
    def remove_class_caches(self, class_ids: list[int] | int) -> int:
        pass

    @abstractmethod
    def get_enrollments(self) -> list[Enrollment]:
        pass

    @abstractmethod
    def append_enrollments(self, enrollments: list[Enrollment] | Enrollment) -> int:
        pass

    @abstractmethod
    def remove_enrollments(self, enrollment_ids: list[int] | int) -> int:
        pass

    @abstractmethod
    def clear_enrollments(self) -> int:
        pass

    @abstractmethod
    def execute_raw(self, query: str, parameters: tuple = ()) -> Any:
        pass
