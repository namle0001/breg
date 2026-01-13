from dataclasses import dataclass, field
from datetime import datetime
from sqlite3 import Connection, connect
from threading import RLock
from typing import Any
from pathlib import Path

from breg.core.database.database import Database
from breg.type.data import (
    ClassCache,
    CourseCache,
    DayBF,
    Enrollment,
    LogicalSchedule,
    Schedule,
    TimeframeBF,
    WeekBF,
)


def _lock_method(lock_attr: str):
    def decorator[T](func: T) -> T:
        def wrapper(self, *args, **kwargs):
            with getattr(self, lock_attr):
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


class SQLite(Database):
    _cache_db_path: str
    _enrollment_db_path: str
    _cache_connection: Connection
    _enrollment_connection: Connection
    _lock: RLock

    def __init__(
        self, cache_db_path: str = None, enrollment_db_path: str = None
    ) -> None:
        need_cache_migration = False
        need_enrollment_migration = False
        if cache_db_path and not Path.exists(cache_db_path):
            need_cache_migration = True
        if enrollment_db_path and not Path.exists(enrollment_db_path):
            need_enrollment_migration = True

        self._cache_db_path = cache_db_path
        self._enrollment_db_path = enrollment_db_path
        self._cache_connection = connect(cache_db_path) if cache_db_path else None
        self._enrollment_connection = (
            connect(enrollment_db_path) if enrollment_db_path else None
        )
        self._lock = RLock()

        if need_cache_migration:
            self._migrate_cache()
        if need_enrollment_migration:
            self._migrate_enrollment()

    def _migrate_cache(self) -> None:
        self._cache_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS class_cache (
                cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT NOT NULL,
                class_code TEXT NOT NULL,
                student_no INTEGER NOT NULL,
                student_capacity INTEGER NOT NULL,
                class_id TEXT DEFAULT NULL,

                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (timestamp, course_code, class_code)
            );

            CREATE TABLE IF NOT EXISTS schedule (
                schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL,
                timeframe INTEGER NOT NULL,
                week INTEGER NOT NULL,
                location TEXT
            );

            CREATE TABLE IF NOT EXISTS class_cache_schedule_link (
                class_cache_id INTEGER NOT NULL,
                schedule_id INTEGER NOT NULL,

                PRIMARY KEY (class_cache_id, schedule_id),
                FOREIGN KEY (class_cache_id) REFERENCES class_cache(cache_id),
                FOREIGN KEY (schedule_id) REFERENCES schedule(schedule_id)
            );

            CREATE TABLE IF NOT EXISTS course_cache (
                cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT NOT NULL,
                course_name TEXT NOT NULL,
                course_id TEXT DEFAULT NULL,

                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (timestamp, course_code)
            )"""
        )

    def _migrate_enrollment(self) -> None:
        self._enrollment_connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS enrollment (
                enrollment_id INTEGER DEFAULT NULL,
                course_code TEXT NOT NULL,
                class_code TEXT NOT NULL,

                PRIMARY KEY (course_code, class_code)
            )"""
        )

    def _check_connection_alive(self, attr: str) -> bool:
        if getattr(self, attr) is None:
            return False
        try:
            getattr(self, attr).cursor().execute("SELECT 1")
        except Exception:
            return False
        return True

    def _get_cache_connection(self) -> Connection:
        if not self._check_connection_alive("_cache_connection"):
            if not self._db_path:
                raise ValueError("Database path is not set")
            self._cache_connection = connect(self._db_path)
        return self._cache_connection

    def _get_enrollment_connection(self) -> Connection:
        if not self._check_connection_alive("_enrollment_connection"):
            if not self._enrollment_db_path:
                raise ValueError("Enrollment database path is not set")
            self._enrollment_connection = connect(self._enrollment_db_path)
        return self._enrollment_connection

    @_lock_method(lock_attr="_lock")
    def get_course_caches(
        self,
        *,
        course_code: str | list[str] = None,
        course_name: str | list[str] = None,
        course_id: str | list[str] = None,
        after: datetime = None,
    ) -> list[CourseCache]:
        if all(v is None for v in [course_code, course_name, course_id]):
            raise ValueError("At least one filter must be provided")

        cursor = self._get_cache_connection().cursor()
        query = "SELECT cache_id, course_id, course_code, course_name, timestamp, last_checked FROM course_cache"
        conditions = []
        parameters = []

        if course_code:
            self._append_condition("course_code", course_code, conditions, parameters)
        if course_name:
            self._append_condition("course_name", course_name, conditions, parameters)
        if course_id:
            self._append_condition("course_id", course_id, conditions, parameters)
        if after:
            conditions.append("timestamp >= ?")
            parameters.append(after.isoformat())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Order by latest timestamp
        query += " ORDER BY timestamp DESC"

        cursor.execute(query, parameters)
        rows = cursor.fetchall()
        course_caches = [
            CourseCache(
                cache_id=row[0],
                course_id=row[1],
                course_code=row[2],
                course_name=row[3],
                timestamp=datetime.fromisoformat(row[4]),
                last_checked=datetime.fromisoformat(row[5]),
            )
            for row in rows
        ]
        return course_caches

    @_lock_method(lock_attr="_lock")
    def get_all_course_caches(self):
        cursor = self._get_cache_connection().cursor()
        cursor.execute(
            "SELECT course_id, course_code, course_name, timestamp FROM course_cache ORDER BY timestamp DESC"
        )
        rows = cursor.fetchall()
        course_caches = [
            CourseCache(
                course_id=row[0],
                course_code=row[1],
                course_name=row[2],
                timestamp=datetime.fromisoformat(row[3]),
            )
            for row in rows
        ]
        return course_caches

    @_lock_method(lock_attr="_lock")
    def get_complete_course_cache(
        self,
        *,
        course_code: str = None,
        course_name: str = None,
        course_id: str = None,
        after: datetime = None,
    ) -> CourseCache | None:
        course_caches = self.get_course_caches(
            course_code=course_code,
            course_name=course_name,
            course_id=course_id,
            after=after,
        )

        complete_cache: CourseCache = CourseCache()
        if not course_caches:
            return None
        for f in CourseCache.fields():
            for cache in course_caches:
                value = getattr(cache, f)
                if value is not None:
                    setattr(complete_cache, f, value)
                    break

        return complete_cache

    @_lock_method(lock_attr="_lock")
    def save_course_caches(self, course_caches: list[CourseCache] | CourseCache) -> int:
        if not isinstance(course_caches, list):
            course_caches = [course_caches]

        cursor = self._get_cache_connection().cursor()
        for cache in course_caches:
            old_caches = self.get_course_caches(
                course_code=cache.course_code,
                course_name=cache.course_name,
                course_id=cache.course_id,
            )
            if old_caches:
                cursor.execute(
                    "UPDATE course_cache SET last_checked = CURRENT_TIMESTAMP WHERE cache_id = ?",
                    (old_caches[0].cache_id,),
                )
            else:
                cursor.execute(
                    "INSERT INTO course_cache (course_code, course_name, course_id, timestamp) VALUES (?, ?, ?, ?)",
                    (
                        cache.course_code,
                        cache.course_name,
                        cache.course_id,
                        cache.timestamp.isoformat(),
                    ),
                )

        self._get_cache_connection().commit()
        return cursor.rowcount

    @_lock_method(lock_attr="_lock")
    def remove_course_caches(self, course_ids: list[int] | int) -> int:
        if not isinstance(course_ids, list):
            course_ids = [course_ids]

        cursor = self._get_cache_connection().cursor()
        cursor.execute(
            f"""
            DELETE FROM course_cache
            WHERE course_id IN ({",".join(["?"] * len(course_ids))})
            """,
            course_ids,
        )
        self._get_cache_connection().commit()

        return cursor.rowcount

    @_lock_method(lock_attr="_lock")
    def get_class_caches(
        self,
        *,
        course_code: str | list[str] = None,
        class_code: str | list[str] = None,
        class_id: str | list[str] = None,
        after: datetime = None,
        query_schedules: bool = True,
    ) -> list[ClassCache]:
        if all(v is None for v in [course_code, class_code, class_id]):
            raise ValueError("At least one filter must be provided")

        cursor = self._get_cache_connection().cursor()
        query: str = ""
        if not query_schedules:
            query = "SELECT cache_id, class_id, course_code, class_code, student_no, student_capacity, timestamp FROM class_cache"
        else:
            query = """SELECT
                        class_cache.cache_id AS cache_id,
                        class_cache.class_id AS class_id,
                        class_cache.course_code AS course_code,
                        class_cache.class_code AS class_code,
                        class_cache.student_no AS student_no,
                        class_cache.student_capacity AS student_capacity,
                        class_cache.timestamp AS timestamp,
                        
                        schedule.schedule_id AS schedule_id,
                        schedule.day AS schedule_day,
                        schedule.timeframe AS schedule_timeframe,
                        schedule.week AS schedule_week,
                        schedule.location AS schedule_location
                    FROM class_cache

                JOIN class_cache_schedule_link
                    ON class_cache.cache_id=class_cache_schedule_link.class_cache_id
                JOIN schedule
                    ON schedule.schedule_id=class_cache_schedule_link.schedule_id
                
            """
        conditions = []
        parameters = []

        if course_code:
            self._append_condition(
                "class_cache.course_code", course_code, conditions, parameters
            )
        if class_code:
            self._append_condition(
                "class_cache.class_code", class_code, conditions, parameters
            )
        if class_id:
            self._append_condition(
                "class_cache.class_id", class_id, conditions, parameters
            )
        if after:
            conditions.append("class_cache.timestamp >= ?")
            parameters.append(after.isoformat())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Order by latest timestamp
        query += " ORDER BY class_cache.timestamp DESC"

        cursor.execute(query, parameters)
        return self.__parse_class_data(cursor.fetchall(), query_schedules)

    @_lock_method(lock_attr="_lock")
    def get_all_class_caches(self, query_schedules: bool = True) -> list[ClassCache]:
        cursor = self._get_cache_connection().cursor()
        query: str = ""
        if not query_schedules:
            query = "SELECT cache_id, class_id, course_code, class_code, student_no, student_capacity, timestamp FROM class_cache ORDER BY timestamp DESC"
        else:
            query = """SELECT
                        class_cache.cache_id AS cache_id,
                        class_cache.class_id AS class_id,
                        class_cache.course_code AS course_code,
                        class_cache.class_code AS class_code,
                        class_cache.student_no AS student_no,
                        class_cache.student_capacity AS student_capacity,
                        class_cache.timestamp AS timestamp,
                        
                        schedule.schedule_id AS schedule_id,
                        schedule.day AS schedule_day,
                        schedule.timeframe AS schedule_timeframe,
                        schedule.week AS schedule_week,
                        schedule.location AS schedule_location
                    FROM class_cache

                JOIN class_cache_schedule_link
                    ON class_cache.cache_id=class_cache_schedule_link.class_cache_id
                JOIN schedule
                    ON schedule.schedule_id=class_cache_schedule_link.schedule_id
                ORDER BY class_cache.timestamp DESC
                """

        cursor.execute(query)
        return self.__parse_class_data(cursor.fetchall(), query_schedules)

    @classmethod
    def __parse_class_data(
        cls, rows: list[Any], query_schedules: bool
    ) -> list[ClassCache]:
        classes_map: dict[int, ClassCache] = {}
        for row in rows:
            cache_id = row[0]
            if cache_id not in classes_map:
                classes_map[cache_id] = ClassCache(
                    cache_id=cache_id,
                    class_id=row[1],
                    course_code=row[2],
                    class_code=row[3],
                    student_no=row[4],
                    student_capacity=row[5],
                    timestamp=datetime.fromisoformat(row[6]),
                )
            if query_schedules:
                classes_map[cache_id].schedules.append(
                    Schedule(
                        schedule_id=row[7],
                        day=DayBF.from_int(row[8]),
                        timeframe=TimeframeBF.from_int(row[9]),
                        week=WeekBF.from_int(row[10]),
                        location=row[11],
                    )
                )
        class_caches = list(classes_map.values())

        return class_caches

    @_lock_method(lock_attr="_lock")
    def get_complete_class_cache(
        self,
        *,
        course_code: str = None,
        class_code: str = None,
        class_id: str = None,
        after: datetime = None,
        query_schedules: bool = True,
    ) -> ClassCache | None:
        class_caches = self.get_class_caches(
            course_code=course_code,
            class_code=class_code,
            class_id=class_id,
            after=after,
            query_schedules=query_schedules,
        )
        complete_cache: ClassCache = ClassCache()
        if not class_caches:
            return None
        for f in ClassCache.fields():
            for cache in class_caches:
                value = getattr(cache, f)
                if value is not None:
                    setattr(complete_cache, f, value)
                    break

        return complete_cache

    @_lock_method(lock_attr="_lock")
    def save_class_caches(
        self,
        class_caches: list[ClassCache] | ClassCache,
    ) -> int:
        if not isinstance(class_caches, list):
            class_caches = [class_caches]

        non_schedule_caches = [cache for cache in class_caches if not cache.schedules]
        schedule_caches = [cache for cache in class_caches if cache.schedules]
        if non_schedule_caches:
            self._lol_thats_a_lot(non_schedule_caches, has_schedules=False)
        if schedule_caches:
            self._lol_thats_a_lot(schedule_caches, has_schedules=True)
        self._get_cache_connection().commit()

        return len(class_caches)

    @dataclass
    class _FairlySimpleState:
        old_cache: ClassCache = None
        old_cache_match: bool = False
        check_schedules: bool = False
        old_schedules_exist: bool = False
        old_schedules_match: bool = False

        matched_schedules: list[Schedule] = field(default_factory=list)
        unmatched_schedules: list[Schedule] = field(default_factory=list)

        new_cache_id: int = None

        def need_new_cache(self) -> bool:
            if self.old_cache is None or not self.old_cache_match:
                return True
            if self.check_schedules:
                if not self.old_schedules_exist or not self.old_schedules_match:
                    return True
            return False

    def _insert_schedule(self, schedule: Schedule) -> int:
        cursor = self._get_cache_connection().cursor()
        cursor.execute(
            "INSERT INTO schedule (day, timeframe, week, location) VALUES (?, ?, ?, ?)",
            (
                schedule.day.value(),
                schedule.timeframe.value(),
                schedule.week.value(),
                schedule.location,
            ),
        )
        if cursor.rowcount > 0:
            return cursor.lastrowid
        else:
            return None

    def _get_schedule_id(self, schedule: Schedule) -> int:
        cursor = self._get_cache_connection().cursor()
        cursor.execute(
            "SELECT schedule_id FROM schedule WHERE day = ? AND timeframe = ? AND week = ? AND location = ? ORDER BY schedule_id DESC LIMIT 1",
            (
                schedule.day.value(),
                schedule.timeframe.value(),
                schedule.week.value(),
                schedule.location,
            ),
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None

    def _lol_thats_a_lot(self, caches: list[ClassCache], has_schedules: bool) -> None:
        # Attempt to find existing caches
        old_caches = self.get_class_caches(
            course_code=[cache.course_code for cache in caches],
            class_code=[cache.class_code for cache in caches],
            query_schedules=has_schedules,
        )

        old_caches_map = {}
        for cache in old_caches:
            if (cache.course_code, cache.class_code) not in old_caches_map:
                old_caches_map[(cache.course_code, cache.class_code)] = cache

        for new_cache in caches:
            state = self._FairlySimpleState(check_schedules=has_schedules)

            if (new_cache.course_code, new_cache.class_code) in old_caches_map:
                state.old_cache = old_caches_map[
                    (new_cache.course_code, new_cache.class_code)
                ]

            if state.old_cache is not None:

                def need_renew(new_val: Any | None, old_val: Any | None) -> bool:
                    return new_val is not None and new_val != old_val

                if any(
                    need_renew(
                        getattr(new_cache, field), getattr(state.old_cache, field)
                    )
                    for field in ["class_id", "student_no", "student_capacity"]
                ):
                    state.old_cache_match = False
                else:
                    state.old_cache_match = True

            # Check schedules

            # After the if statement below,
            # matched_schedules will contain schedules that are the same in both old and new cache
            # unmatched_schedules will contain schedules that are only in the new cache
            if state.check_schedules:
                if state.old_cache is not None and state.old_cache.schedules:
                    state.old_schedules_exist = True
                    old_logical_schedules_map: dict[LogicalSchedule, Schedule] = {}
                    old_logical_schedules_set: set[LogicalSchedule] = set()
                    new_logical_schedules_map: dict[LogicalSchedule, Schedule] = {}
                    new_logical_schedules_set: set[LogicalSchedule] = set()
                    for schedule in state.old_cache.schedules:
                        logical_schedule = LogicalSchedule.from_schedule(schedule)
                        old_logical_schedules_map[logical_schedule] = schedule
                        old_logical_schedules_set.add(logical_schedule)
                    for schedule in new_cache.schedules:
                        logical_schedule = LogicalSchedule.from_schedule(schedule)
                        new_logical_schedules_map[logical_schedule] = schedule
                        new_logical_schedules_set.add(logical_schedule)

                    for logical_schedule in new_logical_schedules_set.intersection(
                        old_logical_schedules_set
                    ):
                        state.matched_schedules.append(
                            old_logical_schedules_map[logical_schedule]
                        )

                    for logical_schedule in new_logical_schedules_set.difference(
                        old_logical_schedules_set
                    ):
                        state.unmatched_schedules.append(
                            new_logical_schedules_map[logical_schedule]
                        )

                    state.old_schedules_match = (
                        old_logical_schedules_set == new_logical_schedules_set
                    )
                else:
                    state.unmatched_schedules = new_cache.schedules.copy()

            cursor = self._get_cache_connection().cursor()
            if state.need_new_cache():
                cursor.execute(
                    "INSERT INTO class_cache (class_id, student_no, student_capacity, course_code, class_code, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        new_cache.class_id,
                        new_cache.student_no,
                        new_cache.student_capacity,
                        new_cache.course_code,
                        new_cache.class_code,
                        new_cache.timestamp.isoformat(),
                    ),
                )
                if cursor.rowcount > 0:
                    state.new_cache_id = cursor.lastrowid
            else:
                cursor.execute(
                    "UPDATE class_cache SET last_checked = CURRENT_TIMESTAMP WHERE cache_id = ?",
                    (state.old_cache.cache_id,),
                )
            # Link schedules
            if state.check_schedules and state.new_cache_id is not None:
                link_schedule_ids: list[int] = []

                # Insert unmatched schedules (or retrieve them if they already exist)
                if not state.old_schedules_match and state.unmatched_schedules:
                    # There is some new schedules, insert them
                    for schedule in state.unmatched_schedules:
                        # Check if the schedule already exists
                        existing_schedule_id = self._get_schedule_id(schedule)
                        if existing_schedule_id is not None:
                            link_schedule_ids.append(existing_schedule_id)
                        else:
                            new_schedule_id = self._insert_schedule(schedule)
                            if new_schedule_id is not None:
                                link_schedule_ids.append(new_schedule_id)
                            else:
                                print("Failed to insert new schedule")

                # Add matched schedules that already exists
                if state.matched_schedules:
                    link_schedule_ids.extend(
                        [schedule.schedule_id for schedule in state.matched_schedules]
                    )

                cursor.executemany(
                    "INSERT INTO class_cache_schedule_link (class_cache_id, schedule_id) VALUES (?, ?)",
                    [
                        (state.new_cache_id, schedule_id)
                        for schedule_id in link_schedule_ids
                    ],
                )

    @_lock_method(lock_attr="_lock")
    def remove_class_caches(self, class_ids: list[int] | int) -> int:
        if not isinstance(class_ids, list):
            class_ids = [class_ids]

        cursor = self._get_cache_connection().cursor()
        cursor.execute(
            f"""
            DELETE FROM class_cache
            WHERE class_id IN ({",".join(["?"] * len(class_ids))})
            """,
            class_ids,
        )
        self._get_cache_connection().commit()

        return cursor.rowcount

    @_lock_method(lock_attr="_lock")
    def get_enrollments(self) -> list[Enrollment]:
        cursor = self._get_enrollment_connection().cursor()
        cursor.execute("SELECT enrollment_id, course_code, class_code FROM enrollment")
        rows = cursor.fetchall()
        enrollments = [
            Enrollment(
                enrollment_id=row[0],
                course_code=row[1],
                class_code=row[2],
            )
            for row in rows
        ]
        return enrollments

    @_lock_method(lock_attr="_lock")
    def append_enrollments(self, enrollments: list[Enrollment] | Enrollment) -> int:
        if not isinstance(enrollments, list):
            enrollments = [enrollments]

        cursor = self._get_enrollment_connection().cursor()
        cursor.executemany(
            "INSERT INTO enrollment (course_code, class_code) VALUES (?, ?)",
            [
                (
                    enrollment.course_code,
                    enrollment.class_code,
                )
                for enrollment in enrollments
            ],
        )

        self._get_enrollment_connection().commit()
        return cursor.rowcount

    @_lock_method(lock_attr="_lock")
    def remove_enrollments(self, enrollment_ids: list[int] | int) -> int:
        if not isinstance(enrollment_ids, list):
            enrollment_ids = [enrollment_ids]

        cursor = self._get_enrollment_connection().cursor()
        cursor.execute(
            f"""
            DELETE FROM enrollment
            WHERE enrollment_id IN ({",".join(["?"] * len(enrollment_ids))})
            """,
            enrollment_ids,
        )
        self._get_enrollment_connection().commit()

        return cursor.rowcount

    @_lock_method(lock_attr="_lock")
    def clear_enrollments(self) -> int:
        cursor = self._get_enrollment_connection().cursor()
        cursor.execute("DELETE FROM enrollment")
        self._get_enrollment_connection().commit()
        return cursor.rowcount

    @_lock_method(lock_attr="_lock")
    def execute_raw(self, query: str, parameters: tuple = ()) -> Any:
        cursor = self._get_cache_connection().cursor()
        cursor.execute(query, parameters)
        self._get_cache_connection().commit()
        return cursor

    @_lock_method(lock_attr="_lock")
    def execute_raw_enrollment(self, query: str, parameters: tuple = ()) -> Any:
        cursor = self._get_enrollment_connection().cursor()
        cursor.execute(query, parameters)
        self._get_enrollment_connection().commit()
        return cursor

    def get_lock(self) -> RLock:
        return self._lock

    @classmethod
    def _append_condition(
        cls,
        field: str,
        value: str | list[str],
        conditions: list[str],
        parameters: list[str],
    ) -> None:
        if isinstance(value, str):
            conditions.append(f"{field} = ?")
            parameters.append(value)
        elif isinstance(value, list):
            conditions.append(f"{field} IN ({','.join(['?'] * len(value))})")
            parameters.extend(value)
