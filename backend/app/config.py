import ipaddress
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

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


LOCAL_FRONTEND_ORIGINS = (
    "http://127.0.0.1:5173", "http://127.0.0.1:4173",
)
LOCAL_API_ORIGIN = "http://127.0.0.1:8000"


class AuthConfigurationError(ValueError):
    def __init__(self):
        super().__init__("Authentication configuration unavailable.")


def is_loopback_host(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host == "localhost"


def _origin_is_valid(origin: str, *, https_only: bool = False) -> bool:
    if not isinstance(origin, str) or not origin.isascii():
        return False
    if any(character.isspace() for character in origin) or "\\" in origin:
        return False
    try:
        parsed = urlsplit(origin)
        host = parsed.hostname
        port = parsed.port
        if (
            parsed.scheme not in (("https",) if https_only else ("http", "https"))
            or not host or parsed.username is not None or parsed.password is not None
            or parsed.path or parsed.query or parsed.fragment
            or origin != f"{parsed.scheme}://{parsed.netloc}"
            or parsed.netloc.endswith(":") or (port is not None and port == 0)
        ):
            return False
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if len(host) > 253 or any(
                re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) is None
                for label in host.split(".")
            ):
                return False
        return parsed.netloc == parsed.netloc.lower()
    except ValueError:
        return False


@dataclass(frozen=True)
class AuthSettings:
    environment: str
    cookie_secure: bool
    api_origin: str
    frontend_origin: str = ""

    def __post_init__(self):
        if (
            self.environment not in ("development", "testing", "production")
            or type(self.cookie_secure) is not bool
        ):
            raise AuthConfigurationError()
        if self.environment == "production":
            if (
                not self.cookie_secure
                or not _origin_is_valid(self.api_origin, https_only=True)
                or not _origin_is_valid(self.frontend_origin, https_only=True)
                or self.api_origin != self.frontend_origin
            ):
                raise AuthConfigurationError()
        elif self.api_origin != LOCAL_API_ORIGIN or self.frontend_origin:
            raise AuthConfigurationError()

    @property
    def trusted_frontend_origins(self) -> tuple[str, ...]:
        if self.environment == "production":
            return (self.frontend_origin,)
        return LOCAL_FRONTEND_ORIGINS


def load_auth_settings(*, testing: bool = False) -> AuthSettings:
    filename = ".env.test" if testing else ".env"
    values = dotenv_values(BACKEND_DIR / filename)

    def value(key: str) -> str:
        return os.environ.get(key, values.get(key) or "")

    secure = value("AUTH_COOKIE_SECURE")
    environment = value("AUTH_ENVIRONMENT")
    if secure not in ("true", "false") or (testing and environment != "testing"):
        raise AuthConfigurationError()
    return AuthSettings(
        environment=environment,
        cookie_secure=secure == "true",
        api_origin=value("AUTH_API_ORIGIN"),
        frontend_origin=value("AUTH_FRONTEND_ORIGIN"),
    )


def get_auth_settings() -> AuthSettings:
    return load_auth_settings()
