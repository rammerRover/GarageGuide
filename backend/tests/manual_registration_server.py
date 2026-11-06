import argparse
import os
import sys
from contextlib import contextmanager
from pathlib import Path


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
import uvicorn

from app import database, user_queries
from app.config import get_settings, load_settings
from app.main import create_app
from database_support import NativeTestDatabase, TestDatabaseSafetyError


@contextmanager
def prepared_test_backend():
    if os.environ.get("RUN_DB_TESTS") != "1":
        raise TestDatabaseSafetyError("Manual verification requires RUN_DB_TESTS=1")
    settings = load_settings(testing=True)
    original_connect = database.connect_database
    original_create = user_queries.create_user
    native = NativeTestDatabase(settings, original_connect)
    try:
        native.check_schema()
        emails = [native.reserve_email() for _ in range(3)]

        def create_reserved_user(settings, *, email, password_hash):
            if email not in emails:
                raise TestDatabaseSafetyError("Only reserved synthetic accounts are permitted")
            return original_create(settings, email=email, password_hash=password_hash)

        database.connect_database = native.connect
        user_queries.create_user = create_reserved_user
        application = create_app()
        application.dependency_overrides[get_settings] = lambda: settings
        yield application, emails
    finally:
        try:
            native.cleanup()
        finally:
            database.connect_database = original_connect
            user_queries.create_user = original_create


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the guarded, synthetic-account-only registration test backend."
    )
    parser.parse_args(argv)
    try:
        with prepared_test_backend() as (application, emails):
            print("Guarded manual backend: garageguide_app_test only.")
            print("Use only these reserved synthetic email addresses:")
            for email in emails:
                print(email)
            print("Stop with Ctrl+C and wait for the verified-cleanup message.")
            try:
                uvicorn.run(application, host="127.0.0.1", port=8000, access_log=False)
            except KeyboardInterrupt:
                pass
    except (Exception, pytest.fail.Exception):
        print(
            "Manual verification stopped without confirmed cleanup. Check test "
            "configuration and resolve only printed fixture accounts before continuing.",
            file=sys.stderr,
        )
        return 1
    print("Verified cleanup: all reserved synthetic accounts are absent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
