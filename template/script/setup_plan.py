import re
from functools import reduce


def main(
    course_code_patterns: list[str] | str = None,
    class_code_patterns: list[str] | str = None,
    solution_count: int = 100,
) -> None:
    """Set up the planning environment.

    Args:
        course_code_patterns (list[str] | str, optional): Course code patterns to filter classes. Defaults to None.
        class_code_patterns (list[str] | str, optional): Class code patterns to filter classes. Defaults to None.
        solution_count (int, optional): Number of solutions wanted. Defaults to 100.
    """
    if isinstance(course_code_patterns, str):
        course_code_patterns = [course_code_patterns]
    if isinstance(class_code_patterns, str):
        class_code_patterns = [class_code_patterns]
    print("Setting up planning environment...")
    print(f"Course code patterns: {course_code_patterns}")
    print(f"Class code patterns: {class_code_patterns}")

    classes = cache().get_all_complete_classes()
    filtered_classes = []
    matched_course_codes = set()
    matched_class_codes = set()
    course_classes_count: dict[str, int] = {}

    for cl in classes:
        course_matched = False
        class_matched = False

        if course_code_patterns:
            for pattern in course_code_patterns:
                if re.match(pattern, cl.course_code):
                    course_matched = True
                    break
        else:
            course_matched = True

        if class_code_patterns:
            for pattern in class_code_patterns:
                if re.match(pattern, cl.class_code):
                    class_matched = True
                    break
        else:
            class_matched = True

        if course_matched and class_matched:
            filtered_classes.append(cl)
            course_classes_count[cl.course_code] = (
                course_classes_count.get(cl.course_code, 0) + 1
            )
            matched_course_codes.add(cl.course_code)
            matched_class_codes.add(cl.class_code)

    plan().setup(filtered_classes, solution_count)

    print(f"Matched course codes: {matched_course_codes}")
    print(f"Matched class codes: {matched_class_codes}")
    print(
        f"Total classes after filtering: {len(filtered_classes)} ({', '.join([str(v) for v in course_classes_count.values()])})"
    )
    print(
        f"Combinations: {reduce(lambda x, y: x * y, course_classes_count.values(), 1)}"
    )
