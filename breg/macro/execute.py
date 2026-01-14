""" ""Macro for executing enrollment actions."""

from breg.runtime import ProcessorTypes
from breg.type.api_internal import ClassID

from .base import Macro


class ExecuteMacro(Macro):
    """Macro for executing enrollment actions."""

    def enroll(
        self,
        *,
        class_id: str = None,
        class_code: str = None,
        course_id: str = None,
        course_code: str = None,
    ) -> None:
        """Enroll in a class given class_id or class_code with course_id or course_code.
        Either class_id or class_code with course_id or course_code must be provided.

        Args:
            class_id (str, optional): Class ID. Defaults to None.
            class_code (str, optional): Class code. Defaults to None.
            course_id (str, optional): Course ID. Defaults to None.
            course_code (str, optional): Course code. Defaults to None.
        """
        exec_processor = self._runtime_context.get_processor(ProcessorTypes.EXECUTOR)
        if class_id is None:
            class_id = self._get_class_id(
                class_code=class_code, course_id=course_id, course_code=course_code
            )
        exec_processor.enroll(ClassID(class_id))

    def unenroll(
        self,
        *,
        enrollment_id: str = None,
        course_code: str = None,
        class_code: str = None,
    ) -> None:
        """Unenroll from a class given enrollment_id or course_code and class_code.
        Either enrollment_id or both course_code and class_code must be provided.

        Args:
            enrollment_id (str, optional): enrollment ID. Defaults to None.
            course_code (str, optional): course code. Defaults to None.
            class_code (str, optional): class code. Defaults to None.

        Raises:
            ValueError: If neither enrollment_id nor both course_code and class_code are provided.
            ValueError: If enrollment is not found for the given course_code and class_code.

        Returns:
            None
        """
        database = self._runtime_context.processor_context().database
        fetch_processor = self._runtime_context.get_processor(ProcessorTypes.FETCHER)
        exec_processor = self._runtime_context.get_processor(ProcessorTypes.EXECUTOR)

        if enrollment_id is None:
            if course_code is None or class_code is None:
                raise ValueError(
                    "Either enrollment_id or both course_code and class_code must be provided"
                )

            enrollments = database.get_enrollments()

            def d(es):
                for enrollment in es:
                    if (
                        enrollment.course_code == course_code
                        and enrollment.class_code == class_code
                    ):
                        return enrollment

            enrollment = d(enrollments)
            if not enrollment:
                # attempt to fetch enrollment data
                enrollments = fetch_processor.fetch_enrollment_data()

            enrollment = d(enrollments)
            if not enrollment:
                raise ValueError(
                    "Enrollment not found for the given course_code and class_code"
                )

            enrollment_id = enrollment.id

        exec_processor.unenroll(enrollment_id)

    def _get_class_id(
        self,
        *,
        class_code: str = None,
        course_id: str = None,
        course_code: str = None,
    ) -> str:
        database = self._runtime_context.processor_context().database
        fetch_processor = self._runtime_context.get_processor(ProcessorTypes.FETCHER)
        if class_code is None:
            raise ValueError("Either class_id or class_code must be provided")

        if course_id is None and course_code is None:
            raise ValueError(
                "Either course_id or course_code must be provided when class_code is used"
            )

        # attemp to search from cache
        class_cache = database.get_complete_class_cache(
            class_code=class_code,
            course_id=course_id,
            course_code=course_code,
            query_schedules=False,
        )
        if not class_cache or class_cache.id is None:
            # fetch for course_id if not provided
            if course_id is None:
                course = database.get_complete_course_cache(course_code=course_code)

                if not course or course.id is None:
                    fetched_courses = fetch_processor.fetch_course_data(course_code)
                    database.save_course_caches(fetched_courses)

                    course = fetched_courses[0] if fetched_courses else None

                if not course or course.id is None:
                    raise ValueError("course_id not found for the given course_code")

                course_id = course.id

            # fetch class_id
            fetched_classes = fetch_processor.fetch_class_data(course_id)
            database.save_class_caches(fetched_classes)

            class_cache = fetched_classes[0] if fetched_classes else None

        if not class_cache or class_cache.id is None:
            raise ValueError("Class not found for the given class_code")

        return class_cache.id
