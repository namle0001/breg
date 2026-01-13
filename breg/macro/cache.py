from breg.type.data import ClassCache, CourseCache, Enrollment

from .base import Macro


class CacheMacro(Macro):
    def get_courses(
        self, *, course_code: str = None, course_id: str = None, course_name: str = None
    ) -> list[CourseCache]:
        database = self._runtime_context.processor_context().database
        return database.get_course_caches(
            course_code=course_code, course_id=course_id, course_name=course_name
        )

    def get_all_courses(self) -> list[CourseCache]:
        database = self._runtime_context.processor_context().database
        return database.get_all_course_caches()

    def get_complete_course(
        self, *, course_code: str = None, course_id: str = None, course_name: str = None
    ) -> CourseCache | None:
        database = self._runtime_context.processor_context().database
        return database.get_complete_course_cache(
            course_code=course_code, course_id=course_id, course_name=course_name
        )

    def get_all_complete_courses(self) -> list[CourseCache]:
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
        database = self._runtime_context.processor_context().database
        return database.get_class_caches(
            class_code=class_code,
            class_id=class_id,
            course_id=course_id,
            course_code=course_code,
        )

    def get_all_classes(self, query_schedules: bool = True) -> list[ClassCache]:
        database = self._runtime_context.processor_context().database
        return database.get_all_class_caches(query_schedules=query_schedules)

    def get_complete_class(
        self,
        *,
        class_code: str = None,
        class_id: str = None,
        course_code: str = None,
        query_schedules: bool = True,
    ) -> ClassCache | None:
        database = self._runtime_context.processor_context().database
        return database.get_complete_class_cache(
            class_code=class_code,
            class_id=class_id,
            course_code=course_code,
            query_schedules=query_schedules,
        )

    def get_all_complete_classes(
        self, query_schedules: bool = True
    ) -> list[ClassCache]:
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
        database = self._runtime_context.processor_context().database
        return database.get_enrollments()

    def get_enrolled_classes(self) -> list[ClassCache]:
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
