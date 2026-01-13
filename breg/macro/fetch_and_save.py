from breg.runtime import ProcessorTypes
from breg.type.data import ClassCache, CourseCache, Enrollment

from .base import Macro


class FetchAndSaveMacro(Macro):
    def fetch_and_save_courses(self, search_str: str) -> list[CourseCache]:
        fetcher = self._runtime_context.get_processor(ProcessorTypes.FETCHER)
        database = self._runtime_context.processor_context().database

        courses = fetcher.fetch_course_data(search_str)
        database.save_course_caches(courses)

        return courses

    def fetch_and_save_classes(
        self, *, course_id: str = None, course_code: str = None
    ) -> list[ClassCache]:
        fetcher = self._runtime_context.get_processor(ProcessorTypes.FETCHER)
        database = self._runtime_context.processor_context().database
        if course_id is None:
            course = database.get_complete_course_cache(course_code=course_code)
            if not course or course.course_id is None:
                # attempt to fetch course first
                course = self.fetch_and_save_courses(search_str=course_code)
                if not course:
                    pass  # Raise error?

            course_id = course.course_id
            course_code = course.course_code
        if course_code is None:
            course = database.get_complete_course_cache(course_id=course_id)
            course_code = course.course_code

        classes = fetcher.fetch_class_data(course_id)
        for cache in classes:
            cache.course_code = course_code
        database.save_class_caches(classes)

        return classes

    def fetch_and_save_courses_and_classes(
        self, search_str: str
    ) -> tuple[list[CourseCache], list[ClassCache]]:
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
        fetcher = self._runtime_context.get_processor(ProcessorTypes.FETCHER)
        database = self._runtime_context.processor_context().database

        enrollments, courses, classes = fetcher.fetch_enrollment_data()
        database.save_course_caches(courses)
        database.save_class_caches(classes)

        if enrollments:
            database.clear_enrollments()
            database.append_enrollments(enrollments)

        return enrollments
