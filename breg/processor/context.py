from dataclasses import dataclass

from breg.config import Environment, Configuration
from breg.core.network import Session
from breg.core.database import Database


@dataclass
class ProcessorContext:
    config: Configuration = None
    env: Environment = None

    session: Session = None
    database: Database = None
