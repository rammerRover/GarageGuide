from uuid import uuid4

import psycopg
import pytest

from app.config import TEST_DATABASE


class TestDatabaseSafetyError(RuntimeError):
    __test__ = False


class NativeTestDatabase:
    def __init__(self, settings, connect):
        self.settings = settings
        self._connect = connect
        self._emails = set()

    def connect(self, settings, *, read_only=False):
        if settings.database != TEST_DATABASE:
            raise TestDatabaseSafetyError("Native tests require garageguide_app_test")
        try:
            connection = self._connect(settings, read_only=read_only)
        except psycopg.Error:
            pytest.fail("Prepared native test database could not be opened", pytrace=False)
        try:
            actual = connection.execute("SELECT current_database()").fetchone()
            if actual != (TEST_DATABASE,):
                raise TestDatabaseSafetyError("Connected database must be garageguide_app_test")
        except psycopg.Error:
            connection.close()
            pytest.fail("Actual native test database could not be verified; no writes allowed", pytrace=False)
        except BaseException:
            connection.close()
            raise
        return connection

    def check_schema(self):
        try:
            with self.connect(self.settings, read_only=True) as connection:
                ready = connection.execute(
                    "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_constraint "
                    "WHERE conrelid = to_regclass(%s) AND conname = %s "
                    "AND contype = 'u' AND pg_get_constraintdef(oid) = 'UNIQUE (email)')",
                    ("public.users", "users_email_key"),
                ).fetchone()
                if ready != (True,):
                    pytest.fail("Prepared users email constraint is required; schema was not changed", pytrace=False)
                connection.execute(
                    "SELECT id, email, password_hash, created_at FROM public.users WHERE FALSE"
                )
        except psycopg.Error:
            pytest.fail("Prepared users schema could not be verified; schema was not changed", pytrace=False)

    def reserve_email(self):
        email = f"gg-reg-{uuid4().hex}@example.com"
        with self.connect(self.settings, read_only=True) as connection:
            exists = connection.execute(
                "SELECT id FROM public.users WHERE email = %s", (email,)
            ).fetchone()
        if exists is not None:
            pytest.fail("Synthetic fixture collision; existing record was not claimed", pytrace=False)
        self._emails.add(email)
        return email

    def cleanup(self):
        if not self._emails:
            return
        try:
            with self.connect(self.settings, read_only=False) as connection:
                for email in self._emails:
                    row = connection.execute(
                        "SELECT id FROM public.users WHERE email = %s", (email,)
                    ).fetchone()
                    if row is not None:
                        connection.execute(
                            "DELETE FROM public.users WHERE id = %s AND email = %s",
                            (row[0], email),
                        )
            with self.connect(self.settings, read_only=True) as connection:
                remaining = connection.execute(
                    "SELECT id FROM public.users WHERE email = ANY(%s)",
                    (list(self._emails),),
                ).fetchall()
                if remaining:
                    pytest.fail("Synthetic cleanup verification failed; stop native testing", pytrace=False)
        except psycopg.Error:
            pytest.fail("Synthetic cleanup failed; stop native testing and resolve tracked fixtures", pytrace=False)
        self._emails.clear()
