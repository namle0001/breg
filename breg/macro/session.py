"""Session management macros."""

from dataclasses import dataclass, fields
from typing import TypedDict, get_type_hints

from breg.config.config import HTTPConfiguration
from breg.core.network import Session
from breg.processor.session.round import RoundMananger
from breg.type.data import Round

from .base import Macro


class SessionMacro(Macro):
    """Macro for managing session data like JSESSIONID, round, and seed."""

    _SESSION_FILE = ".sess"

    @dataclass
    class SessionData:
        JSESSIONID: str = None
        ROUND: str = None
        SEED: str = None

        def unparse(self) -> str:
            lines = []
            for field in fields(self):
                value = getattr(self, field.name)
                if value is not None:
                    lines.append(f"{field.name}={value}")
                else:
                    lines.append(f"{field.name}=")
            return "\n".join(lines)

        @classmethod
        def parse(cls, data: str) -> "SessionMacro.SessionData":
            session_data = cls()

            for line in data.splitlines():
                if line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                if hasattr(session_data, key):
                    setattr(session_data, key, value if value != "" else None)
            return session_data

    class SessionDataDict(TypedDict):
        JSESSIONID: str
        ROUND: str
        SEED: str

    def _save(self, data: SessionDataDict) -> None:
        old_data = self._load()
        for key, value in data.items():
            if hasattr(old_data, key):
                setattr(old_data, key, value)

        with self._runtime_context.project_fs().open(
            self._SESSION_FILE, mode="w"
        ) as session_file:
            session_file.write(old_data.unparse())

    def save_jsession(self) -> None:
        """Saves the current JSESSIONID to the session file."""
        self._save(
            {
                "JSESSIONID": self._runtime_context.processor_context().session.get_cookie(
                    "JSESSIONID"
                )
            }
        )

    def save_round_and_seed(self) -> None:
        """Saves the current round and seed to the session file."""
        round_mananger = self._runtime_context.get_processor(RoundMananger)
        self._save(
            {
                "ROUND": round_mananger.last_round,
                "SEED": round_mananger.last_seed,
            }
        )

    def _load(self) -> "SessionMacro.SessionData":
        with self._runtime_context.project_fs().open(
            self._SESSION_FILE, mode="r"
        ) as session_file:
            session_data = self.SessionData.parse(session_file.read())
        return session_data

    def restore_jsession(self) -> None:
        """Restores the JSESSIONID from the session file."""
        session_data = self._load()
        if session_data.JSESSIONID is None:
            return

        processor_context = self._runtime_context.processor_context()
        if processor_context.session is None:
            self._runtime_context.initialize_cores(
                net_session=Session(
                    HTTPConfiguration.from_target(self._runtime_context.config()),
                    session_data.JSESSIONID,
                )
            )
        self._runtime_context.processor_context().session.set_cookie(
            "JSESSIONID", session_data.JSESSIONID
        )

    def restore_round_and_seed(self) -> None:
        """Restores the round and seed from the session file."""
        session_data = self._load()
        round_mananger = self._runtime_context.get_processor(RoundMananger)

        # Attempt to switch round, seed
        if session_data.ROUND is not None:
            round_mananger.switch_round(session_data.ROUND)
            if session_data.SEED is not None:
                round_mananger.switch_seed(session_data.SEED)

    def switch_round(self, round_id: str) -> None:
        """Switches to a specific round.

        Args:
            round_id (str): Round id number.
        """
        round_mananger = self._runtime_context.get_processor(RoundMananger)
        round_mananger.switch_round(round_id)

    def switch_seed(self, seed_id: str) -> None:
        """Switches to a specific seed.

        Args:
            seed_id (str): Seed id number.
        """
        round_mananger = self._runtime_context.get_processor(RoundMananger)
        round_mananger.switch_seed(seed_id)

    def get_rounds(self) -> list[Round]:
        """Fetches the list of rounds.

        Returns:
            list[Round]: List of Round objects.
        """
        round_mananger = self._runtime_context.get_processor(RoundMananger)
        return round_mananger.get_rounds()

    def get_seeds(self) -> list[Round]:
        """Fetches the list of seeds.

        Returns:
            list[Seed]: List of Seed objects.
        """
        round_mananger = self._runtime_context.get_processor(RoundMananger)
        return round_mananger.get_seeds()
