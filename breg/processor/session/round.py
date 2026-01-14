from urllib.parse import urlencode

from bs4 import BeautifulSoup
from re import search as re_search

from breg.core.network.net import ContentType
from breg.exception.network import NetworkException
from breg.type.data import Round, Seed

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

    def get_rounds(self) -> list[Round]:
        response = self._context.session.get(
            path=self._context.config.TARGET_FETCH_ROUNDS_PATH
        )

        soup = BeautifulSoup(response.text(), "html.parser")
        rows = soup.select("#div-DanhSachHocKy  table > tr")

        rounds: list[Round] = []

        for row in rows:
            if row.select_one("th"):
                continue  # Skip header row
            data = row.select("td")

            no = data[0].text.strip()
            round_name = data[1].text.strip()
            round_title = data[2].text.strip()
            start_time = data[3].text.strip()
            end_time = data[4].text.strip()

            round_id = re_search(
                r"w*\s*\(\s*(?P<round_id>\d+)\s*,\s*\w+\s*\)", row["onclick"]
            ).group("round_id")

            rounds.append(
                Round(
                    round_id=round_id,
                    round_name=round_name,
                    round_title=round_title,
                    start_time=start_time,
                    end_time=end_time,
                )
            )
        return rounds

    def get_seeds(self) -> list[Seed]:
        response = self._context.session.post(
            path=self._context.config.TARGET_FETCH_SEEDS_PATH,
            body=urlencode({self._context.config.ROUND_NAME: self.last_round}),
            content_type=ContentType.FORM_URLENCODED,
        )

        soup = BeautifulSoup(response.text(), "html.parser")
        rows = soup.select("table#tblDotDK > tr")

        seeds: list[Seed] = []

        for row in rows:
            if row.select_one("th"):
                continue  # Skip header row
            data = row.select("td")

            seed_title = data[1].text.strip()

            seed_id = re_search(r"[A-Za-z]+(?P<seed_id>\d+)", row["id"]).group(
                "seed_id"
            )

            seeds.append(Seed(seed_id=seed_id, seed_title=seed_title))
        return seeds
