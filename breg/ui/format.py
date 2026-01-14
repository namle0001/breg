from typing import Literal
from tabulate import tabulate

from breg.type.data import ClassCache, Round
from shutil import get_terminal_size


def format_classes_schedules(
    class_caches: list[ClassCache], tablefmt: str = "simple_grid"
) -> str:
    """Format class schedules into a table string.

    Args:
        class_caches (list[ClassCache]): List of ClassCache objects.

    Returns:
        str: Formatted table string of class schedules.
    """

    headers = ["", "", "Period", "Day", "Location", "Weeks"]
    table_data = []

    max_week_end = 0
    max_period_end = 0
    for cache in class_caches:
        for schedule in cache.schedules:
            week_list = schedule.week.list()
            period_list = schedule.timeframe.list()
            week_end = max(i + 1 for i, v in enumerate(week_list) if v)
            period_end = max(i + 1 for i, v in enumerate(period_list) if v)
            if week_end > max_week_end:
                max_week_end = week_end
            if period_end > max_period_end:
                max_period_end = period_end

    for cache in class_caches:
        class_info = [
            cache.course_code,
            cache.class_code,
        ]

        schedules = []
        for schedule in cache.schedules:
            timeframe = []
            for p in schedule.timeframe.list():
                if p:
                    timeframe.append(str(len(timeframe) + 1))
                else:
                    timeframe.append("-")

            week = []
            for w in schedule.week.list():
                if w:
                    week.append(str((len(week) + 1) % 10))
                else:
                    week.append("-")

            day = None
            for d, v in schedule.day.dict().items():
                if v:
                    day = d
                    break

            while len(week) > max_week_end and week[-1] == "-":
                week.pop()
            while len(timeframe) > max_period_end and timeframe[-1] == "-":
                timeframe.pop()

            schedules.append(
                [
                    "",
                    "",
                    " ".join(timeframe),
                    day.capitalize() if day else "N/A",
                    schedule.location,
                    "".join(week),
                ]
            )

        table_data.append(class_info)
        table_data.extend(schedules)

    return tabulate(table_data, headers=headers, tablefmt=tablefmt)


def format_rounds(
    rounds: list[Round],
    tablefmt: str = "simple_grid",
    limit: int = 10,
    sort: Literal["asc", "desc"] = "asc",
) -> str:
    """Format rounds into a table string.

    Args:
        rounds (list[Round]): List of Round objects.

    Returns:
        str: Formatted table string of rounds.
    """

    headers = ["Round Name", "Round Title", "Start Time", "End Time"]
    table_data = []

    if limit > 0 and len(rounds) > limit:
        rounds = rounds[:limit]

    it = rounds if sort == "desc" else reversed(rounds)
    for r in it:
        table_data.append(
            [
                r.round_id,
                r.round_name,
                r.round_title,
                r.start_time,
                r.end_time,
            ]
        )

    maxcolwidths = [
        None,
        None,
        min(get_terminal_size().columns - 10 - (20 + 20 + 20), 60),
        None,
        None,
    ]

    return tabulate(
        table_data, headers=headers, tablefmt=tablefmt, maxcolwidths=maxcolwidths
    )


def format_seeds(seeds: list[Round], tablefmt: str = "simple_grid") -> str:
    """Format seeds into a table string.

    Args:
        seeds (list[Seed]): List of Seed objects.

    Returns:
        str: Formatted table string of seeds.
    """

    headers = ["Seed ID", "Seed Title"]
    table_data = []

    for s in seeds:
        table_data.append(
            [
                s.seed_id,
                s.seed_title,
            ]
        )

    maxcolwidths = [None, 80]

    return tabulate(
        table_data, headers=headers, tablefmt=tablefmt, maxcolwidths=maxcolwidths
    )
