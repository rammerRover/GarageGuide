import argparse
import os
import sys
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import patch


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
import uvicorn

from app import database, session_queries, user_queries
from app.config import get_auth_settings, get_settings, load_auth_settings, load_settings
from app.main import create_app
from database_support import NativeTestDatabase, TestDatabaseSafetyError


@contextmanager
def prepared_test_backend():
    if os.environ.get("RUN_DB_TESTS") != "1":
        raise TestDatabaseSafetyError("Manual verification requires RUN_DB_TESTS=1")
    settings = load_settings(testing=True)
    auth_settings = load_auth_settings(testing=True)
    original_connect = database.connect_database
    original_create = user_queries.create_user
    original_verify = user_queries.verify_user_credentials
    original_issue = session_queries.create_session
    original_extend = session_queries.validate_and_extend_session
    original_revoke = session_queries.revoke_session
    native = NativeTestDatabase(settings, original_connect)
    try:
        native.check_schema()
        emails = [native.reserve_email() for _ in range(3)]

        def create_reserved_user(settings, *, email, password_hash):
            if email not in emails:
                raise TestDatabaseSafetyError("Only reserved synthetic accounts are permitted")
            return original_create(settings, email=email, password_hash=password_hash)

        def verify_reserved_user(settings, credentials):
            if credentials.email not in emails:
                raise TestDatabaseSafetyError("Only reserved synthetic accounts are permitted")
            return original_verify(settings, credentials)

        def create_reserved_session(settings, *, user, presented_token=None, prepare_response=None):
            native.track_user(user.id, user.email)
            native.require_reserved_session(presented_token)
            issued = original_issue(
                settings, user=user, presented_token=presented_token, prepare_response=prepare_response
            )
            native.track_session(issued.session.session_id, user.id)
            return issued

        def extend_reserved_session(settings, token):
            native.require_reserved_session(token)
            return original_extend(settings, token)

        def revoke_reserved_session(settings, token):
            native.require_reserved_session(token)
            return original_revoke(settings, token)

        with ExitStack() as patches:
            for owner, name, replacement in (
                (database, "connect_database", native.connect),
                (user_queries, "create_user", create_reserved_user),
                (user_queries, "verify_user_credentials", verify_reserved_user),
                (session_queries, "create_session", create_reserved_session),
                (session_queries, "validate_and_extend_session", extend_reserved_session),
                (session_queries, "revoke_session", revoke_reserved_session),
            ):
                patches.enter_context(patch.object(owner, name, replacement))
            application = create_app()
            application.dependency_overrides[get_settings] = lambda: settings
            application.dependency_overrides[get_auth_settings] = lambda: auth_settings
            yield application, emails
    finally:
        native.cleanup()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the guarded, synthetic-account-only authentication test backend."
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
    print("Verified cleanup: all reserved synthetic accounts and sessions are absent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
