from urllib.parse import urlencode

from breg.core.network.net import ContentType, Session
from breg.config.config import Configuration
from breg.exception.network import NetworkException


class RoundMananger:
    _session: Session
    _config: Configuration

    def __init__(self, session: Session, config: Configuration):
        self._session = session
        self._config = config

    def switch_round(self, round_id: str):
        response = self._session.post(
            path=self._config.TARGET_SWITCH_ROUND_PATH,
            body=urlencode({self._config.ROUND_NAME: round_id}),
            content_type=ContentType.FORM_URLENCODED,
        )

        if response.getcode() >= 400:
            raise NetworkException(
                f"Failed to switch round to '{round_id}'. HTTP {response.getcode()}"
            )

        self._session.additional_data["current_round"] = round_id

    def switch_seed(self, seed_id: str):
        response = self._session.post(
            path=self._config.TARGET_SWITCH_SEED_PATH,
            body=urlencode({self._config.SEED_NAME: seed_id}),
            content_type=ContentType.FORM_URLENCODED,
        )

        if response.getcode() >= 400:
            raise NetworkException(
                f"Failed to switch seed to '{seed_id}'. HTTP {response.getcode()}"
            )

        self._session.additional_data["current_seed"] = seed_id
