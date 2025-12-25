CREATE TABLE class_cache (
    timestamp TIMESTAMP NOT NULL,
    course_code TEXT NOT NULL,
    class_code TEXT NOT NULL,
    student_no INTEGER NOT NULL,
    student_capacity INTEGER NOT NULL,
    class_id TEXT DEFAULT NULL,

    PRIMARY KEY (timestamp, course_code, class_code),
);

CREATE TABLE schedule (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    day INTEGER NOT NULL,
    timeframe INTEGER NOT NULL,
    week INTEGER NOT NULL,
    location TEXT,
);

CREATE TABLE class_cache_schedule_link (
    timestamp TIMESTAMP NOT NULL,
    course_code TEXT NOT NULL,
    class_code TEXT NOT NULL,
    schedule_id INTEGER NOT NULL,

    PRIMARY KEY (timestamp, course_code, class_code, schedule_id),
    FOREIGN KEY (timestamp, course_code, class_code) REFERENCES cache(timestamp, course_code, class_code),
    FOREIGN KEY (schedule_id) REFERENCES schedule(schedule_id)
);

CREATE TABLE course_cache (
    timestamp TIMESTAMP NOT NULL,
    course_code TEXT NOT NULL,
    course_name TEXT NOT NULL,
    course_id TEXT DEFAULT NULL,

    PRIMARY KEY (timestamp, course_code),
)