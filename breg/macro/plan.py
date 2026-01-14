"""Macro for planning class schedules using the SchedulePlanner."""

from enum import Enum
from heapq import heappop
from json import JSONDecoder, JSONEncoder
from threading import Event, Lock, Thread

from breg.processor.plan import Preferences, SchedulePlanner
from breg.processor.plan.planner import (
    Class,
    MaxHeapSolution,
    Solution,
)
from breg.processor.plan.planner import (
    State as PlannerState,
)
from breg.runtime import RuntimeContext
from breg.runtime.registry import ProcessorTypes
from breg.type import ClassCache

from .base import Macro


def _lock_method(lock_attr: str, blocking: bool = True):
    def decorator[T](method: T) -> T:
        def wrapper(self, *args, **kwargs):
            lock: Lock = getattr(self, lock_attr)
            if not lock.acquire(blocking=blocking):
                raise RuntimeError("Could not acquire lock for method execution.")
            try:
                return method(self, *args, **kwargs)
            finally:
                lock.release()

        return wrapper

    return decorator


class PlanMacro(Macro):
    """Macro for planning class schedules using the SchedulePlanner."""

    _lock: Lock
    _runner: "Runner"

    def __init__(self, context: RuntimeContext):
        super().__init__(context)
        self._lock = Lock()
        self._runner = None

    @_lock_method("_lock", False)
    def setup(self, class_caches: list[ClassCache], solution_count: int = 100) -> None:
        """Setup the planner with class caches and initialize solutions.

        Args:
            class_caches (list[ClassCache]): List of class caches to be used by the planner.
            solution_count (int, optional): Number of solutions wanted. Defaults to 100.
        """
        planner = self._runtime_context.get_processor(ProcessorTypes.PLANNER)
        planner.prepare_classes(class_caches)
        planner.initialize(solution_count)

    @_lock_method("_lock", False)
    def run(self, detached: bool = True) -> None:
        """Run the planner either in detached mode or blocking mode.

        Args:
            detached (bool, optional): Whether to run the planner in detached mode. Defaults to True.
        """
        planner = self._runtime_context.get_processor(ProcessorTypes.PLANNER)
        if not detached:
            while planner.step():
                pass
        else:
            print("Running planner in detached mode...")
            self._runner = self.Runner(
                planner=planner,
                lock=self._lock,
            )

    def detached_runner(self) -> "Runner | None":
        """Get the detached runner if it is running.

        Returns:
            Runner | None: The detached runner instance or None if not running.
        """
        return self._runner

    def stop_detached(self) -> None:
        """Stop the detached planner if it is running."""
        if self._runner is not None:
            self._runner.stop()
            self._runner = None

    def is_finished(self) -> bool:
        """Check if the planner has finished running.

        Returns:
            bool: True if the planner is finished, False otherwise.
        """
        return self._runtime_context.get_processor(ProcessorTypes.PLANNER).is_finished()

    def is_running(self) -> bool:
        """Check if the planner is currently running.

        Returns:
            bool: True if the planner is running, False otherwise.
        """
        runner = self.detached_runner()
        if runner is None:
            return False
        return runner._state == self.Runner.State.RUNNING

    def _sort_em_up(self, unsorted: list[Solution]) -> list[Solution]:
        solutions: list[MaxHeapSolution] = []
        for s in unsorted:
            if isinstance(s, MaxHeapSolution):
                solutions.append(s)
            else:
                solutions.append(MaxHeapSolution.fromSol(s))

        # Sort solutions in ascending order based on their cost
        sorted = []
        while solutions:
            sorted.append(heappop(solutions))
        sorted.reverse()  # Reverse to get ascending order
        return sorted

    @_lock_method("_lock", False)
    def get_raw_solutions(self) -> list[list[Class]]:
        """Get the planned class caches after running the planner.

        Returns:
            list[list[Class]]: A list of solutions, each containing a list of Class objects.
        """
        informated_sols: list[list[Class]] = []
        state = self._runtime_context.get_processor(ProcessorTypes.PLANNER).get_state()
        solutions = self._sort_em_up(state.optimal_solutions.copy())

        for solution in solutions:
            informated_sol: list[Class] = []

            for course_index, class_index in enumerate(solution.classes):
                informated_sol.append(state.classes[course_index][class_index])

            informated_sols.append(informated_sol)

        return informated_sols

    @_lock_method("_lock", False)
    def get_solutions(self) -> list[list[ClassCache]]:
        """Get the planned class caches after running the planner.

        Returns:
            list[list[ClassCache]]: A list of solutions, each containing a list of ClassCache objects.
        """
        informated_sols: list[list[ClassCache]] = []
        state = self._runtime_context.get_processor(ProcessorTypes.PLANNER).get_state()
        solutions = self._sort_em_up(state.optimal_solutions.copy())

        for solution in solutions:
            informated_sol: list[ClassCache] = []

            for course_index, class_index in enumerate(solution.classes):
                cls = state.classes[course_index][class_index]
                cache = ClassCache(
                    class_code=cls.class_code,
                    course_code=cls.course_code,
                    schedules=cls.schedules,
                )
                informated_sol.append(cache)

            informated_sols.append(informated_sol)

        return informated_sols

    class Runner:
        class State(Enum):
            PENDING = 0
            RUNNING = 1
            STOPPED = 2

        _thread: Thread
        _stop_event: Event
        _state: State

        def __init__(self, planner: SchedulePlanner, lock: Lock):
            self._stop_event = Event()
            self._state = self.State.PENDING
            self._thread = Thread(target=self.run, args=(planner, lock), daemon=True)
            self._thread.start()

        def stop(self):
            self._stop_event.set()

        def run(self, planner: SchedulePlanner, lock: Lock):
            with lock:
                self._state = self.State.RUNNING
                while True:
                    if self._stop_event.is_set():
                        break
                    if not planner.step():
                        break
                self._state = self.State.STOPPED

    ### Preferences and Planner State Management ###

    @_lock_method("_lock", False)
    def load_preferences(self, preferences: Preferences | str) -> None:
        """Load preferences from a JSON string or Preferences object.

        Args:
            preferences (Preferences | str): The preferences object or JSON string to be loaded.
        """
        if isinstance(preferences, str):
            preferences = Preferences.from_dict(
                JSONDecoder().decode(preferences),
            )
        planner = self._runtime_context.get_processor(ProcessorTypes.PLANNER)
        planner.set_preferences(preferences)

    def load_preferences_from_file(self, filepath: str) -> None:
        """Load preferences from a file.

        Args:
            filepath (str): The file path to load the preferences from.
        """
        with self._runtime_context.project_fs().open(
            filepath, mode="r", encoding="utf-8"
        ) as f:
            self.load_preferences(f.read())

    def save_preferences(self) -> str:
        """Save preferences to a JSON string.

        Returns:
            str: The preferences as a JSON string.
        """
        planner = self._runtime_context.get_processor(ProcessorTypes.PLANNER)
        return JSONEncoder().encode(planner.get_preferences().dict())

    def save_preferences_to_file(self, filepath: str) -> None:
        """Save preferences to a file.

        Args:
            filepath (str): The file path to save the preferences.
        """
        prefs_str = self.save_preferences()
        with self._runtime_context.project_fs().open(
            filepath, mode="w", encoding="utf-8"
        ) as f:
            f.write(prefs_str)

    @_lock_method("_lock", False)
    def load_state(self, state: PlannerState | str) -> None:
        """Load planner state from a JSON string or PlannerState object.

        Args:
            state (PlannerState | str): The planner state object or JSON string to be loaded.
        """
        if isinstance(state, str):
            state = PlannerState.from_dict(
                JSONDecoder().decode(state),
            )
        self._runtime_context.get_processor(ProcessorTypes.PLANNER).set_state(state)

    def load_state_from_file(self, filepath: str) -> None:
        """Load planner state from a file.

        Args:
            filepath (str): The file path to load the planner state from.
        """
        with self._runtime_context.project_fs().open(
            filepath, mode="r", encoding="utf-8"
        ) as f:
            self.load_state(f.read())

    def reset_state(self) -> None:
        """Reset the planner state to its initial state."""
        planner = self._runtime_context.get_processor(ProcessorTypes.PLANNER)
        planner.new_state()

    @_lock_method("_lock", False)
    def save_state(self) -> str:
        """Save planner state to a JSON string.

        Returns:
            str: The planner state as a JSON string.
        """
        planner = self._runtime_context.get_processor(ProcessorTypes.PLANNER)
        return JSONEncoder().encode(planner.get_state().dict())

    def save_state_to_file(self, filepath: str) -> None:
        """Save planner state to a file.

        Args:
            filepath (str): The file path to save the planner state.
        """
        with self._runtime_context.project_fs().open(
            filepath, mode="w", encoding="utf-8"
        ) as f:
            f.write(self.save_state())

    def save_pref(self, preferences: Preferences, filepath: str = None) -> None | str:
        """Save preferences to a file or return as a JSON string.

        Args:
            preferences (Preferences): The preferences object to be saved.
            filepath (str, optional): The file path to save the preferences. Defaults to None.

        Returns:
            None | str: Returns None if saved to a file, or a JSON string if no file path is provided.
        """
        prefs_dict = preferences.dict()
        prefs_str = JSONEncoder().encode(prefs_dict)
        if filepath is None:
            return prefs_str
        with self._runtime_context.project_fs().open(
            filepath, mode="w", encoding="utf-8"
        ) as f:
            f.write(prefs_str)

    def load_pref(
        self, filepath: str | None = None, data: str | None = None
    ) -> Preferences:
        """Load preferences from a file or JSON string.

        Args:
            filepath (str | None, optional): The file path to load the preferences from. Defaults to None.
            data (str | None, optional): The JSON string to load the preferences from. Defaults to None.

        Raises:
            ValueError: If neither filepath nor data is provided.

        Returns:
            Preferences: The loaded preferences object.
        """
        if data is None and filepath is not None:
            with self._runtime_context.project_fs().open(
                filepath, mode="r", encoding="utf-8"
            ) as f:
                data = f.read()
        if data is None:
            raise ValueError("Either filepath or data must be provided.")
        prefs_dict = JSONDecoder().decode(data)
        return Preferences.from_dict(prefs_dict)

    @classmethod
    def init_base_preferences(cls, course_codes: list[str] = None) -> Preferences:
        """Initialize base preferences, optionally for specific course codes local preferences.

        Args:
            course_codes (list[str], optional): List of course codes to initialize local timetable preferences for. Defaults to None.

        Returns:
            Preferences: The initialized preferences object.
        """
        prefs = Preferences()
        if course_codes is not None:
            prefs.initialize_local_timetable_prefs(course_codes)
        return prefs
