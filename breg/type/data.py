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
from typing import Any

from breg.type.api_internal import EnrollmentID


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
    timestamp: datetime
    course_code: str
    class_code: str
    class_id: str
    student_no: int
    student_capacity: int
    schedules: list["Schedule"]

    def __init__(
        self,
        timestamp: datetime = None,
        course_code: str = None,
        class_code: str = None,
        class_id: str = None,
        student_no: int = None,
        student_capacity: int = None,
        schedules: list["Schedule"] = None,
    ):
        self.timestamp = timestamp if timestamp is not None else datetime.now()
        self.course_code = course_code
        self.class_code = class_code
        self.class_id = class_id
        self.student_no = student_no
        self.student_capacity = student_capacity
        self.schedules = schedules if schedules is not None else []


class Schedule:
    day: "DayBF"
    timeframe: "TimeframeBF"
    week: "WeekBF"
    location: str

    def __init__(
        self,
        day: "DayBF" = None,
        timeframe: "TimeframeBF" = None,
        week: "WeekBF" = None,
        location: str = None,
    ):
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


class CourseCache:
    timestamp: datetime
    course_code: str
    course_name: str
    course_id: str

    def __init__(
        self,
        timestamp: datetime = None,
        course_code: str = None,
        course_name: str = None,
        course_id: str = None,
    ):
        self.timestamp = timestamp if timestamp is not None else datetime.now()
        self.course_code = course_code
        self.course_name = course_name
        self.course_id = course_id


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

    def value(self) -> Any:
        return cast(pointer(self), POINTER(c_uint8)).contents.value

    def __and__(self, other: "DayBF") -> c_uint8:
        return self.value() & other.value() & 0x7F  # Mask out reserved bit

    def __or__(self, other: "DayBF") -> c_uint8:
        return self.value() | other.value() & 0x7F  # Mask out reserved bit

    def __xor__(self, other: "DayBF") -> c_uint8:
        return self.value() ^ other.value() & 0x7F  # Mask out reserved bit

    @classmethod
    def from_int(cls, value: int) -> "DayBF":
        instance = cls()
        cast(pointer(instance), POINTER(c_uint8)).contents.value = (
            value & 0x7F
        )  # Mask out reserved bit
        return instance


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

    def value(self) -> Any:
        return cast(pointer(self), POINTER(c_uint16)).contents.value

    def __and__(self, other: "TimeframeBF") -> c_uint16:
        return self.value() & other.value()

    def __or__(self, other: "TimeframeBF") -> c_uint16:
        return self.value() | other.value()

    def __xor__(self, other: "TimeframeBF") -> c_uint16:
        return self.value() ^ other.value()

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

    def value(self) -> Any:
        return cast(pointer(self), POINTER(c_uint64)).contents.value

    def __and__(self, other: "WeekBF") -> c_uint64:
        return self.value() & other.value()

    def __or__(self, other: "WeekBF") -> c_uint64:
        return self.value() | other.value()

    def __xor__(self, other: "WeekBF") -> c_uint64:
        return self.value() ^ other.value()

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
