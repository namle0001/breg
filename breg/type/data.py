from ctypes import (
    Structure,
    c_uint8,
    c_uint16,
    c_uint64,
    cast,
    POINTER,
    pointer,
)
from datetime import datetime
from enum import StrEnum

from breg.type.api_internal import EnrollmentID, ClassID


class Enrollment:
    enrollment_id: EnrollmentID
    course_code: str
    class_code: str

    def __init__(
        self,
        enrollment_id: EnrollmentID = None,
        course_code: str = None,
        class_code: str = None,
    ):
        self.enrollment_id = enrollment_id
        self.course_code = course_code
        self.class_code = class_code


class ClassCache:
    cache_id: int
    timestamp: datetime
    course_code: str
    class_code: str
    class_id: ClassID
    student_no: int
    student_capacity: int
    schedules: list["Schedule"]
    last_checked: datetime

    def __init__(
        self,
        cache_id: int = None,
        timestamp: datetime = None,
        course_code: str = None,
        class_code: str = None,
        class_id: ClassID = None,
        student_no: int = None,
        student_capacity: int = None,
        schedules: list["Schedule"] = None,
        last_checked: datetime = None,
    ):
        self.cache_id = cache_id
        self.timestamp = timestamp if timestamp is not None else datetime.now()
        self.course_code = course_code
        self.class_code = class_code
        self.class_id = class_id
        self.student_no = student_no
        self.student_capacity = student_capacity
        self.schedules = schedules if schedules is not None else []
        self.last_checked = last_checked if last_checked is not None else datetime.now()

    @classmethod
    def fields(cls) -> list[str]:
        return [
            "cache_id",
            "timestamp",
            "course_code",
            "class_code",
            "class_id",
            "student_no",
            "student_capacity",
            "schedules",
            "last_checked",
        ]


class Schedule:
    schedule_id: int
    day: "DayBF"
    timeframe: "TimeframeBF"
    week: "WeekBF"
    location: str

    def __init__(
        self,
        schedule_id: int = None,
        day: "DayBF" = None,
        timeframe: "TimeframeBF" = None,
        week: "WeekBF" = None,
        location: str = None,
    ):
        self.schedule_id = schedule_id
        self.day = day
        self.timeframe = timeframe
        self.week = week
        self.location = location

    def conflicts_with(self, other: "Schedule") -> bool:
        if not self.day & other.day:
            return False
        if not self.timeframe & other.timeframe:
            return False
        if not self.week & other.week:
            return False
        return True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Schedule):
            return NotImplemented

        return (
            self.schedule_id == other.schedule_id
            and self.location == other.location
            and self.day == other.day
            and self.timeframe == other.timeframe
            and self.week == other.week
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.schedule_id,
                self.location,
                self.day,
                self.timeframe,
                self.week,
            )
        )

    def dict(self) -> "dict":
        return {
            "schedule_id": self.schedule_id,
            "day": self.day.value(),
            "timeframe": self.timeframe.value(),
            "week": self.week.value(),
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, data: "dict") -> "Schedule":
        return cls(
            schedule_id=data.get("schedule_id"),
            day=DayBF.from_int(data.get("day", 0)),
            timeframe=TimeframeBF.from_int(data.get("timeframe", 0)),
            week=WeekBF.from_int(data.get("week", 0)),
            location=data.get("location"),
        )

    @classmethod
    def fields(cls) -> list[str]:
        return [
            "schedule_id",
            "day",
            "timeframe",
            "week",
            "location",
        ]


class LogicalSchedule(Schedule):
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LogicalSchedule):
            return NotImplemented
        return (
            self.location == other.location
            and self.day == other.day
            and self.timeframe == other.timeframe
            and self.week == other.week
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.location,
                self.day,
                self.timeframe,
                self.week,
            )
        )

    @classmethod
    def from_schedule(cls, schedule: Schedule) -> "LogicalSchedule":
        return cls(
            schedule_id=schedule.schedule_id,
            day=schedule.day,
            timeframe=schedule.timeframe,
            week=schedule.week,
            location=schedule.location,
        )

    @classmethod
    def from_schedules(cls, schedules: list[Schedule]) -> list["LogicalSchedule"]:
        return [cls.from_schedule(schedule) for schedule in schedules]


class CourseCache:
    cache_id: int
    timestamp: datetime
    course_code: str
    course_name: str
    course_id: str
    last_checked: datetime

    def __init__(
        self,
        cache_id: int = None,
        timestamp: datetime = None,
        course_code: str = None,
        course_name: str = None,
        course_id: str = None,
        last_checked: datetime = None,
    ):
        self.cache_id = cache_id
        self.timestamp = timestamp if timestamp is not None else datetime.now()
        self.course_code = course_code
        self.course_name = course_name
        self.course_id = course_id
        self.last_checked = last_checked if last_checked is not None else datetime.now()

    @classmethod
    def fields(cls) -> list[str]:
        return [
            "cache_id",
            "timestamp",
            "course_code",
            "course_name",
            "course_id",
            "last_checked",
        ]


class DayBF(Structure):
    _fields_ = [
        ("mon", c_uint8, 1),
        ("tue", c_uint8, 1),
        ("wed", c_uint8, 1),
        ("thu", c_uint8, 1),
        ("fri", c_uint8, 1),
        ("sat", c_uint8, 1),
        ("sun", c_uint8, 1),
        ("reserved", c_uint8, 1),
    ]

    def value(self) -> int:
        return (
            cast(pointer(self), POINTER(c_uint8)).contents.value & 0x7F
        )  # Mask out reserved bit

    def get(self, day: "Day | int | str") -> int:
        if isinstance(day, Day):
            day_str = day.value
        elif isinstance(day, int):
            day_str = Day.from_int(day - 1).value
        elif isinstance(day, str):
            day_str = day.lower()
        else:
            raise ValueError("Invalid day type")

        if day_str in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
            return getattr(self, day_str)
        raise ValueError(f"Invalid day string: {day_str}")

    def __and__(self, other: "DayBF") -> int:
        return self.value() & other.value()

    def __or__(self, other: "DayBF") -> int:
        return self.value() | other.value()

    def __xor__(self, other: "DayBF") -> int:
        return self.value() ^ other.value()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DayBF):
            return NotImplemented
        return self.value() == other.value()

    def __hash__(self) -> int:
        return hash(self.value())

    @classmethod
    def from_int(cls, value: int) -> "DayBF":
        instance = cls()
        # Mask out reserved bit
        cast(pointer(instance), POINTER(c_uint8)).contents.value = value & 0x7F
        return instance

    def dict(self) -> "dict[str, int]":
        d = {}
        for f in self._fields_[:-1]:  # Exclude reserved
            field_name = f[0]
            field_value = getattr(self, field_name)
            d[field_name] = field_value
        return d

    def list(self) -> "list[int]":
        return [getattr(self, f[0]) for f in self._fields_[:-1]]  # Exclude reserved


class TimeframeBF(Structure):
    _fields_ = [
        ("period_1", c_uint16, 1),
        ("period_2", c_uint16, 1),
        ("period_3", c_uint16, 1),
        ("period_4", c_uint16, 1),
        ("period_5", c_uint16, 1),
        ("period_6", c_uint16, 1),
        ("period_7", c_uint16, 1),
        ("period_8", c_uint16, 1),
        ("period_9", c_uint16, 1),
        ("period_10", c_uint16, 1),
        ("period_11", c_uint16, 1),
        ("period_12", c_uint16, 1),
        ("period_13", c_uint16, 1),
        ("period_14", c_uint16, 1),
        ("period_15", c_uint16, 1),
        ("period_16", c_uint16, 1),
    ]

    def value(self) -> int:
        return cast(pointer(self), POINTER(c_uint16)).contents.value

    def get(self, period: int) -> int:
        if 1 <= period <= 16:
            return getattr(self, f"period_{period}")
        raise ValueError("Period must be between 1 and 16")

    def __and__(self, other: "TimeframeBF") -> int:
        return self.value() & other.value()

    def __or__(self, other: "TimeframeBF") -> int:
        return self.value() | other.value()

    def __xor__(self, other: "TimeframeBF") -> int:
        return self.value() ^ other.value()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TimeframeBF):
            return NotImplemented
        return self.value() == other.value()

    def __hash__(self) -> int:
        return hash(self.value())

    @classmethod
    def from_int(cls, value: int) -> "TimeframeBF":
        instance = cls()
        cast(pointer(instance), POINTER(c_uint16)).contents.value = value
        return instance

    @classmethod
    def from_timeframe_str(cls, timeframe_str: str) -> "TimeframeBF":
        timeframe_bf = cls()
        periods = timeframe_str.split(None)
        for period in periods:
            if not period.isdigit():
                continue
            period_int = int(period)
            if 1 <= period_int <= 16:
                setattr(timeframe_bf, f"period_{period_int}", 1)

        return timeframe_bf

    def dict(self) -> "dict[str, int]":
        d = {}
        for f in self._fields_:
            field_name = f[0]
            field_value = getattr(self, field_name)
            d[field_name] = field_value
        return d

    def list(self) -> "list[int]":
        return [getattr(self, f[0]) for f in self._fields_]


class WeekBF(Structure):
    _fields_ = [
        ("week_1", c_uint64, 1),
        ("week_2", c_uint64, 1),
        ("week_3", c_uint64, 1),
        ("week_4", c_uint64, 1),
        ("week_5", c_uint64, 1),
        ("week_6", c_uint64, 1),
        ("week_7", c_uint64, 1),
        ("week_8", c_uint64, 1),
        ("week_9", c_uint64, 1),
        ("week_10", c_uint64, 1),
        ("week_11", c_uint64, 1),
        ("week_12", c_uint64, 1),
        ("week_13", c_uint64, 1),
        ("week_14", c_uint64, 1),
        ("week_15", c_uint64, 1),
        ("week_16", c_uint64, 1),
        ("week_17", c_uint64, 1),
        ("week_18", c_uint64, 1),
        ("week_19", c_uint64, 1),
        ("week_20", c_uint64, 1),
        ("week_21", c_uint64, 1),
        ("week_22", c_uint64, 1),
        ("week_23", c_uint64, 1),
        ("week_24", c_uint64, 1),
        ("week_25", c_uint64, 1),
        ("week_26", c_uint64, 1),
        ("week_27", c_uint64, 1),
        ("week_28", c_uint64, 1),
        ("week_29", c_uint64, 1),
        ("week_30", c_uint64, 1),
        ("week_31", c_uint64, 1),
        ("week_32", c_uint64, 1),
        ("week_33", c_uint64, 1),
        ("week_34", c_uint64, 1),
        ("week_35", c_uint64, 1),
        ("week_36", c_uint64, 1),
        ("week_37", c_uint64, 1),
        ("week_38", c_uint64, 1),
        ("week_39", c_uint64, 1),
        ("week_40", c_uint64, 1),
        ("week_41", c_uint64, 1),
        ("week_42", c_uint64, 1),
        ("week_43", c_uint64, 1),
        ("week_44", c_uint64, 1),
        ("week_45", c_uint64, 1),
        ("week_46", c_uint64, 1),
        ("week_47", c_uint64, 1),
        ("week_48", c_uint64, 1),
        ("week_49", c_uint64, 1),
        ("week_50", c_uint64, 1),
        ("week_51", c_uint64, 1),
        ("week_52", c_uint64, 1),
        ("week_53", c_uint64, 1),
        ("week_54", c_uint64, 1),
        ("week_55", c_uint64, 1),
        ("week_56", c_uint64, 1),
        ("week_57", c_uint64, 1),
        ("week_58", c_uint64, 1),
        ("week_59", c_uint64, 1),
        ("week_60", c_uint64, 1),
        ("week_61", c_uint64, 1),
        ("week_62", c_uint64, 1),
        ("week_63", c_uint64, 1),
        ("week_64", c_uint64, 1),
    ]

    def value(self) -> int:
        return cast(pointer(self), POINTER(c_uint64)).contents.value

    def get(self, week: int) -> int:
        if 1 <= week <= 64:
            return getattr(self, f"week_{week}")
        raise ValueError("Week must be between 1 and 64")

    def __and__(self, other: "WeekBF") -> int:
        return self.value() & other.value()

    def __or__(self, other: "WeekBF") -> int:
        return self.value() | other.value()

    def __xor__(self, other: "WeekBF") -> int:
        return self.value() ^ other.value()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WeekBF):
            return NotImplemented
        return self.value() == other.value()

    def __hash__(self) -> int:
        return hash(self.value())

    @classmethod
    def from_int(cls, value: int) -> "WeekBF":
        instance = cls()
        cast(pointer(instance), POINTER(c_uint64)).contents.value = value
        return instance

    @classmethod
    def from_week_str(cls, week_str: str) -> "WeekBF":
        week_bf = cls()
        week = 0

        while week < len(week_str):
            if week_str[week] != "-":
                setattr(week_bf, f"week_{week + 1}", 1)
            week += 1

        return week_bf

    def dict(self) -> "dict[str, int]":
        d = {}
        for f in self._fields_:
            field_name = f[0]
            field_value = getattr(self, field_name)
            d[field_name] = field_value
        return d

    def list(self) -> "list[int]":
        return [getattr(self, f[0]) for f in self._fields_]


class Day(StrEnum):
    MONDAY = "mon"
    TUESDAY = "tue"
    WEDNESDAY = "wed"
    THURSDAY = "thu"
    FRIDAY = "fri"
    SATURDAY = "sat"
    SUNDAY = "sun"

    __day_map: dict[int, "Day"]

    @classmethod
    def from_str(cls, day_str: str) -> "Day":
        day_str = day_str.lower()
        for day in cls:
            if day.value == day_str:
                return day
        raise ValueError(f"Invalid day string: {day_str}")

    @classmethod
    def __day_map(cls):
        return {
            0: Day.MONDAY,
            1: Day.TUESDAY,
            2: Day.WEDNESDAY,
            3: Day.THURSDAY,
            4: Day.FRIDAY,
            5: Day.SATURDAY,
            6: Day.SUNDAY,
        }

    @classmethod
    def from_int(cls, value: int) -> "Day":
        if value in cls.__day_map():
            return cls.__day_map()[value]
        raise ValueError(f"Invalid day integer: {value}")

    def to_int(self) -> int:
        for key, val in self.__day_map().items():
            if val == self:
                return key
        raise ValueError(f"Invalid day enum: {self}")
