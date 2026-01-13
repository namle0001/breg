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
)