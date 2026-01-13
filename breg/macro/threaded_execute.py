from dataclasses import dataclass
from threading import Thread

from enum import Enum

from breg.exception.network import NetworkSoftFailException
from breg.runtime import RuntimeContext
from breg.runtime.registry import ProcessorTypes
from breg.type.api_internal import ClassID

from .base import Macro


class ThreadedExecuteMacro(Macro):
    @dataclass
    class ClassLookupInfo:
        class_id: str
        class_code: str
        course_id: str
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
        _msg: str
        _context: RuntimeContext
        thread: Thread = None
        retries: int = 0

        def __init__(self, context: RuntimeContext):
            self._context = context
            self._state = ThreadedExecuteMacro.ExecutionState.PENDING
            self._msg = ""

        def get_state(self) -> "ThreadedExecuteMacro.ExecutionState":
            return self._state

        def get_msg(self) -> str:
            return self._msg

        def run(
            self,
            class_info: "ThreadedExecuteMacro.ClassLookupInfo",
            retries: int = 0,
        ):
            try:
                self._state = ThreadedExecuteMacro.ExecutionState.FETCHING
                self._msg = "Fetching class info for "
                if class_info.class_id is not None:
                    self._msg += "class_id=" + class_info.class_id
                else:
                    self._msg += (
                        "class_code="
                        + class_info.class_code
                        + ", course_id="
                        + class_info.course_id
                        + ", course_code="
                        + class_info.course_code
                    )
                class_id = class_info.class_id
                if class_id is None:
                    class_id = ThreadedExecuteMacro._get_class_id(
                        self,
                        class_code=class_info.class_code,
                        course_id=class_info.course_id,
                        course_code=class_info.course_code,
                    )
                self._state = ThreadedExecuteMacro.ExecutionState.REGISTERING
                self._msg = "Registering class_id=" + class_id
                self._context.get_processor(ProcessorTypes.EXECUTOR).enroll(
                    ClassID(class_id)
                )
                self._state = ThreadedExecuteMacro.ExecutionState.COMPLETED
            except NetworkSoftFailException as e:
                (enrollments, _, _) = self._context.get_processor(
                    ProcessorTypes.FETCHER
                ).fetch_enrollment_data()
                class_code = class_info.class_code or None
                course_code = class_info.course_code or None

                if not class_code or not course_code:
                    class_code, course_code = self._get_class_course_code(
                        class_id=class_info.class_id,
                    )

                if not class_code or not course_code:
                    raise Exception(
                        "Class code or course code not found for the given class_id. "
                        "Failed to determine enrollment to verify registration failure."
                    )

                for enrollment in enrollments:
                    if (
                        enrollment.class_code == class_code
                        and enrollment.course_code == course_code
                    ):
                        break
                else:
                    self._state = ThreadedExecuteMacro.ExecutionState.FAILED
                    self._msg = str(e)
                    if self.retries < retries:
                        self.retries += 1
                        self._state = ThreadedExecuteMacro.ExecutionState.RETRYING
                        self.run(class_info, retries=retries)
                    return
            except Exception as e:
                self._state = ThreadedExecuteMacro.ExecutionState.FAILED
                self._msg = str(e)
                if self.retries < retries:
                    self.retries += 1
                    self._state = ThreadedExecuteMacro.ExecutionState.RETRYING
                    self.run(class_info, retries=retries)

        def _get_class_id(
            self,
            *,
            class_code: str = None,
            course_id: str = None,
            course_code: str = None,
        ) -> str:
            database = self._context.processor_context().database
            fetch_processor = self._context.get_processor(ProcessorTypes.FETCHER)
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
            *,
            class_id: str = None,
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

    def enroll_batch(
        self,
        class_infos: list["ThreadedExecuteMacro.ClassLookupInfo"],
        duplicates: int = 1,
    ) -> "ThreadedExecuteMacro.ThreadPoolManager":
        threads: list[ThreadedExecuteMacro.Runner] = []

        for info in class_infos:
            for _ in range(duplicates):
                runner = ThreadedExecuteMacro.Runner(self._runtime_env)
                runner.thread = Thread(
                    target=runner.run,
                    args=(info,),
                )
                threads.append(runner)
                runner.thread.start()

        return ThreadedExecuteMacro.ThreadPoolManager(threads)
