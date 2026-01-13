from dataclasses import dataclass
import sys


class PreferenceLevel(int):
    AVOID = sys.maxsize
    NEUTRAL = 0


class TimeframePreferences:
    _prefs: dict[int, PreferenceLevel]
    _MAX_TIMEFRAMES = 16

    def __init__(self) -> None:
        self._prefs = {}
        for i in range(self._MAX_TIMEFRAMES):
            self._prefs[i] = PreferenceLevel.NEUTRAL

    def get(self, timeframe: int) -> PreferenceLevel:
        return self._prefs.get(timeframe, PreferenceLevel.NEUTRAL)  # type: ignore

    def set(self, timeframe: int, level: PreferenceLevel) -> None:
        self._prefs[timeframe] = level

    def dict(self) -> dict:
        return self._prefs.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "TimeframePreferences":
        prefs = cls()
        for timeframe, level in data.items():
            prefs.set(int(timeframe), PreferenceLevel(level))
        return prefs


class NeutralTimeframePreferences(TimeframePreferences):
    def __init__(self) -> None:
        super().__init__()

    def set(self, timeframe: int, level: PreferenceLevel) -> None:
        pass


class DayPreferences:
    _prefs: dict[int, PreferenceLevel]
    _MAX_DAYS = 7

    def __init__(self) -> None:
        self._prefs = {}
        for i in range(self._MAX_DAYS):
            self._prefs[i] = PreferenceLevel.NEUTRAL

    def get(self, day: int) -> PreferenceLevel:
        return self._prefs.get(day, PreferenceLevel.NEUTRAL)  # type: ignore

    def set(self, day: int, timeframe_pref: PreferenceLevel) -> None:
        self._prefs[day] = timeframe_pref

    def dict(self) -> dict:
        return self._prefs.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "DayPreferences":
        prefs = cls()
        for day, level in data.items():
            prefs.set(int(day), PreferenceLevel(level))
        return prefs


class NeutralDayPreferences(DayPreferences):
    def __init__(self) -> None:
        super().__init__()

    def set(self, day: int, level: PreferenceLevel) -> None:
        pass


class WeekPreferences:
    _prefs: dict[int, PreferenceLevel]
    _MAX_WEEKS = 64

    def __init__(self) -> None:
        self._prefs = {}
        for i in range(self._MAX_WEEKS):
            self._prefs[i] = PreferenceLevel.NEUTRAL

    def get(self, week: int) -> PreferenceLevel:
        return self._prefs.get(week, PreferenceLevel.NEUTRAL)  # type: ignore

    def set(self, week: int, day_pref: PreferenceLevel) -> None:
        self._prefs[week] = day_pref

    def dict(self) -> dict:
        return self._prefs.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "WeekPreferences":
        prefs = cls()
        for week, level in data.items():
            prefs.set(int(week), PreferenceLevel(level))
        return prefs


class NeutralWeekPreferences(WeekPreferences):
    def __init__(self) -> None:
        super().__init__()

    def set(self, week: int, level: PreferenceLevel) -> None:
        pass


class TimeTablePreferences:
    _timeframe_prefs: TimeframePreferences
    _day_prefs: DayPreferences
    _week_prefs: WeekPreferences

    def __init__(self) -> None:
        self._timeframe_prefs = TimeframePreferences()
        self._day_prefs = DayPreferences()
        self._week_prefs = WeekPreferences()

    def get_timeframes_prefs(self) -> TimeframePreferences:
        return self._timeframe_prefs

    def get_timeframe(self, timeframe: int) -> PreferenceLevel:
        return self._timeframe_prefs.get(timeframe)

    def set_timeframe(self, timeframe: int, level: PreferenceLevel) -> None:
        self._timeframe_prefs.set(timeframe, level)

    def get_day_prefs(self) -> DayPreferences:
        return self._day_prefs

    def get_day(self, day: int) -> DayPreferences:
        return self._day_prefs.get(day)

    def set_day(self, day: int, level: PreferenceLevel) -> None:
        self._day_prefs.set(day, level)

    def get_week_prefs(self) -> WeekPreferences:
        return self._week_prefs

    def get_week(self, week: int) -> WeekPreferences:
        return self._week_prefs.get(week)

    def set_week(self, week: int, level: PreferenceLevel) -> None:
        self._week_prefs.set(week, level)

    def dict(self) -> dict:
        return {
            "timeframes": self._timeframe_prefs.dict(),
            "days": self._day_prefs.dict(),
            "weeks": self._week_prefs.dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimeTablePreferences":
        prefs: "TimeTablePreferences" = cls()
        prefs._timeframe_prefs = TimeframePreferences.from_dict(data["timeframes"])
        prefs._day_prefs = DayPreferences.from_dict(data["days"])
        prefs._week_prefs = WeekPreferences.from_dict(data["weeks"])
        return prefs


class NeutralTimeTablePreferences(TimeTablePreferences):
    def __init__(self) -> None:
        super().__init__()
        self._timeframe_prefs = NeutralTimeframePreferences()
        self._day_prefs = NeutralDayPreferences()
        self._week_prefs = NeutralWeekPreferences()


@dataclass
class GapPenalty:
    penalty: int
    base: float

    def is_neutral(self) -> bool:
        return self.penalty == 0

    def dict(self) -> dict:
        return {
            "penalty": self.penalty,
            "base": self.base,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GapPenalty":
        return cls(
            penalty=data["penalty"],
            base=data["base"],
        )


@dataclass
class NeutralGapPenalty(GapPenalty):
    penalty: int = 0
    base: float = 1.0

    def __post_init__(self):
        self.penalty = 0
        self.base = 1.0


class Preferences:
    _global_timetable_prefs: TimeTablePreferences
    _local_timetable_prefs: dict[str, TimeTablePreferences]
    _gap_penalty: dict[int, GapPenalty]

    def __init__(self) -> None:
        self._global_timetable_prefs = TimeTablePreferences()
        self._local_timetable_prefs = {}
        self._gap_penalty = {}

        for gap_size in range(1, 6):
            self._gap_penalty[gap_size] = NeutralGapPenalty()

    def get_global_timetable_prefs(self) -> TimeTablePreferences:
        return self._global_timetable_prefs

    def set_global_timetable_prefs(self, prefs: TimeTablePreferences) -> None:
        self._global_timetable_prefs = prefs

    def get_local_timetable_prefs(self, key: str) -> TimeTablePreferences:
        return self._local_timetable_prefs.get(key, NeutralTimeTablePreferences())

    def set_local_timetable_prefs(self, key: str, prefs: TimeTablePreferences) -> None:
        self._local_timetable_prefs[key] = prefs

    def initialize_local_timetable_prefs(self, keys: list[str] | str) -> None:
        if isinstance(keys, str):
            keys = [keys]
        for k in keys:
            if k not in self._local_timetable_prefs:
                self._local_timetable_prefs[k] = TimeTablePreferences()

    def get_gap_penalty(self, gap_size: int) -> GapPenalty:
        return self._gap_penalty.get(gap_size, NeutralGapPenalty())

    def set_gap_penalty(self, gap_size: int, penalty: GapPenalty) -> None:
        self._gap_penalty[gap_size] = penalty

    def dict(self) -> dict:
        return {
            "global": self._global_timetable_prefs.dict(),
            "local": {
                key: prefs.dict() for key, prefs in self._local_timetable_prefs.items()
            },
            "gap_penalty": {k: v.dict() for k, v in self._gap_penalty.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Preferences":
        prefs: "Preferences" = cls()
        prefs._global_timetable_prefs = TimeTablePreferences.from_dict(data["global"])
        for key, tp_data in data["local"].items():
            prefs._local_timetable_prefs[key] = TimeTablePreferences.from_dict(tp_data)
        for gap_size, gp_data in data["gap_penalty"].items():
            prefs._gap_penalty[int(gap_size)] = GapPenalty.from_dict(gp_data)
        return prefs
