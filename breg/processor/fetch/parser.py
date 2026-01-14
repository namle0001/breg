from re import Match
from re import search as regex_search
from unicodedata import normalize

from bs4 import BeautifulSoup, Tag

from breg.type.data import (
    ClassCache,
    CourseCache,
    DayBF,
    Enrollment,
    Schedule,
    TimeframeBF,
    WeekBF,
)

_day_map = {
    normalize("NFC", "thứ 2"): 1 << 0,
    normalize("NFC", "thứ 3"): 1 << 1,
    normalize("NFC", "thứ 4"): 1 << 2,
    normalize("NFC", "thứ 5"): 1 << 3,
    normalize("NFC", "thứ 6"): 1 << 4,
    normalize("NFC", "thứ 7"): 1 << 5,
    normalize("NFC", "chủ nhật"): 1 << 6,
}


def parse_enrollment_data(
    raw_data: str,
) -> tuple[list[Enrollment], list[CourseCache], list[ClassCache]]:
    soup = BeautifulSoup(raw_data, "html.parser")
    panels = soup.select("div.panel.panel-default")

    enrollments: list[Enrollment] = []
    course_caches: list[CourseCache] = []
    class_caches: list[ClassCache] = []

    for panel in panels:
        enrollment_id: str = None

        panel_heading_content = (
            panel.select_one("div.panel-heading").select_one("div.row").select("div")
        )
        panel_no = panel_heading_content[0].get_text(strip=True)
        if panel_heading_content[1].select_one("a"):
            enrollment_id_match: Match[str] | None = regex_search(
                r".*\((?P<eid>\d+)\)", panel_heading_content[1].select_one("a")["href"]
            )
            if enrollment_id_match is not None:
                enrollment_id = enrollment_id_match.group("eid")

        title: str = None
        if enrollment_id is not None:
            title = panel_heading_content[1].select_one("a").get_text(strip=True)
        else:
            title = panel_heading_content[1].get_text(strip=True)

        course_code = title.split("-")[0].strip()
        course_name = title.split("-")[1].strip()
        credits = int(panel_heading_content[2].get_text(strip=True)[0])

        # Parse schedule
        panel_body_content = (
            panel.select_one("div.panel-body")
            .select_one("div > div > table")
            .select("tr")
        )

        # len should be 3
        # 0: Header
        # 1: info
        class_cache = parse_class_info(panel_body_content[1])
        class_cache.course_code = course_code
        class_cache.schedules = parse_schedule_table(
            panel_body_content[2].select_one("table")
        )

        enrollments.append(
            Enrollment(
                enrollment_id=enrollment_id,
                course_code=course_code,
                class_code=class_cache.class_code,
            )
        )
        course_caches.append(
            CourseCache(
                course_code=course_code,
                course_name=course_name,
            )
        )
        class_caches.append(class_cache)
    return enrollments, course_caches, class_caches


def parse_course_data(raw_data: str) -> list[CourseCache]:
    soup = BeautifulSoup(raw_data, "html.parser")

    courses: list[CourseCache] = []
    rows = soup.select("table > tr")
    for row in rows:
        if not row.has_attr("id") or not row["id"].startswith("monHoc"):
            continue

        info = row.select("td.item_list")

        course_id: str = regex_search(r"monHoc(?P<sid>\d+)", row["id"]).group("sid")
        order = info[0].get_text(strip=True)
        course_code = info[2].get_text(strip=True)
        course_name = info[3].get_text(strip=True)
        credits = float(info[4].get_text(strip=True))
        courses.append(
            CourseCache(
                course_code=course_code,
                course_name=course_name,
                course_id=course_id,
            )
        )

    return courses


def parse_class_data(raw_data: str) -> list[ClassCache]:
    soup = BeautifulSoup(raw_data, "html.parser")

    classes: list[ClassCache] = []
    rows = soup.select("table.gridTable > tr")
    for row in rows:
        # Seperator row
        if row.select_one("td > hr"):
            continue

        if row.select_one("table"):
            last_class = classes[-1]
            last_class.schedules.extend(parse_schedule_table(row.select_one("table")))
            continue

        classes.append(parse_class_info(row))

    return classes


def _parse_timeframe_str(timeframe_str: str) -> TimeframeBF:
    timeframe_bf = TimeframeBF()
    periods = timeframe_str.split()
    for period in periods:
        if not period.isdigit():
            continue
        period_int = int(period)
        if 1 <= period_int <= 16:
            setattr(timeframe_bf, f"period_{period_int}", 1)
    return timeframe_bf


def _parse_week_str(week_str: str) -> WeekBF:
    week_bf = WeekBF()

    for week, _ in enumerate(week_str):
        if week_str[week] != "-":
            setattr(week_bf, f"week_{week + 1}", 1)

    return week_bf


def parse_schedule_table(table: Tag) -> list[Schedule]:
    schedules = table.select("tr")
    schedule_list: list[Schedule] = []
    for schedule in schedules:
        if schedule.select_one("td.item_list") is None:
            continue
        schedule_info = schedule.select("td.item_list")

        day = schedule_info[0].get_text(strip=True)
        timeframe = schedule_info[1].get_text(strip=True)
        location = schedule_info[2].get_text(strip=True)
        branch = schedule_info[3].get_text(strip=True)
        excersise = schedule_info[4].get_text(strip=True)
        week = schedule_info[5].get_text(strip=True)

        day_bf = DayBF.from_int(_day_map.get(normalize("NFC", day).casefold(), 0))
        timeframe_bf = _parse_timeframe_str(timeframe)
        week_bf = WeekBF.from_week_str(week)
        schedule_list.append(
            Schedule(
                day=day_bf, timeframe=timeframe_bf, week=week_bf, location=location
            )
        )

    return schedule_list


def parse_class_info(row: Tag) -> ClassCache:
    class_cache = ClassCache()
    class_info = row.select("td.item_list")

    class_cache.class_code = class_info[0].get_text(strip=True)
    class_cache.student_no = int(class_info[1].get_text(strip=True).split("/")[0])
    class_cache.student_capacity = int(class_info[1].get_text(strip=True).split("/")[1])
    language = class_info[2].get_text(strip=True)
    lecture_code = class_info[3].get_text(strip=True)
    lecturer = class_info[4].get_text(strip=True)
    excersise_code = class_info[5].get_text(strip=True)
    excersise_teacher = class_info[6].get_text(strip=True)
    lecture_capacity = int(class_info[7].get_text(strip=True))
    if len(class_info) >= 9 and class_info[8].select_one("button"):
        class_cache.class_id = regex_search(
            r".*\(\w*,\s*(?P<cid>\d+),\s*\w*\)",
            class_info[8].select_one("button")["onclick"],
        ).group("cid")

    return class_cache
