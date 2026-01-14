"""Threaded execution macro for enrolling in classes concurrently."""

from dataclasses import dataclass
from enum import Enum
from threading import Thread
from typing import TypedDict

from breg.exception.network import NetworkException, NetworkSoftFailException
from breg.runtime import RuntimeContext
from breg.runtime.registry import ProcessorTypes
from breg.type.api_internal import ClassID

from .base import Macro


class ThreadedExecuteMacro(Macro):
    """Macro for executing class enrollments concurrently."""

    @dataclass
    class MinimalClassInfo:
        class_id: str
        class_code: str
        course_code: str

    class ClassIdInfo(TypedDict):
        class_id: str

    class ClassCodeWCourseIdInfo(TypedDict):
        class_code: str
        course_id: str

    class ClassCodeWCourseCodeInfo(TypedDict):
        class_code: str
        course_code: str

    class ExecutionState(Enum):
        PENDING = 1
        FETCHING = 2
        REGISTERING = 3
        COMPLETED = 4
        FAILED = 5
        RETRYING = 6

    class Runner:
        _state: "ThreadedExecuteMacro.ExecutionState"
        _fetch_enrollment_report: "ThreadedExecuteMacro.Runner.ReportState"
        _msg: str
        _context: RuntimeContext
        thread: Thread
        retries: int

        class ReportState(Enum):
            UNINITIALIZED = 1
            FETCHING = 2
            FAILED = 3
            SUCCEEDED = 4

            def success(self) -> bool:
                return self == ThreadedExecuteMacro.Runner.ReportState.SUCCEEDED

            def running(self) -> bool:
                return self == ThreadedExecuteMacro.Runner.ReportState.FETCHING

        def __init__(self, context: RuntimeContext):
            self._context = context
            self._state = ThreadedExecuteMacro.ExecutionState.PENDING
            self._fetch_enrollment_report = (
                ThreadedExecuteMacro.Runner.ReportState.UNINITIALIZED
            )
            self._msg = ""
            self.retries = 0
            self.thread = None

        def get_state(self) -> "ThreadedExecuteMacro.ExecutionState":
            return self._state

        def get_msg(self) -> str:
            return self._msg

        def run(
            self,
            class_info: "ThreadedExecuteMacro.ClassIdInfo | ThreadedExecuteMacro.ClassCodeWCourseIdInfo | ThreadedExecuteMacro.ClassCodeWCourseCodeInfo | ThreadedExecuteMacro.MinimalClassInfo",
            max_retries: int = 0,
        ):
            if self._fetch_enrollment_report.success():
                self._state = ThreadedExecuteMacro.ExecutionState.COMPLETED
                return
            try:
                if not isinstance(class_info, ThreadedExecuteMacro.MinimalClassInfo):
                    # Fetch class info stage
                    self._state = ThreadedExecuteMacro.ExecutionState.FETCHING
                    self._msg = "Fetching class info for "
                    if isinstance(class_info, ThreadedExecuteMacro.ClassIdInfo):
                        self._msg += "class_id=" + class_info["class_id"]
                    else:
                        self._msg += (
                            "class_code="
                            + class_info["class_code"]
                            + ", course_id="
                            + class_info.get("course_id")
                            + ", course_code="
                            + class_info.get("course_code")
                        )

                    if isinstance(class_info, ThreadedExecuteMacro.ClassIdInfo):
                        class_id = class_info["class_id"]
                        class_code, course_code = self._get_class_course_code(class_id)
                    else:
                        class_id = self._get_class_id(class_info)

                    class_code, course_code = self._get_class_course_code(class_id)
                    class_info = ThreadedExecuteMacro.MinimalClassInfo(
                        class_id=class_id,
                        class_code=class_code,
                        course_code=course_code,
                    )

                # Register stage
                self._state = ThreadedExecuteMacro.ExecutionState.REGISTERING
                self._msg = "Registering class_id=" + class_info.class_id
                self._context.get_processor(ProcessorTypes.EXECUTOR).enroll(
                    ClassID(class_info.class_id)
                )
                self._state = ThreadedExecuteMacro.ExecutionState.COMPLETED
            except NetworkSoftFailException as e:
                # verify enrollment
                if not self._fetch_enrollment_report.running():
                    Thread(
                        target=self._check_fetch_enrollment,
                        args=(
                            class_info.course_code,
                            class_info.class_code,
                        ),
                    ).start()

                self._state = ThreadedExecuteMacro.ExecutionState.FAILED
                self._msg = str(e)
                self._retry(class_info, max_retries)
            except NetworkException as e:
                self._state = ThreadedExecuteMacro.ExecutionState.FAILED
                self._msg = str(e)
                self._retry(class_info, max_retries)

        def _retry(self, class_info, max_retries: int) -> None:
            if max_retries == -1 or self.retries < max_retries:
                self.retries += 1
                self._state = ThreadedExecuteMacro.ExecutionState.RETRYING

                self.thread = Thread(target=self.run, args=(class_info, max_retries))
                self.thread.start()

        def _check_fetch_enrollment(self, course_code, class_code) -> None:
            self._fetch_enrollment_report = (
                ThreadedExecuteMacro.Runner.ReportState.FETCHING
            )
            fetch_processor = self._context.get_processor(ProcessorTypes.FETCHER)
            (enrollments, _, _) = fetch_processor.fetch_enrollment_data()

            for enrollment in enrollments:
                if (
                    enrollment.class_code == class_code
                    and enrollment.course_code == course_code
                ):
                    self._fetch_enrollment_report = (
                        ThreadedExecuteMacro.Runner.ReportState.SUCCEEDED
                    )
                    return
            self._fetch_enrollment_report = (
                ThreadedExecuteMacro.Runner.ReportState.FAILED
            )

        def _get_class_id(
            self,
            search: "ThreadedExecuteMacro.ClassCodeWCourseIdInfo | ThreadedExecuteMacro.ClassCodeWCourseCodeInfo",
        ) -> str:
            database = self._context.processor_context().database
            fetch_processor = self._context.get_processor(ProcessorTypes.FETCHER)

            # attemp to search from cache
            class_cache = database.get_complete_class_cache(
                class_code=search["class_code"],
                course_id=search.get("course_id"),
                course_code=search.get("course_code"),
                query_schedules=False,
            )
            if not class_cache or class_cache.id is None:
                # fetch for course_id if not provided
                if search.get("course_id") is None:
                    course = database.get_complete_course_cache(
                        course_code=search.get("course_code")
                    )

                    if not course or course.id is None:
                        fetched_courses = fetch_processor.fetch_course_data(
                            search.get("course_code")
                        )
                        database.save_course_caches(fetched_courses)

                        course = fetched_courses[0] if fetched_courses else None

                    if not course or course.id is None:
                        raise ValueError(
                            "course_id not found for the given course_code"
                        )

                    course_id = course.id

                # fetch class_id
                fetched_classes = fetch_processor.fetch_class_data(course_id)
                database.save_class_caches(fetched_classes)

                class_cache = fetched_classes[0] if fetched_classes else None

            if not class_cache or class_cache.id is None:
                raise ValueError("Class not found for the given class_code")

            return class_cache.id

        def _get_class_course_code(
            self,
            class_id: str,
        ) -> tuple[str, str]:
            database = self._context.processor_context().database
            cache = database.get_complete_class_cache(
                class_id=class_id, query_schedules=False
            )
            if not cache:
                raise ValueError("Class not found for the given class_id")

            return cache.class_code, cache.course_code

    class ThreadPoolManager:
        _threads: list["ThreadedExecuteMacro.Runner"]

        def __init__(self, runners: list["ThreadedExecuteMacro.Runner"]):
            self._threads = runners

        def all_completed(self) -> bool:
            return all(
                thread.get_state()
                in [
                    ThreadedExecuteMacro.ExecutionState.COMPLETED,
                    ThreadedExecuteMacro.ExecutionState.FAILED,
                ]
                for thread in self._threads
            )

        def join_all(self) -> None:
            for thread in self._threads:
                thread.thread.join()

        def get_threads(self) -> list["ThreadedExecuteMacro.Runner"]:
            return self._threads

    def enroll(
        self,
        class_infos: list[
            "ThreadedExecuteMacro.ClassIdInfo | ThreadedExecuteMacro.ClassCodeWCourseIdInfo | ThreadedExecuteMacro.ClassCodeWCourseCodeInfo"
        ],
        retries: int = 10,
        duplicates: int = 1,
    ) -> "ThreadedExecuteMacro.ThreadPoolManager":
        """Register multiple classes concurrently.

        Args:
            class_infos (list[ &quot;ThreadedExecuteMacro.ClassIdInfo | ThreadedExecuteMacro.ClassCodeWCourseIdInfo | ThreadedExecuteMacro.ClassCodeWCourseCodeInfo&quot; ]): _description_
            retries (int, optional): _description_. Defaults to 10.
            duplicates (int, optional): _description_. Defaults to 1.

        Returns:
            ThreadedExecuteMacro.ThreadPoolManager: _description_
        """
        threads: list[ThreadedExecuteMacro.Runner] = []

        for info in class_infos:
            for _ in range(duplicates):
                runner = ThreadedExecuteMacro.Runner(self._runtime_env)
                runner.thread = Thread(target=runner.run, args=(info, retries))
                threads.append(runner)
                runner.thread.start()

        return ThreadedExecuteMacro.ThreadPoolManager(threads)
