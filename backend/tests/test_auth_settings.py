import pytest

from app import config
from app.config import AuthConfigurationError, AuthSettings, load_auth_settings


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture
def auth_environment(monkeypatch):
    for key in ("AUTH_ENVIRONMENT", "AUTH_COOKIE_SECURE", "AUTH_API_ORIGIN", "AUTH_FRONTEND_ORIGIN"):
        monkeypatch.delenv(key, raising=False)
    values = {
        "AUTH_ENVIRONMENT": "testing", "AUTH_COOKIE_SECURE": "false",
        "AUTH_API_ORIGIN": "http://127.0.0.1:8000", "AUTH_FRONTEND_ORIGIN": "",
    }
    files = []

    def dotenv(path):
        files.append(path.name)
        return values

    monkeypatch.setattr(config, "dotenv_values", dotenv)
    return values, files


def test_test_loader_reads_only_test_file_and_explicit_settings(auth_environment):
    _, files = auth_environment
    settings = load_auth_settings(testing=True)
    assert files == [".env.test"]
    assert settings.environment == "testing" and settings.cookie_secure is False
    assert settings.trusted_frontend_origins == (
        "http://127.0.0.1:5173", "http://127.0.0.1:4173",
    )


def test_environment_override_is_validated(auth_environment, monkeypatch):
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    assert load_auth_settings(testing=True).cookie_secure is True
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "untrusted-private-value")
    with pytest.raises(AuthConfigurationError) as caught:
        load_auth_settings(testing=True)
    assert str(caught.value) == "Authentication configuration unavailable."


@pytest.mark.parametrize("key", ["AUTH_ENVIRONMENT", "AUTH_COOKIE_SECURE", "AUTH_API_ORIGIN"])
def test_missing_settings_fail_closed_without_implicit_development(auth_environment, key):
    values, _ = auth_environment
    del values[key]
    with pytest.raises(AuthConfigurationError):
        load_auth_settings(testing=True)


@pytest.mark.parametrize("value", ["False", "0", "1", "yes", "", "false "])
def test_secure_flag_is_a_strict_boolean(auth_environment, value):
    values, _ = auth_environment
    values["AUTH_COOKIE_SECURE"] = value
    with pytest.raises(AuthConfigurationError):
        load_auth_settings(testing=True)


def test_test_loader_rejects_non_test_environment(auth_environment):
    values, _ = auth_environment
    values["AUTH_ENVIRONMENT"] = "development"
    with pytest.raises(AuthConfigurationError):
        load_auth_settings(testing=True)


@pytest.mark.parametrize("environment", ["development", "testing"])
@pytest.mark.parametrize("api_origin", ["http://0.0.0.0:8000", "http://192.0.2.1:8000", "https://garage.example"])
def test_insecure_nonloopback_configuration_is_rejected(environment, api_origin):
    with pytest.raises(AuthConfigurationError):
        AuthSettings(environment, False, api_origin)


@pytest.mark.parametrize("secure", [False, "false", 0, None])
def test_production_requires_true_boolean_secure_cookie(secure):
    with pytest.raises(AuthConfigurationError):
        AuthSettings("production", secure, "https://garage.example", "https://garage.example")


@pytest.mark.parametrize("origin", [
    "", "null", "http://garage.example", "https://garage.example/",
    "https://garage.example/path", "https://garage.example?query",
    "https://garage.example#fragment", "https://user:private@garage.example",
    "https://garage.example:70000", "https://garage.example:",
    "https://garage.example:0", "https://garage.example\\untrusted",
    " https://garage.example", "https://garage.example\n", "https://*.example",
    "https://[invalid]", "https://garage.example,https://other.example",
    "https://-invalid.example", "https://GARAGE.example", "https://garag\u00e9.example",
])
def test_production_origins_are_strict_canonical_https(origin):
    with pytest.raises(AuthConfigurationError) as caught:
        AuthSettings("production", True, origin, origin)
    assert str(caught.value) == "Authentication configuration unavailable."


def test_production_requires_same_origin_frontend_and_api():
    with pytest.raises(AuthConfigurationError):
        AuthSettings("production", True, "https://api.example", "https://garage.example")
    settings = AuthSettings("production", True, "https://garage.example", "https://garage.example")
    assert settings.trusted_frontend_origins == ("https://garage.example",)


def test_local_modes_cannot_expand_trusted_frontends():
    with pytest.raises(AuthConfigurationError):
        AuthSettings("development", False, "http://127.0.0.1:8000", "http://other.example")
    with pytest.raises(AuthConfigurationError):
        AuthSettings("unknown", False, "http://127.0.0.1:8000")
