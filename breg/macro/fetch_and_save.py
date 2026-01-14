"""Module providing macros for fetching and saving course and class data."""

from breg.runtime import ProcessorTypes
from breg.type.data import ClassCache, CourseCache, Enrollment

from typing import TypedDict

from .base import Macro


class FetchAndSaveMacro(Macro):
    """Macro for fetching and saving course and class data."""

    def fetch_and_save_courses(self, search_str: str) -> list[CourseCache]:
        """Fetches course data based on a search string and saves it to the database.

        Args:
            search_str (str): Course to search for.

        Returns:
            list[CourseCache]: A list of fetched CourseCache objects.
        """
        fetcher = self._runtime_context.get_processor(ProcessorTypes.FETCHER)
        database = self._runtime_context.processor_context().database

        courses = fetcher.fetch_course_data(search_str)
        database.save_course_caches(courses)

        return courses

    class _CourseIdLookup(TypedDict):
        course_id: str

    class _CourseCodeLookup(TypedDict):
        course_code: str

    def fetch_and_save_classes(
        self, search: _CourseCodeLookup | _CourseIdLookup
    ) -> list[ClassCache]:
        """Fetches class data for a specific course and saves it to the database.

        Args:
            search (_CourseCodeLookup | _CourseIdLookup): Course identifier.
                Either course code or course ID.

        Returns:
            list[ClassCache]: A list of fetched ClassCache objects.
        """
        fetcher = self._runtime_context.get_processor(ProcessorTypes.FETCHER)
        database = self._runtime_context.processor_context().database

        course_id: str | None = None
        course_code: str | None = None
        if isinstance(search, self._CourseIdLookup):
            course_id = search["course_id"]
            course_code = database.get_complete_course_cache(
                course_id=course_id
            ).course_code
        else:
            course_code = search["course_code"]
            course = database.get_complete_course_cache(course_code=course_code)
            if not course or course.course_id is None:
                # attempt to fetch course first
                course = self.fetch_and_save_courses(search_str=course_code)
                if not course:
                    pass  # Raise error?

            course_id = course.course_id

        classes = fetcher.fetch_class_data(course_id)
        for cache in classes:
            cache.course_code = course_code
        database.save_class_caches(classes)

        return classes

    def fetch_and_save_courses_and_classes(
        self, search_str: str
    ) -> tuple[list[CourseCache], list[ClassCache]]:
        """Fetches course and class data based on a search string and saves them to the database.

        Args:
            search_str (str): Course to search for.

        Returns:
            tuple[list[CourseCache], list[ClassCache]]: A tuple containing lists of fetched CourseCache and ClassCache objects.
        """
        fetcher = self._runtime_context.get_processor(ProcessorTypes.FETCHER)
        database = self._runtime_context.processor_context().database

        courses = fetcher.fetch_course_data(search_str)
        database.save_course_caches(courses)

        all_classes: list[ClassCache] = []
        for course in courses:
            classes = fetcher.fetch_class_data(course.course_id)
            for cache in classes:
                cache.course_code = course.course_code
            database.save_class_caches(classes)
            all_classes.extend(classes)

        return courses, all_classes

    def fetch_and_save_enrollments(self) -> list[Enrollment]:
        """Fetches enrollment data and saves it to the database.

        Returns:
            list[Enrollment]: A list of fetched Enrollment objects.
        """
        fetcher = self._runtime_context.get_processor(ProcessorTypes.FETCHER)
        database = self._runtime_context.processor_context().database

        enrollments, courses, classes = fetcher.fetch_enrollment_data()
        database.save_course_caches(courses)
        database.save_class_caches(classes)

        if enrollments:
            database.clear_enrollments()
            database.append_enrollments(enrollments)

        return enrollments
