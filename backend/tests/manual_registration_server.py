import argparse
import os
import sys
from contextlib import ExitStack, contextmanager
from datetime import date
from pathlib import Path
from unittest.mock import patch


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
import uvicorn

from app import database, service_queries, session_queries, user_queries, vehicle_queries
from app.service_schemas import ServiceCreate
from app.config import get_auth_settings, get_settings, load_auth_settings, load_settings
from app.main import create_app
from database_support import NativeTestDatabase, TestDatabaseSafetyError


@contextmanager
def prepared_test_backend(*, service_links=False):
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
    original_list_vehicles = vehicle_queries.list_vehicles
    original_create_vehicle = vehicle_queries.create_vehicle
    original_get_vehicle = vehicle_queries.get_vehicle
    original_update_vehicle = vehicle_queries.update_vehicle
    original_list_services = service_queries.list_services
    original_create_service = service_queries.create_service
    original_get_service = service_queries.get_service
    original_update_service = service_queries.update_service
    original_remove_service = service_queries.remove_service
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

        def list_reserved_vehicles(settings, *, actor, prepare_response=None):
            native.track_user(actor.user.id, actor.user.email)
            options = {"prepare_response": prepare_response} if prepare_response is not None else {}
            return original_list_vehicles(settings, actor=actor, **options)

        def create_reserved_vehicle(settings, *, actor, vehicle, prepare_response=None):
            native.track_user(actor.user.id, actor.user.email)
            native.reserve_vehicle(actor.user.id, vehicle)
            options = {"prepare_response": prepare_response} if prepare_response is not None else {}
            created = original_create_vehicle(settings, actor=actor, vehicle=vehicle, **options)
            native.track_vehicle(created.id, actor.user.id, vehicle)
            if service_links and actor.user.email == emails[2]:
                prepare_browser_service_links(native, settings, actor, created.id)
            return created

        def get_reserved_vehicle(settings, *, actor, vehicle_id, prepare_response=None):
            native.track_user(actor.user.id, actor.user.email)
            native.require_reserved_vehicle(vehicle_id, actor.user.id)
            options = {"prepare_response": prepare_response} if prepare_response is not None else {}
            return original_get_vehicle(settings, actor=actor, vehicle_id=vehicle_id, **options)

        def update_reserved_vehicle(settings, *, actor, vehicle_id, patch, prepare_response=None):
            native.track_user(actor.user.id, actor.user.email)
            native.require_reserved_vehicle(vehicle_id, actor.user.id)
            options = {"prepare_response": prepare_response} if prepare_response is not None else {}
            return original_update_vehicle(settings, actor=actor, vehicle_id=vehicle_id, patch=patch, **options)

        def service_parent(actor, vehicle_id):
            native.track_user(actor.user.id, actor.user.email)
            if not native.require_reserved_vehicle(vehicle_id, actor.user.id):
                raise vehicle_queries.VehicleNotFoundError()

        def list_reserved_services(settings, *, actor, vehicle_id, prepare_response=None):
            service_parent(actor, vehicle_id)
            return original_list_services(settings, actor=actor, vehicle_id=vehicle_id, prepare_response=prepare_response)

        def create_reserved_service(settings, *, actor, vehicle_id, service, prepare_response=None):
            service_parent(actor, vehicle_id)
            native.reserve_service(vehicle_id, actor.user.id, service)
            created = original_create_service(settings, actor=actor, vehicle_id=vehicle_id, service=service, prepare_response=prepare_response)
            native.track_service(created.id, vehicle_id, actor.user.id, service)
            return created

        def service_identity(actor, vehicle_id, service_id):
            native.track_user(actor.user.id, actor.user.email)
            native.require_reserved_service(service_id, vehicle_id, actor.user.id)

        def get_reserved_service(settings, *, actor, vehicle_id, service_id, prepare_response=None):
            service_identity(actor, vehicle_id, service_id)
            return original_get_service(settings, actor=actor, vehicle_id=vehicle_id, service_id=service_id, prepare_response=prepare_response)

        def update_reserved_service(settings, *, actor, vehicle_id, service_id, patch, prepare_response=None):
            service_identity(actor, vehicle_id, service_id)
            return original_update_service(settings, actor=actor, vehicle_id=vehicle_id, service_id=service_id, patch=patch, prepare_response=prepare_response)

        def remove_reserved_service(settings, *, actor, vehicle_id, service_id, confirmation, prepare_response=None):
            service_identity(actor, vehicle_id, service_id)
            return original_remove_service(settings, actor=actor, vehicle_id=vehicle_id, service_id=service_id, confirmation=confirmation, prepare_response=prepare_response)

        with ExitStack() as patches:
            for owner, name, replacement in (
                (database, "connect_database", native.connect),
                (user_queries, "create_user", create_reserved_user),
                (user_queries, "verify_user_credentials", verify_reserved_user),
                (session_queries, "create_session", create_reserved_session),
                (session_queries, "validate_and_extend_session", extend_reserved_session),
                (session_queries, "revoke_session", revoke_reserved_session),
                (vehicle_queries, "list_vehicles", list_reserved_vehicles),
                (vehicle_queries, "create_vehicle", create_reserved_vehicle),
                (vehicle_queries, "get_vehicle", get_reserved_vehicle),
                (vehicle_queries, "update_vehicle", update_reserved_vehicle),
                (service_queries, "list_services", list_reserved_services),
                (service_queries, "create_service", create_reserved_service),
                (service_queries, "get_service", get_reserved_service),
                (service_queries, "update_service", update_reserved_service),
                (service_queries, "remove_service", remove_reserved_service),
            ):
                patches.enter_context(patch.object(owner, name, replacement))
            application = create_app()
            application.dependency_overrides[get_settings] = lambda: settings
            application.dependency_overrides[get_auth_settings] = lambda: auth_settings
            yield application, emails
    finally:
        native.cleanup()


def prepare_browser_service_links(native, settings, actor, vehicle_id):
    """Explicit test-only setup; never mounted as an HTTP endpoint."""
    for kind in ("part", "completion"):
        service = ServiceCreate(
            service_date=date.today().isoformat(), service_type="inspection",
            description=f"Synthetic {kind}-linked service", notes="Guarded browser fixture",
        )
        # The patched helper reserves and tracks this exact service before setup.
        record = service_queries.create_service(settings, actor=actor, vehicle_id=vehicle_id, service=service)
        if kind == "part":
            name = native.reserve_part_snapshot(record.id, vehicle_id, actor.user.id)
            with native.connect(settings) as connection:
                connection.execute(
                    "INSERT INTO public.service_parts (service_record_id, name, quantity, notes) "
                    "SELECT s.id, %s, %s, %s FROM public.service_records AS s "
                    "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                    "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s RETURNING id",
                    (name, 1, "Guarded browser fixture", record.id, vehicle_id, actor.user.id),
                ).fetchone()
        else:
            name = native.reserve_maintenance_schedule(vehicle_id, actor.user.id)
            with native.connect(settings) as connection:
                schedule_id = connection.execute(
                    "INSERT INTO public.maintenance_schedules (vehicle_id, name, interval_days, baseline_date) "
                    "SELECT id, %s, %s, %s FROM public.vehicles WHERE id = %s AND user_id = %s RETURNING id",
                    (name, 30, date.today(), vehicle_id, actor.user.id),
                ).fetchone()[0]
            native.reserve_maintenance_completion(schedule_id, record.id, vehicle_id, actor.user.id)
            with native.connect(settings) as connection:
                connection.execute(
                    "INSERT INTO public.maintenance_completions (vehicle_id, schedule_id, service_record_id) "
                    "SELECT s.vehicle_id, %s, s.id FROM public.service_records AS s "
                    "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                    "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s RETURNING id",
                    (schedule_id, record.id, vehicle_id, actor.user.id),
                ).fetchone()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the guarded, synthetic-account-only authentication test backend."
    )
    parser.add_argument("--service-links", action="store_true", help="Seed exact linked service fixtures for new vehicles of the third reserved account")
    args = parser.parse_args(argv)
    try:
        with prepared_test_backend(service_links=args.service_links) as (application, emails):
            print("Guarded manual backend: garageguide_app_test only.")
            print("Use only these reserved synthetic email addresses:")
            for email in emails:
                print(email)
            if args.service_links:
                print("Only the third reserved account's new vehicles receive linked service fixtures; the first two start with empty history.")
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
    print("Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
