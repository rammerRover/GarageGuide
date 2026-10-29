import pytest
from fastapi.testclient import TestClient

from app.config import get_settings, load_settings
from app.main import create_app


@pytest.fixture
def test_settings():
    # Fail before any connection if environment variables target another database.
    return load_settings(testing=True)


@pytest.fixture
def client(test_settings):
    application = create_app()
    application.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(application) as test_client:
        yield test_client
