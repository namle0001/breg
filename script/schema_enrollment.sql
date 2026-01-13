CREATE TABLE IF NOT EXISTS enrollment (
    enrollment_id INTEGER DEFAULT NULL,
    course_code TEXT NOT NULL,
    class_code TEXT NOT NULL,

    PRIMARY KEY (course_code, class_code)
)