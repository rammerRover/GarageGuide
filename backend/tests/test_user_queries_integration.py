import psycopg
import pytest
from pydantic import SecretStr

from app import database
from app.security import validate_and_hash_credentials
from app.user_queries import DuplicateEmailError, create_user, insert_user


pytestmark = pytest.mark.integration


@pytest.fixture
def encoded_hash():
    secret = SecretStr(chr(0x61) * 15)
    return validate_and_hash_credentials(secret, secret)


def test_committed_user_visible_and_sequential_duplicate(native_database, encoded_hash):
    email = native_database.reserve_email()
    row = create_user(native_database.settings, email=email, password_hash=encoded_hash)
    assert row[1] == email
    assert row[0] > 0
    assert row[2].tzinfo is not None
    with database.connect_database(native_database.settings, read_only=True) as connection:
        stored = connection.execute(
            "SELECT id, password_hash FROM public.users WHERE email = %s", (email,)
        ).fetchall()
    one_matching_account = stored == [(row[0], encoded_hash)]
    assert one_matching_account
    with pytest.raises(DuplicateEmailError):
        create_user(native_database.settings, email=email, password_hash=encoded_hash)
    with database.connect_database(native_database.settings, read_only=True) as connection:
        assert connection.execute(
            "SELECT count(*) FROM public.users WHERE email = %s", (email,)
        ).fetchone() == (1,)


def test_failed_transaction_rolls_back_then_recovers(native_database, encoded_hash):
    email = native_database.reserve_email()
    with pytest.raises(psycopg.errors.UniqueViolation):
        with database.connect_database(native_database.settings, read_only=False) as connection:
            insert_user(connection, email, encoded_hash)
            insert_user(connection, email, encoded_hash)
    assert connection.closed
    with database.connect_database(native_database.settings, read_only=True) as reader:
        assert reader.execute(
            "SELECT id FROM public.users WHERE email = %s", (email,)
        ).fetchone() is None
    row = create_user(native_database.settings, email=email, password_hash=encoded_hash)
    assert row[1] == email


def test_cleanup_recovers_id_after_request_failure(native_database, encoded_hash):
    email = native_database.reserve_email()
    with pytest.raises(RuntimeError, match="Synthetic lost response"):
        create_user(native_database.settings, email=email, password_hash=encoded_hash)
        raise RuntimeError("Synthetic lost response")
    native_database.cleanup()
    with database.connect_database(native_database.settings, read_only=True) as connection:
        assert connection.execute(
            "SELECT id FROM public.users WHERE email = %s", (email,)
        ).fetchone() is None


def test_health_transaction_is_read_only_on_native_database(native_database):
    with database.connect_database(native_database.settings, read_only=True) as connection:
        assert connection.execute("SHOW transaction_read_only").fetchone() == ("on",)
