from urllib.parse import urlencode

from breg.core.network import Response
from breg.exception.network import (
    NetworkException,
    NetworkSoftFailException,
    UnauthorizedException,
)
from breg.type.api_internal import ClassID, EnrollmentID

from ..base import Processor


class Executor(Processor):
    def enroll(self, class_id_value: ClassID):
        if not isinstance(class_id_value, ClassID):
            raise TypeError("class_id_value must be of type ClassID")

        response = self._context.session.post(
            path=self._context.config.TARGET_REGISTER_PATH,
            body=urlencode(
                {self._context.config.CLASS_ID_NAME: class_id_value}
            ).encode(),
        )
        self._error_check(
            response, f"Failed to register enrollment for class id {class_id_value}"
        )

    def unenroll(self, enrollment_id_value: EnrollmentID):
        if not isinstance(enrollment_id_value, EnrollmentID):
            raise TypeError("enrollment_id_value must be of type EnrollmentID")

        response = self._context.session.post(
            path=self._context.config.TARGET_UNREGISTER_PATH,
            body=urlencode(
                {self._context.config.ENROLLMENT_ID_NAME: enrollment_id_value}
            ).encode(),
        )

        self._error_check(
            response, f"Failed to unenroll enrollment ID {enrollment_id_value}"
        )

    @classmethod
    def _error_check(cls, response: Response, fail_message: str):
        if response.status() == 401:
            raise UnauthorizedException(f"{fail_message}: 401 Unauthorized access")
        if not response.ok():
            raise NetworkException(f"{fail_message}: HTTP {response.status()}")

        try:
            response_data = response.json()
        except Exception as e:
            raise NetworkSoftFailException(
                f"Message from server: {response_data}"
            ) from e
        else:
            if (
                type(response_data) is not dict
                or response_data.get("code") != "success"
            ):
                raise NetworkSoftFailException(f"Message from server: {response_data}")
