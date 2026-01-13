from heapq import heappop, heappush
from dataclasses import dataclass, field
from collections import deque

from breg.type import ClassCache
from breg.type.data import Schedule
from .preferences import (
    GapPenalty,
    Preferences,
    TimeTablePreferences,
    NeutralGapPenalty,
)

from ..base import Processor


class SchedulePlanner(Processor):
    _preferences: Preferences
    _state: "State"

    def __init__(self, context) -> None:
        super().__init__(context=context)
        self._preferences = None
        self._state = State()

    def solution_count(self, count: int) -> None:
        self._state.requested_solution_count = count

    @classmethod
    def _calculate_cost(
        cls, schedules: list[Schedule], prefs: TimeTablePreferences
    ) -> int:
        total_cost = 0
        for schedule in schedules:
            for period in range(16):
                cost = prefs.get_timeframe(period)
                if cost is not None and (schedule.timeframe.get(period + 1)):
                    total_cost += cost

            for day in range(7):
                cost = prefs.get_day(day)
                if cost is not None and (schedule.day.get(day + 1)):
                    total_cost += cost

            for week in range(2):
                cost = prefs.get_week(week)
                if cost is not None and (schedule.week.get(week + 1)):
                    total_cost += cost
        return total_cost

    def prepare_classes(self, class_caches: list[ClassCache]):
        # Populate classes from caches
        for cache in class_caches:
            cl = Class(
                course_code=cache.course_code,
                class_code=cache.class_code,
                schedules=cache.schedules.copy(),
            )
            if not next(
                (x for x in self._state.course_codes if x == cache.course_code), None
            ):
                self._state.course_codes.append(cache.course_code)
                self._state.classes.append([])
            index = self._state.course_codes.index(cache.course_code)
            self._state.classes[index].append(cl)

        # Calculate costs for each class
        for classes in self._state.classes:
            for cl in classes:
                cl.global_cost = self._calculate_cost(
                    cl.schedules, self._preferences.get_global_timetable_prefs()
                )
                cl.local_cost = self._calculate_cost(
                    cl.schedules,
                    self._preferences.get_local_timetable_prefs(cl.course_code),
                )

        # Sort classes by total cost
        for classes in self._state.classes:
            classes.sort(key=lambda c: c.total_cost())

    def initialize(self, solution_count: int) -> None:
        self._state.requested_solution_count = solution_count
        self._state.next_class = [0] * len(self._state.classes)
        self._state.preferences = NamelessPreferences(
            global_timetable_prefs=self._preferences.get_global_timetable_prefs(),
            local_timetable_prefs=[
                self._preferences.get_local_timetable_prefs(code)
                for code in self._state.course_codes
            ],
            gap_penalty=[
                self._preferences._gap_penalty.get(gap_size, NeutralGapPenalty())
                for gap_size in range(1, 16)
            ],
        )

    # return (gap size, gap count)
    @classmethod
    def _check_collision_and_count_gap(
        cls, schedules: list[Schedule]
    ) -> tuple[bool, dict[int, int]] | tuple[bool, int]:
        gap_map: dict[int, int] = {}
        for i in range(len(schedules) - 1):
            for j in range(i + 1, len(schedules)):
                # Compare day, then week
                if not schedules[i].day & schedules[j].day:
                    continue
                if not schedules[i].week & schedules[j].week:
                    continue

                if schedules[i].timeframe & schedules[j].timeframe:
                    return False, j  # Collision detected

                combined_timeframe = schedules[i].timeframe | schedules[j].timeframe
                gap_size = 0
                in_gap = False
                start_counting = False
                for period in range(16):
                    if (combined_timeframe >> (period)) & 1:
                        start_counting = True
                        if in_gap:
                            gap_map.setdefault(gap_size, 0)
                            gap_map[gap_size] += 1
                            gap_size = 0
                            in_gap = False

                    else:
                        if not start_counting:
                            continue
                        in_gap = True
                        gap_size += 1

        return True, gap_map

    def step(self) -> bool:
        can_proceed = True
        increasable_indices: deque[int] = deque(maxlen=len(self._state.course_codes))
        solution = Solution()
        solution.classes = [0] * len(self._state.course_codes)
        schedules: list[Schedule] = []

        if can_proceed:
            for course_index, course_code in enumerate(self._state.course_codes):
                class_list = self._state.classes[course_index]
                class_index = self._state.next_class[course_index]
                cl = class_list[class_index]

                if class_index + 1 < len(class_list):
                    increasable_indices.append(course_index)

                solution.pref_cost += cl.total_cost()
                solution.classes[course_index] = class_index
                # Do not proceed if any class has no schedules
                if not cl.schedules:
                    can_proceed = False
                    break
                schedules.extend(cl.schedules)

        if can_proceed:
            # Check for collisions
            can_proceed, sup = self._check_collision_and_count_gap(schedules)
            if not can_proceed:
                # Collision detected, skip this combination
                bad_index = sup
                while increasable_indices and increasable_indices[-1] > bad_index:
                    increasable_indices.pop()
            else:
                # No collisions, proceed to calculate costs
                # Calculate gap penalties
                gaps = sup
                for gap_size, gap_count in gaps.items():
                    gap_penalty = self._state.preferences.gap_penalty[gap_size - 1]
                    if gap_penalty is not None:
                        # penalty = p + p*b + p*b^2 + ... for gap_count times
                        # geometric series sum
                        # total_penalty = p * (b^(n+1) - 1) / (b - 1)
                        solution.gap_cost += int(
                            (gap_penalty.base ** (gap_count + 1) - 1)
                            / (gap_penalty.base - 1)
                            * gap_penalty.penalty
                        )

        if can_proceed:
            # Store solution
            self._state.add_solution(solution)

        # Explored all combinations
        if not increasable_indices:
            self._state.finished = True
            return False

        # Increment the last increasable index and reset the rest
        self._state.next_class[increasable_indices[-1]] += 1
        for course_index in range(
            increasable_indices[-1] + 1, len(self._state.course_codes)
        ):
            self._state.next_class[course_index] = 0
        return True

    def is_finished(self) -> bool:
        return self._state.finished

    def get_state(self) -> "State":
        return self._state

    def set_state(self, state: "State") -> None:
        self._state = state

    def new_state(self) -> "State":
        old_state = self._state
        self._state = State()
        return old_state

    def get_preferences(self) -> Preferences:
        return self._preferences

    def set_preferences(self, preferences: Preferences) -> None:
        self._preferences = preferences


@dataclass
class Solution:
    gap_cost: int = 0
    pref_cost: int = 0
    classes: list[int] = field(default_factory=list)

    def total_cost(self) -> int:
        return self.gap_cost + self.pref_cost

    def dict(self) -> "dict":
        return {
            "gap_cost": self.gap_cost,
            "pref_cost": self.pref_cost,
            "classes": self.classes.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Solution":
        return cls(
            gap_cost=data["gap_cost"],
            pref_cost=data["pref_cost"],
            classes=data["classes"],
        )


class MaxHeapSolution(Solution):
    def __lt__(self, other: "Solution") -> bool:
        return self.total_cost() > other.total_cost()  # Reverse for max-heap

    @classmethod
    def fromSol(cls, sol: Solution) -> "MaxHeapSolution":
        return cls(
            gap_cost=sol.gap_cost,
            pref_cost=sol.pref_cost,
            classes=sol.classes,
        )


class MinHeapSolution(Solution):
    def __lt__(self, other: "Solution") -> bool:
        return self.total_cost() < other.total_cost()  # Normal for min-heap

    @classmethod
    def fromSol(cls, sol: Solution) -> "MinHeapSolution":
        return cls(
            gap_cost=sol.gap_cost,
            pref_cost=sol.pref_cost,
            classes=sol.classes,
        )


@dataclass
class Class:
    class_code: str
    course_code: str
    schedules: list[Schedule]
    global_cost: int = 0
    local_cost: int = 0

    def total_cost(self) -> int:
        return self.global_cost + self.local_cost

    def dict(self) -> "dict":
        return {
            "class_code": self.class_code,
            "course_code": self.course_code,
            "schedules": [s.dict() for s in self.schedules],
            "global_cost": self.global_cost,
            "local_cost": self.local_cost,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Class":
        return cls(
            class_code=data["class_code"],
            course_code=data["course_code"],
            schedules=[Schedule.from_dict(s) for s in data["schedules"]],
            global_cost=data["global_cost"],
            local_cost=data["local_cost"],
        )


@dataclass
class NamelessPreferences:
    global_timetable_prefs: TimeTablePreferences = None
    local_timetable_prefs: list[TimeTablePreferences] = field(default_factory=list)
    gap_penalty: list[GapPenalty] = field(default_factory=list)

    def dict(self) -> "dict":
        return {
            "global": self.global_timetable_prefs.dict(),
            "local": [p.dict() for p in self.local_timetable_prefs],
            "gap_penalty": [gp.dict() for gp in self.gap_penalty],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NamelessPreferences":
        return cls(
            global_timetable_prefs=TimeTablePreferences.from_dict(data["global"]),
            local_timetable_prefs=[
                TimeTablePreferences.from_dict(p) for p in data["local"]
            ],
            gap_penalty=[GapPenalty.from_dict(gp) for gp in data["gap_penalty"]],
        )


@dataclass(unsafe_hash=True)
class State:
    requested_solution_count: int = 0
    preferences: NamelessPreferences = None
    course_codes: list[str] = field(default_factory=list)
    classes: list[list[Class]] = field(default_factory=list)
    next_class: list[int] = field(default_factory=list)
    optimal_solutions: list[Solution] = field(default_factory=list)
    finished: bool = False

    def add_solution(self, solution: Solution) -> None:
        if not isinstance(solution, MaxHeapSolution):
            solution = MaxHeapSolution.fromSol(solution)
        heappush(self.optimal_solutions, solution)
        if len(self.optimal_solutions) > self.requested_solution_count:
            heappop(self.optimal_solutions)

    def dict(self) -> "dict":
        return {
            "requested_solution_count": self.requested_solution_count,
            "preferences": self.preferences.dict(),
            "course_codes": self.course_codes.copy(),
            "classes": [[c.dict() for c in clist] for clist in self.classes],
            "next_class": self.next_class.copy(),
            "optimal_solutions": [s.dict() for s in self.optimal_solutions],
            "finished": self.finished,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "State":
        return cls(
            requested_solution_count=data["requested_solution_count"],
            preferences=NamelessPreferences.from_dict(data["preferences"]),
            course_codes=data["course_codes"],
            classes=[[Class.from_dict(c) for c in clist] for clist in data["classes"]],
            next_class=data["next_class"],
            optimal_solutions=[
                Solution.from_dict(s) for s in data["optimal_solutions"]
            ],
            finished=data["finished"],
        )
