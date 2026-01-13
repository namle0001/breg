from urllib.parse import urlencode

from breg.core.network.net import ContentType
from breg.exception.network import NetworkException

from ..base import Processor


class RoundMananger(Processor):
    last_round: str
    last_seed: str

    def __init__(self, context=None):
        super().__init__(context)

        self.last_round = None
        self.last_seed = None

    def switch_round(self, round_id: str):
        response = self._context.session.post(
            path=self._context.config.TARGET_SWITCH_ROUND_PATH,
            body=urlencode({self._context.config.ROUND_NAME: round_id}),
            content_type=ContentType.FORM_URLENCODED,
        )

        if not response.ok():
            raise NetworkException(
                f"Failed to switch round to '{round_id}'. HTTP {response.status()}"
            )

        self.last_round = round_id

        self._context.session.additional_data["current_round"] = round_id

    def switch_seed(self, seed_id: str):
        response = self._context.session.post(
            path=self._context.config.TARGET_SWITCH_SEED_PATH,
            body=urlencode({self._context.config.SEED_NAME: seed_id}),
            content_type=ContentType.FORM_URLENCODED,
        )

        if not response.ok():
            raise NetworkException(
                f"Failed to switch seed to '{seed_id}'. HTTP {response.status()}"
            )

        self.last_seed = seed_id

        self._context.session.additional_data["current_seed"] = seed_id
