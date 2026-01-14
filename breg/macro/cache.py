"""Macro for accessing cached data related to courses and classes."""

from breg.type.data import ClassCache, CourseCache, Enrollment

from .base import Macro


def _append_docstring(docstring: str):
    def decorator(method):
        method.__doc__ = (method.__doc__ or "") + "\n" + docstring
        return method

    return decorator


class CacheMacro(Macro):
    """CacheMacro provides methods to access cached data related to courses and classes."""

    __complete_cache_docs__ = """
        A complete cache is a cache that contains all most up-to-date data
        available.
        
        This is achieved by propagating data from earlier caches
        that are not available in later caches.
    """

    def get_courses(
        self, *, course_code: str = None, course_id: str = None, course_name: str = None
    ) -> list[CourseCache]:
        """Retrieve a list of CourseCache objects based on the provided filters.

        Args:
            course_code (str, optional): filter by course code. Defaults to None.
            course_id (str, optional): filter by course ID. Defaults to None.
            course_name (str, optional): filter by course name. Defaults to None.

        Returns:
            list[CourseCache]: a list of CourseCache objects matching the filters if there are any.
        """
        database = self._runtime_context.processor_context().database
        return database.get_course_caches(
            course_code=course_code, course_id=course_id, course_name=course_name
        )

    def get_all_courses(self) -> list[CourseCache]:
        """Retrieve all CourseCache objects from the database.

        Returns:
            list[CourseCache]: a list of all CourseCache objects.
        """
        database = self._runtime_context.processor_context().database
        return database.get_all_course_caches()

    @_append_docstring(__complete_cache_docs__)
    def get_complete_course(
        self, *, course_code: str = None, course_id: str = None, course_name: str = None
    ) -> CourseCache | None:
        """Retrieve a complete CourseCache object based on the provided filters.

        Args:
            course_code (str, optional): filter by course code. Defaults to None.
            course_id (str, optional): filter by course ID. Defaults to None.
            course_name (str, optional): filter by course name. Defaults to None.

        Returns:
            CourseCache | None: a complete CourseCache object matching the filters if there is any.
        """
        database = self._runtime_context.processor_context().database
        return database.get_complete_course_cache(
            course_code=course_code, course_id=course_id, course_name=course_name
        )

    @_append_docstring(__complete_cache_docs__)
    def get_all_complete_courses(self) -> list[CourseCache]:
        """Retrieve all complete CourseCache objects from the database.

        Returns:
            list[CourseCache]: a list of all complete CourseCache objects.
        """
        database = self._runtime_context.processor_context().database
        courses = database.get_all_course_caches()

        complete_courses: dict[str, CourseCache] = {}
        for course in courses:
            for f in CourseCache.fields():
                complete_cache = complete_courses.setdefault(
                    course.course_code, CourseCache()
                )
                if not getattr(complete_cache, f):
                    value = getattr(course, f)
                    if value:
                        setattr(complete_cache, f, value)

        return list(complete_courses.values())

    def get_classes(
        self,
        *,
        class_code: str = None,
        class_id: str = None,
        course_id: str = None,
        course_code: str = None,
    ) -> list[ClassCache]:
        """Retrieve a list of ClassCache objects based on the provided filters.

        Args:
            class_code (str, optional): filter by class code. Defaults to None.
            class_id (str, optional): filter by class ID. Defaults to None.
            course_id (str, optional): filter by course ID. Defaults to None.
            course_code (str, optional): filter by course code. Defaults to None.

        Returns:
            list[ClassCache]: a list of ClassCache objects matching the filters.
        """
        database = self._runtime_context.processor_context().database
        return database.get_class_caches(
            class_code=class_code,
            class_id=class_id,
            course_id=course_id,
            course_code=course_code,
        )

    def get_all_classes(self, query_schedules: bool = True) -> list[ClassCache]:
        """Retrieve all ClassCache objects from the database.

        Args:
            query_schedules (bool, optional): whether to query schedules. Defaults to True.

        Returns:
            list[ClassCache]: a list of all ClassCache objects.
        """
        database = self._runtime_context.processor_context().database
        return database.get_all_class_caches(query_schedules=query_schedules)

    @_append_docstring(__complete_cache_docs__)
    def get_complete_class(
        self,
        *,
        class_code: str = None,
        class_id: str = None,
        course_code: str = None,
        query_schedules: bool = True,
    ) -> ClassCache | None:
        """Retrieve a complete ClassCache object based on the provided filters.

        Args:
            class_code (str, optional): filter by class code. Defaults to None.
            class_id (str, optional): filter by class ID. Defaults to None.
            course_code (str, optional): filter by course code. Defaults to None.
            query_schedules (bool, optional): whether to query schedules. Defaults to True.

        Returns:
            ClassCache | None: a complete ClassCache object matching the filters, or None if not found.
        """
        database = self._runtime_context.processor_context().database
        return database.get_complete_class_cache(
            class_code=class_code,
            class_id=class_id,
            course_code=course_code,
            query_schedules=query_schedules,
        )

    @_append_docstring(__complete_cache_docs__)
    def get_all_complete_classes(
        self, query_schedules: bool = True
    ) -> list[ClassCache]:
        """Retrieve all complete ClassCache objects from the database.

        Args:
            query_schedules (bool, optional): whether to query schedules. Defaults to True.

        Returns:
            list[ClassCache]: a list of all complete ClassCache objects.
        """
        database = self._runtime_context.processor_context().database
        classes = database.get_all_class_caches(query_schedules=query_schedules)

        complete_classes: dict[tuple[str, str], ClassCache] = {}
        for cls in classes:
            for f in ClassCache.fields():
                complete_cache = complete_classes.setdefault(
                    (cls.course_code, cls.class_code), ClassCache()
                )
                if not getattr(complete_cache, f):
                    value = getattr(cls, f)
                    if value:
                        setattr(complete_cache, f, value)

        return list(complete_classes.values())

    def get_enrollments(self) -> list[Enrollment]:
        """Retrieve all Enrollment objects from the database.

        Returns:
            list[Enrollment]: a list of all Enrollment objects.
        """
        database = self._runtime_context.processor_context().database
        return database.get_enrollments()

    def get_enrolled_classes(self) -> list[ClassCache]:
        """Retrieve all ClassCache objects for the classes the user is enrolled in.

        Returns:
            list[ClassCache]: a list of ClassCache objects for enrolled classes.
        """
        database = self._runtime_context.processor_context().database
        enrollments = database.get_enrollments()

        enrolled_classes: list[ClassCache] = []
        for enrollment in enrollments:
            cls = database.get_complete_class_cache(
                class_code=enrollment.class_code,
                course_code=enrollment.course_code,
                query_schedules=True,
            )
            if cls:
                enrolled_classes.append(cls)

        return enrolled_classes
