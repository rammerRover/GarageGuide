import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values


BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE = "garageguide_app_test"


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    database: str
    user: str
    password: str = field(repr=False)


def load_settings(*, testing: bool = False) -> Settings:
    filename = ".env.test" if testing else ".env"
    values = dotenv_values(BACKEND_DIR / filename)

    def value(key: str, default: str = "") -> str:
        return os.environ.get(key, values.get(key) or default)

    database = value("PGDATABASE", TEST_DATABASE if testing else "garageguide_app")
    if testing and database != TEST_DATABASE:
        raise ValueError(f"Application tests require PGDATABASE={TEST_DATABASE}")
    return Settings(
        host=value("PGHOST", "localhost"),
        port=int(value("PGPORT", "5432")),
        database=database,
        user=value("PGUSER"),
        password=value("PGPASSWORD"),
    )


def get_settings() -> Settings:
    return load_settings()
