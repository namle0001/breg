CREATE TABLE IF NOT EXISTS enrollment (
    seq_id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER DEFAULT NULL,
    course_code TEXT NOT NULL,
    class_code TEXT NOT NULL,
)