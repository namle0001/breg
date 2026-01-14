"""Data types for BReg system."""

from ctypes import (
    POINTER,
    Structure,
    c_uint8,
    c_uint16,
    c_uint64,
    cast,
    pointer,
)
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from breg.type.api_internal import ClassID, EnrollmentID


class Enrollment:
    """Represents a student's enrollment in a specific course and class."""

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
    """Represents cached data for a specific class."""

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
        """Returns the list of fields in the ClassCache.

        Returns:
            list[str]: A list of field names in the ClassCache.
        """
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
    """Represents a schedule instance of a class."""

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
        """Determines if this schedule conflicts with another schedule.

        Args:
            other (Schedule): The other schedule to compare with.

        Returns:
            bool: True if the schedules conflict, False otherwise.
        """
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
        """Converts the Schedule instance to a dictionary.

        Returns:
            dict: A dictionary representation of the Schedule instance.
        """
        return {
            "schedule_id": self.schedule_id,
            "day": self.day.value(),
            "timeframe": self.timeframe.value(),
            "week": self.week.value(),
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, data: "dict") -> "Schedule":
        """Creates a Schedule instance from a dictionary.

        Args:
            data (dict): A dictionary containing schedule data.

        Returns:
            Schedule: A Schedule instance created from the dictionary.
        """
        return cls(
            schedule_id=data.get("schedule_id"),
            day=DayBF.from_int(data.get("day", 0)),
            timeframe=TimeframeBF.from_int(data.get("timeframe", 0)),
            week=WeekBF.from_int(data.get("week", 0)),
            location=data.get("location"),
        )

    @classmethod
    def fields(cls) -> list[str]:
        """Returns the list of fields in the Schedule.

        Returns:
            list[str]: A list of field names in the Schedule.
        """
        return [
            "schedule_id",
            "day",
            "timeframe",
            "week",
            "location",
        ]


class LogicalSchedule(Schedule):
    """A logical representation of a schedule.
    Its instance is an identical Schedule by location, day, timeframe and week.
    """

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
        """Creates a LogicalSchedule instance from a Schedule instance.

        Args:
            schedule (Schedule): The Schedule instance to convert.

        Returns:
            LogicalSchedule: A LogicalSchedule instance created from the Schedule.
        """
        return cls(
            schedule_id=schedule.schedule_id,
            day=schedule.day,
            timeframe=schedule.timeframe,
            week=schedule.week,
            location=schedule.location,
        )

    @classmethod
    def from_schedules(cls, schedules: list[Schedule]) -> "list[LogicalSchedule]":
        """Creates a list of LogicalSchedule instances from a list of Schedule instances.

        Returns:
            list[LogicalSchedule]: A list of LogicalSchedule instances created from the list of Schedule instances.
        """
        return [cls.from_schedule(schedule) for schedule in schedules]


class CourseCache:
    """Represents cached data for a specific course."""

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
        """Returns the list of fields in the CourseCache.

        Returns:
            list[str]: A list of field names in the CourseCache.
        """
        return [
            "cache_id",
            "timestamp",
            "course_code",
            "course_name",
            "course_id",
            "last_checked",
        ]


class DayBF(Structure):
    """Days of the week bitfield representation.
    Each bit represents a day of the week, starting from Monday (bit 0) to Sunday (bit 6).
    The 8th bit is reserved and should be ignored.
    """

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
        """Returns the integer value of the DayBF bitfield.

        Returns:
            int: The integer value of the DayBF bitfield.
        """
        return (
            cast(pointer(self), POINTER(c_uint8)).contents.value & 0x7F
        )  # Mask out reserved bit

    def get(self, day: "Day | int | str") -> int:
        """Gets the value of a specific day in the DayBF.

        Args:
            day (Day | int | str): The day to get the value for.

        Raises:
            ValueError: If the day is invalid.
        Returns:
            int: The value of the specified day in the DayBF.
        """
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
        """Creates a DayBF instance from an integer value.

        Args:
            value (int): The integer value to create the DayBF from.

        Returns:
            DayBF: A DayBF instance created from the given integer value.
        """
        instance = cls()
        # Mask out reserved bit
        cast(pointer(instance), POINTER(c_uint8)).contents.value = value & 0x7F
        return instance

    def dict(self) -> "dict[str, int]":
        """Converts the DayBF instance to a dictionary.

        Returns:
            dict[str, int]: A dictionary representation of the DayBF instance.
        """
        d = {}
        for f in self._fields_[:-1]:  # Exclude reserved
            field_name = f[0]
            field_value = getattr(self, field_name)
            d[field_name] = field_value
        return d

    def list(self) -> "list[int]":
        """Converts the DayBF instance to a list.
        The returned list has each element representing a day of the week,
        and its value is 1 if the day is set, otherwise 0.

        Returns:
            list[int]: A list representation of the DayBF instance.
        """
        return [getattr(self, f[0]) for f in self._fields_[:-1]]  # Exclude reserved


class TimeframeBF(Structure):
    """Timeframes bitfield representation.
    Each bit represents a period, starting from period 1 (bit 0) to period 16 (bit 15).
    """

    # Period 1 to 16
    _fields_ = [(f"period_{i}", c_uint16, 1) for i in range(1, 16 + 1)]

    def value(self) -> int:
        """Returns the integer value of the TimeframeBF bitfield.

        Returns:
            int: The integer value of the TimeframeBF bitfield.
        """
        return cast(pointer(self), POINTER(c_uint16)).contents.value

    def get(self, period: int) -> int:
        """Gets the value of a specific period in the TimeframeBF.

        Args:
            period (int): The period to get the value for.

        Raises:
            ValueError: If the period is not between 1 and 16.

        Returns:
            int: The value of the specified period. 0 if not set, 1 if set.
        """
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
        """Creates a TimeframeBF instance from an integer value.

        Args:
            value (int): The integer value to create the TimeframeBF from.

        Returns:
            TimeframeBF: A TimeframeBF instance created from the given integer value.
        """
        instance = cls()
        cast(pointer(instance), POINTER(c_uint16)).contents.value = value
        return instance

    def dict(self) -> "dict[str, int]":
        """Converts the TimeframeBF instance to a dictionary.

        Returns:
            dict[str, int]: A dictionary representation of the TimeframeBF instance.
        """
        d = {}
        for f in self._fields_:
            field_name = f[0]
            field_value = getattr(self, field_name)
            d[field_name] = field_value
        return d

    def list(self) -> "list[int]":
        """Converts the TimeframeBF instance to a list.

        Returns:
            list[int]: A list representation of the TimeframeBF instance.
        """
        return [getattr(self, f[0]) for f in self._fields_]


class WeekBF(Structure):
    """Weeks bitfield representation.
    Each bit represents a week, starting from week 1 (bit 0) to week 64 (bit 63).
    """

    # Week 1 to 64
    _fields_ = [(f"week_{i}", c_uint64, 1) for i in range(1, 64 + 1)]

    def value(self) -> int:
        """Returns the integer value of the WeekBF bitfield.

        Returns:
            int: The integer value of the WeekBF bitfield.
        """
        return cast(pointer(self), POINTER(c_uint64)).contents.value

    def get(self, week: int) -> int:
        """Gets the value of a specific week in the WeekBF.

        Args:
            week (int): The week number to get the value for.

        Raises:
            ValueError: If the week is not between 1 and 64.

        Returns:
            int: The toggle value of the specified week. 0 if not set, 1 if set.
        """
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
        """Creates a WeekBF instance from an integer representation.

        Args:
            value (int): The integer value to create the WeekBF from.

        Returns:
            WeekBF: A WeekBF instance created from the given integer value.
        """
        instance = cls()
        cast(pointer(instance), POINTER(c_uint64)).contents.value = value
        return instance

    def dict(self) -> "dict[str, int]":
        """Converts the WeekBF instance to a dictionary.

        Returns:
            dict[str, int]: A dictionary representation of the WeekBF instance.
        """
        d = {}
        for f in self._fields_:
            field_name = f[0]
            field_value = getattr(self, field_name)
            d[field_name] = field_value
        return d

    def list(self) -> "list[int]":
        """Converts the WeekBF instance to a list.

        Returns:
            list[int]: A list representation of the WeekBF instance.
        """
        return [getattr(self, f[0]) for f in self._fields_]


class Day(StrEnum):
    """Enumeration for days of the week."""

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
        """Returns the Day enum member corresponding to the given string.

        Args:
            day_str (str): The string representation of the day.

        Raises:
            ValueError: If the day string is not valid.

        Returns:
            Day: The Day enum member corresponding to the given string.
        """
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
        """Returns the Day enum member corresponding to the given integer.
        Start from 0 (Monday) to 6 (Sunday).

        Args:
            value (int): The integer representation of the day.

        Raises:
            ValueError: If the integer is not between 0 and 6.

        Returns:
            Day: The Day enum member corresponding to the given integer.
        """
        if value in cls.__day_map():
            return cls.__day_map()[value]
        raise ValueError(f"Invalid day integer: {value}")

    def to_int(self) -> int:
        """Returns the integer representation of the Day enum member.
        Start from 0 (Monday) to 6 (Sunday).

        Raises:
            ValueError: If the Day enum member is invalid.

        Returns:
            int: The integer representation of the Day enum member.
        """
        for key, val in self.__day_map().items():
            if val == self:
                return key
        raise ValueError(f"Invalid day enum: {self}")


@dataclass
class Round:
    """Represents a round of course registration."""

    round_id: str = None
    round_name: str = None
    round_title: str = None
    start_time: str = None
    end_time: str = None


@dataclass
class Seed:
    """Represents a seed of course registration."""

    seed_id: str = None
    seed_title: str = None
