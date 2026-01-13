from urllib.parse import urlencode

from breg.core.network import ContentType, Response
from breg.exception.network import NetworkException, UnauthorizedException
from breg.type.data import (
    ClassCache,
    CourseCache,
    Enrollment,
)

from ..base import Processor

from .parser import (
    parse_class_data,
    parse_course_data,
    parse_enrollment_data,
)


class Fetcher(Processor):
    def fetch_enrollment_data(
        self,
    ) -> tuple[list[Enrollment], list[CourseCache], list[ClassCache]]:
        response = self._context.session.post(
            path=self._context.config.TARGET_FETCH_ENROLLMENTS_PATH,
            body=b"",
        )

        self._check_net_error(response, "Failed to fetch enrollment data")
        response_data = response.text()

        return parse_enrollment_data(response_data)

    def fetch_course_data(self, search_string: str) -> list[CourseCache]:
        response = self._context.session.post(
            path=self._context.config.TARGET_FETCH_COURSES_PATH,
            body=f"{self._context.config.COURSE_CODE_NAME}={search_string}".encode(),
            content_type=ContentType.FORM_URLENCODED,
        )

        self._check_net_error(response, "Failed to fetch course data")
        response_data = response.text()

        return parse_course_data(response_data)

    def fetch_class_data(self, course_id: str) -> list[ClassCache]:
        response = self._context.session.post(
            path=self._context.config.TARGET_FETCH_CLASSES_PATH,
            body=urlencode({self._context.config.COURSE_ID_NAME: course_id}).encode(),
            content_type=ContentType.FORM_URLENCODED,
        )

        self._check_net_error(response, "Failed to fetch class data")
        response_data = response.text()

        return parse_class_data(response_data)

    @classmethod
    def _check_net_error(cls, response: Response, fail_message) -> None:
        if response.status() == 401:
            raise UnauthorizedException(f"{fail_message}: 401 Unauthorized access")

        if not response.ok():
            raise NetworkException(f"{fail_message}: HTTP {response.status()}")
