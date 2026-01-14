"""Abstract base class for database operations."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from breg.type.data import (
    ClassCache,
    CourseCache,
    Enrollment,
)


def _append_docstring(docstring: str):
    def decorator(method):
        method.__doc__ = (method.__doc__ or "") + "\n" + docstring
        return method

    return decorator


class Database(ABC):
    """Abstract base class for database operations."""

    __complete_cache_docs__ = """
        A complete cache is a cache that contains all most up-to-date data
        available.
        
        This is achieved by propagating data from earlier caches
        that are not available in later caches.
    """

    @abstractmethod
    def get_course_caches(
        self,
        *,
        course_code: str | list[str] = None,
        course_name: str | list[str] = None,
        course_id: str | list[str] = None,
        after: datetime = None,
    ) -> list[CourseCache]:
        """Fetch course caches from the database.

        Args:
            course_code (str | list[str], optional): Course code(s) to filter by. Defaults to None.
            course_name (str | list[str], optional): Course name(s) to filter by. Defaults to None.
            course_id (str | list[str], optional): Course ID(s) to filter by. Defaults to None.
            after (datetime, optional): The datetime that the cache was created after. Defaults to None.

        Returns:
            list[CourseCache]: A list of course caches.
        """
        pass

    @abstractmethod
    def get_all_course_caches(
        self,
    ) -> list[CourseCache]:
        """Fetch all course caches from the database.

        Returns:
            list[CourseCache]: A list of all course caches.
        """
        pass

    @_append_docstring(__complete_cache_docs__)
    @abstractmethod
    def get_complete_course_cache(
        self,
        *,
        course_code: str = None,
        course_name: str = None,
        course_id: str = None,
        after: datetime = None,
    ) -> CourseCache | None:
        """Fetch a complete course cache from the database.

        Args:
            course_code (str, optional): The course code to filter by. Defaults to None.
            course_name (str, optional): The course name to filter by. Defaults to None.
            course_id (str, optional): The course ID to filter by. Defaults to None.
            after (datetime, optional): The datetime that the cache was created after. Defaults to None.

        Returns:
            CourseCache | None: A complete course cache or None if not found.
        """
        pass

    @abstractmethod
    def save_course_caches(self, course_caches: list[CourseCache] | CourseCache) -> int:
        """Save course caches to the database.
        This method will not guarantee that new caches are always saved.
        If a cache doesn't have any changes compared to existing caches, it may not be saved.

        Args:
            course_caches (list[CourseCache] | CourseCache): The course caches to save.

        Returns:
            int: The number of course caches saved.
        """
        pass

    @abstractmethod
    def remove_course_caches(self, cache_ids: list[int] | int) -> int:
        """Remove course caches from the database.
        Args:
            cache_ids (list[int] | int): The cache IDs to remove.

        Returns:
            int: The number of course caches removed.
        """
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
        """Fetch class caches from the database.

        Args:
            course_code (str | list[str], optional): The course code(s) to filter by. Defaults to None.
            class_code (str | list[str], optional): The class code(s) to filter by. Defaults to None.
            class_id (str | list[str], optional): The class ID(s) to filter by. Defaults to None.
            after (datetime, optional): The datetime that the cache was created after. Defaults to None.
            query_schedules (bool, optional): Whether to query schedules. Defaults to True.
        Returns:
            list[ClassCache]: A list of class caches.
        """
        pass

    @abstractmethod
    def get_all_class_caches(
        self,
        *,
        query_schedules: bool = True,
    ) -> list[ClassCache]:
        """Fetch all class caches from the database.

        Args:
            query_schedules (bool, optional): Whether to query schedules. Defaults to True.

        Returns:
            list[ClassCache]: A list of all class caches.
        """
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
        """Fetch a complete class cache from the database.

        Args:
            course_code (str, optional): The course code(s) to filter by. Defaults to None.
            class_code (str, optional): The class code(s) to filter by. Defaults to None.
            class_id (str, optional): The class ID(s) to filter by. Defaults to None.
            after (datetime, optional): The datetime that the cache was created after. Defaults to None.
            query_schedules (bool, optional): Whether to query schedules. Defaults to True.

        Returns:
            ClassCache | None: A complete class cache or None if not found.
        """
        pass

    @abstractmethod
    def save_class_caches(self, class_caches: list[ClassCache] | ClassCache) -> int:
        """Save class caches to the database.

        This method will not guarantee that new caches are always saved.
        If a cache doesn't have any changes compared to existing caches, it may not be saved.

        Args:
            class_caches (list[ClassCache] | ClassCache): The class caches to save.

        Returns:
            int: The number of class caches saved.
        """
        pass

    @abstractmethod
    def remove_class_caches(self, cache_ids: list[int] | int) -> int:
        """Remove class caches from the database.

        Args:
            cache_ids (list[int] | int): The cache IDs to remove.
        Returns:
            int: The number of class caches removed.
        """
        pass

    @abstractmethod
    def get_enrollments(self) -> list[Enrollment]:
        """Fetch all enrollments from the database.

        Returns:
            list[Enrollment]: A list of all enrollments.
        """
        pass

    @abstractmethod
    def append_enrollments(self, enrollments: list[Enrollment] | Enrollment) -> int:
        """Append enrollments to the database.

        Args:
            enrollments (list[Enrollment] | Enrollment): The enrollments to append.

        Returns:
            int: The number of enrollments appended.
        """
        pass

    @abstractmethod
    def remove_enrollments(self, enrollment_ids: list[int] | int) -> int:
        """Remove enrollments from the database.

        Args:
            enrollment_ids (list[int] | int): The enrollment IDs to remove.

        Returns:
            int: The number of enrollments removed.
        """
        pass

    @abstractmethod
    def clear_enrollments(self) -> int:
        """Clear all enrollments from the database.

        Returns:
            int: The number of enrollments removed.
        """
        pass

    @abstractmethod
    def execute_raw(self, query: str, parameters: tuple = ()) -> Any:
        """Execute a raw SQL query.

        Args:
            query (str): The SQL query to execute.
            parameters (tuple, optional): The parameters for the SQL query. Defaults to ().
        Returns:
            Any: The result of the SQL query execution.
        """
        pass
