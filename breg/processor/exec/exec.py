import json
from http.client import HTTPResponse
from urllib.parse import urlencode

from breg.config.config import Configuration
from breg.core.network.net import Session
from breg.exception.network import (
    NetworkException,
    NetworkSoftFailException,
    UnauthorizedException,
)
from breg.type.api_internal import ClassCode, EnrollmentID


class Executor:
    _session: Session
    _config: Configuration

    def __init__(self, session: Session, config: Configuration) -> None:
        self._session = session
        self._config = config

    def register(self, class_code_value: ClassCode):
        if not isinstance(class_code_value, ClassCode):
            raise TypeError("class_code_value must be of type ClassCode")

        response = self._session.post(
            path=self._config.TARGET_REGISTER_PATH,
            body=urlencode({self._config.CLASS_ID_NAME: class_code_value}).encode(),
        )
        self._error_check(
            response, f"Failed to register enrollment for class code {class_code_value}"
        )

    def unregister(self, enrollment_id_value: EnrollmentID):
        if not isinstance(enrollment_id_value, EnrollmentID):
            raise TypeError("enrollment_id_value must be of type EnrollmentID")

        response = self._session.post(
            path=self._config.TARGET_UNREGISTER_PATH,
            body=urlencode(
                {self._config.ENROLLMENT_ID_NAME: enrollment_id_value}
            ).encode(),
        )

        self._error_check(
            response, f"Failed to unregister enrollment ID {enrollment_id_value}"
        )

    def _error_check(self, response: HTTPResponse, fail_message: str):
        if response.getcode() == 401:
            raise UnauthorizedException(f"{fail_message}: 401 Unauthorized access")

        if response.getcode() != 200:
            raise NetworkException(f"{fail_message}: HTTP {response.getcode()}")

        try:
            response_data = response.read().decode()
            if json.loads(response_data).get("code") != "success":
                raise NetworkSoftFailException(f"Message from server: {response_data}")

        except json.JSONDecodeError as e:
            raise NetworkSoftFailException(
                f"Message from server: {response_data}"
            ) from e
