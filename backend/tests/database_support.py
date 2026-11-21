from uuid import uuid4

import psycopg
import pytest

from app.config import TEST_DATABASE
from app.security import hash_session_token


VEHICLE_FIELDS = ("year", "make", "model", "engine", "vehicle_type", "mileage", "operating_hours")
VEHICLE_MATCH = " AND ".join(f"{field} IS NOT DISTINCT FROM %s" for field in VEHICLE_FIELDS)
SERVICE_FIELDS = ("service_date", "service_type", "description", "mileage", "operating_hours", "cost", "notes")
SERVICE_MATCH = " AND ".join(f"s.{field} IS NOT DISTINCT FROM %s" for field in SERVICE_FIELDS)


class TestDatabaseSafetyError(RuntimeError):
    __test__ = False


class NativeTestDatabase:
    def __init__(self, settings, connect):
        self.settings = settings
        self._connect = connect
        self._emails = set()
        self._users = {}
        self._sessions = {}
        self._vehicle_reservations = set()
        self._vehicles = {}
        self._service_reservations = set()
        self._services = {}
        self._part_reservations = set()
        self._schedule_reservations = set()
        self._completion_reservations = set()
        self._parts = {}
        self._catalog_reservations = set()
        self._catalog_parts = {}
        self._schedules = {}
        self._completions = {}
        self.cleanup_verified = False
        self.cleanup_counts = (0, 0)
        self.cleanup_vehicle_count = 0
        self.cleanup_service_count = 0
        self.cleanup_link_counts = (0, 0, 0)
        self.cleanup_catalog_count = 0
        self.browser_server_running = False

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
                self._check_session_schema(connection)
                connection.execute(
                    "SELECT id, user_id, year, make, model, engine, vehicle_type, mileage, "
                    "operating_hours, readings_updated_at, created_at FROM public.vehicles WHERE FALSE"
                )
                connection.execute(
                    "SELECT id, vehicle_id, service_date, service_type, description, mileage, "
                    "operating_hours, cost, notes, created_at FROM public.service_records WHERE FALSE"
                )
                self._check_linked_schema(connection)
                self._check_catalog_schema(connection)
        except psycopg.Error:
            pytest.fail("Prepared users/session/vehicle/service schema could not be verified; schema was not changed", pytrace=False)

    def _check_session_schema(self, connection):
        connection.execute(
            "SELECT id, user_id, token_hash, created_at, expires_at, revoked_at "
            "FROM public.user_sessions WHERE FALSE"
        )
        constraints = connection.execute(
            "SELECT contype, pg_get_constraintdef(oid) FROM pg_catalog.pg_constraint "
            "WHERE conrelid = to_regclass(%s)", ("public.user_sessions",),
        ).fetchall()
        required = {
            ("p", "PRIMARY KEY (id)"), ("u", "UNIQUE (token_hash)"),
            ("f", "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"),
            ("c", "CHECK ((expires_at > created_at))"),
        }
        if not required.issubset(set(constraints)):
            pytest.fail("Prepared session constraints are required; schema was not changed", pytrace=False)

    def _check_linked_schema(self, connection):
        required = {
            "public.service_parts": {
                ("FOREIGN KEY (service_record_id) REFERENCES service_records(id) ON DELETE CASCADE", False),
            },
            "public.maintenance_completions": {
                ("FOREIGN KEY (service_record_id, vehicle_id) REFERENCES service_records(id, vehicle_id) ON DELETE CASCADE", False),
                ("FOREIGN KEY (schedule_id, vehicle_id) REFERENCES maintenance_schedules(id, vehicle_id) ON DELETE CASCADE", False),
            },
        }
        for table, constraints in required.items():
            rows = connection.execute(
                "SELECT pg_get_constraintdef(oid), condeferrable FROM pg_catalog.pg_constraint "
                "WHERE conrelid = to_regclass(%s) AND contype = 'f'", (table,),
            ).fetchall()
            if not constraints.issubset(set(rows)):
                pytest.fail("Prepared linked-record foreign keys are required; schema was not changed", pytrace=False)

    def reserve_email(self):
        email = f"gg-reg-{uuid4().hex}@example.com"
        with self.connect(self.settings, read_only=True) as connection:
            exists = connection.execute(
                "SELECT id FROM public.users WHERE email = %s", (email,)
            ).fetchone()
        if exists is not None:
            pytest.fail("Synthetic fixture collision; existing record was not claimed", pytrace=False)
        self._emails.add(email)
        self.cleanup_verified = False
        return email

    def _check_catalog_schema(self, connection):
        connection.execute("SELECT id, manufacturer, part_number, name, category FROM public.parts WHERE FALSE")
        connection.execute(
            "SELECT id, service_record_id, part_id, name, part_number, manufacturer, quantity, notes "
            "FROM public.service_parts WHERE FALSE"
        )
        unique = connection.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_catalog.pg_constraint "
            "WHERE conrelid = to_regclass(%s) AND contype = 'u'", ("public.parts",),
        ).fetchall()
        references = connection.execute(
            "SELECT pg_get_constraintdef(oid), condeferrable FROM pg_catalog.pg_constraint "
            "WHERE conrelid = to_regclass(%s) AND contype = 'f'", ("public.service_parts",),
        ).fetchall()
        if (
            ("UNIQUE (manufacturer, part_number)",) not in unique
            or ("FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE SET NULL", False) not in references
        ):
            pytest.fail("Prepared catalog/snapshot constraints are required; schema was not changed", pytrace=False)

    def track_user(self, user_id, email):
        if email not in self._emails:
            raise TestDatabaseSafetyError("Only reserved synthetic users may be tracked")
        with self.connect(self.settings, read_only=True) as connection:
            row = connection.execute(
                "SELECT id FROM public.users WHERE id = %s AND email = %s", (user_id, email)
            ).fetchone()
        if row != (user_id,):
            raise TestDatabaseSafetyError("Synthetic user ownership could not be verified")
        self._users[user_id] = email

    def track_session(self, session_id, user_id):
        if user_id not in self._users:
            raise TestDatabaseSafetyError("Session owner must be a tracked synthetic user")
        with self.connect(self.settings, read_only=True) as connection:
            row = connection.execute(
                "SELECT id, token_hash FROM public.user_sessions WHERE id = %s AND user_id = %s",
                (session_id, user_id),
            ).fetchone()
        if row is None:
            raise TestDatabaseSafetyError("Synthetic session ownership could not be verified")
        self._sessions[row[0]] = (user_id, row[1])

    def require_reserved_session(self, token):
        if token is None:
            return
        with self.connect(self.settings, read_only=True) as connection:
            row = connection.execute(
                "SELECT u.id, u.email FROM public.user_sessions AS s "
                "JOIN public.users AS u ON u.id = s.user_id WHERE s.token_hash = %s",
                (hash_session_token(token),),
            ).fetchone()
        if row is not None:
            if row[1] not in self._emails:
                raise TestDatabaseSafetyError("Only reserved synthetic sessions are permitted")
            self._users[row[0]] = row[1]

    def reserve_vehicle(self, user_id, vehicle):
        if user_id not in self._users:
            raise TestDatabaseSafetyError("Vehicle owner must be a tracked synthetic user")
        reservation = (user_id, *(getattr(vehicle, field) for field in VEHICLE_FIELDS))
        if reservation not in self._vehicle_reservations:
            with self.connect(self.settings, read_only=True) as connection:
                exists = connection.execute(
                    "SELECT id FROM public.vehicles WHERE user_id = %s AND " + VEHICLE_MATCH,
                    reservation,
                ).fetchone()
            if exists is not None:
                raise TestDatabaseSafetyError("Synthetic vehicle collision; existing record was not claimed")
            self._vehicle_reservations.add(reservation)
        self.cleanup_verified = False

    def track_vehicle(self, vehicle_id, user_id, vehicle):
        reservation = (user_id, *(getattr(vehicle, field) for field in VEHICLE_FIELDS))
        if reservation not in self._vehicle_reservations:
            raise TestDatabaseSafetyError("Vehicle must be reserved before writing")
        with self.connect(self.settings, read_only=True) as connection:
            row = connection.execute(
                "SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s AND " + VEHICLE_MATCH,
                (vehicle_id, *reservation),
            ).fetchone()
        if row != (vehicle_id,):
            raise TestDatabaseSafetyError("Synthetic vehicle ownership could not be verified")
        self._vehicles[vehicle_id] = user_id

    def require_reserved_vehicle(self, vehicle_id, user_id):
        if user_id not in self._users:
            raise TestDatabaseSafetyError("Vehicle owner must be a tracked synthetic user")
        with self.connect(self.settings, read_only=True) as connection:
            row = connection.execute(
                "SELECT id FROM public.vehicles WHERE id = %s AND user_id = %s",
                (vehicle_id, user_id),
            ).fetchone()
        # Let the production query return its ordinary missing/foreign outcome.
        # Never adopt a record merely because its owner or current values match.
        if row is not None and self._vehicles.get(vehicle_id) != user_id:
            raise TestDatabaseSafetyError("Only tracked synthetic vehicles may be accessed or updated")
        if row is not None:
            self.cleanup_verified = False
        return row is not None

    def require_reserved_service(self, service_id, vehicle_id, user_id):
        self.require_reserved_vehicle(vehicle_id, user_id)
        with self.connect(self.settings, read_only=True) as connection:
            row = connection.execute(
                "SELECT s.id FROM public.service_records AS s "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s",
                (service_id, vehicle_id, user_id),
            ).fetchone()
        # Missing, foreign and wrong-parent requests reach the ordinary safe 404.
        # Never adopt ordinary data, even under a synthetic parent.
        if row is not None and self._services.get(service_id) != (vehicle_id, user_id):
            raise TestDatabaseSafetyError("Only tracked synthetic service records may be accessed or updated")
        if row is not None:
            self.cleanup_verified = False
        return row is not None

    def _recover_and_delete_vehicles(self, connection):
        for reservation in self._vehicle_reservations:
            rows = connection.execute(
                "SELECT id FROM public.vehicles WHERE user_id = %s AND " + VEHICLE_MATCH,
                reservation,
            ).fetchall()
            for (vehicle_id,) in rows:
                self._vehicles[vehicle_id] = reservation[0]
        for vehicle_id, user_id in self._vehicles.items():
            connection.execute(
                "DELETE FROM public.vehicles WHERE id = %s AND user_id = %s",
                (vehicle_id, user_id),
            )

    def reserve_service(self, vehicle_id, user_id, service):
        if user_id not in self._users or self._vehicles.get(vehicle_id) != user_id:
            raise TestDatabaseSafetyError("Service parent must be an exact tracked synthetic vehicle and owner")
        reservation = (vehicle_id, user_id, *(getattr(service, field) for field in SERVICE_FIELDS))
        if reservation not in self._service_reservations:
            with self.connect(self.settings, read_only=True) as connection:
                exists = connection.execute(
                    "SELECT s.id FROM public.service_records AS s "
                    "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                    "WHERE s.vehicle_id = %s AND v.user_id = %s AND " + SERVICE_MATCH,
                    reservation,
                ).fetchone()
            if exists is not None:
                raise TestDatabaseSafetyError("Synthetic service collision; existing record was not claimed")
            self._service_reservations.add(reservation)
        self.cleanup_verified = False

    def track_service(self, service_id, vehicle_id, user_id, service):
        reservation = (vehicle_id, user_id, *(getattr(service, field) for field in SERVICE_FIELDS))
        if reservation not in self._service_reservations:
            raise TestDatabaseSafetyError("Service must be reserved before writing")
        with self.connect(self.settings, read_only=True) as connection:
            row = connection.execute(
                "SELECT s.id FROM public.service_records AS s "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s AND " + SERVICE_MATCH,
                (service_id, *reservation),
            ).fetchone()
        if row != (service_id,):
            raise TestDatabaseSafetyError("Synthetic service ownership could not be verified")
        self._services[service_id] = (vehicle_id, user_id)
        self.cleanup_verified = False

    def _recover_and_delete_services(self, connection):
        for reservation in self._service_reservations:
            rows = connection.execute(
                "SELECT s.id FROM public.service_records AS s "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.vehicle_id = %s AND v.user_id = %s AND " + SERVICE_MATCH,
                reservation,
            ).fetchall()
            for (service_id,) in rows:
                self._services[service_id] = reservation[:2]
        for service_id, (vehicle_id, user_id) in self._services.items():
            row = connection.execute(
                "SELECT s.id FROM public.service_records AS s "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s FOR UPDATE OF s",
                (service_id, vehicle_id, user_id),
            ).fetchone()
            if row is None:
                continue
            linked = connection.execute(
                "SELECT EXISTS (SELECT 1 FROM public.service_parts WHERE service_record_id = %s) "
                "OR EXISTS (SELECT 1 FROM public.maintenance_completions "
                "WHERE service_record_id = %s AND vehicle_id = %s)",
                (service_id, service_id, vehicle_id),
            ).fetchone()
            if linked != (False,):
                raise TestDatabaseSafetyError("Synthetic service has unexpected linked records; no cascade permitted")
            connection.execute(
                "DELETE FROM public.service_records AS s USING public.vehicles AS v "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.id = s.vehicle_id AND v.user_id = %s",
                (service_id, vehicle_id, user_id),
            )

    def _remaining_services(self, connection):
        if not self._service_reservations and not self._services:
            return []
        return connection.execute(
            "SELECT s.id FROM public.service_records AS s "
            "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
            "WHERE s.id = ANY(%s) OR (s.vehicle_id = ANY(%s) AND v.user_id = ANY(%s))",
            (list(self._services), list({row[0] for row in self._service_reservations}),
             list({row[1] for row in self._service_reservations})),
        ).fetchall()

    def _require_service_fixture(self, service_id, vehicle_id, user_id):
        if (
            user_id not in self._users or self._vehicles.get(vehicle_id) != user_id
            or self._services.get(service_id) != (vehicle_id, user_id)
        ):
            raise TestDatabaseSafetyError("Linked record requires an exact tracked synthetic service and owner")

    def reserve_part_snapshot(self, service_id, vehicle_id, user_id, *, name=None):
        self._require_service_fixture(service_id, vehicle_id, user_id)
        if name is None:
            name = f"gg-service-part-{uuid4().hex}"
        if not isinstance(name, str) or not name:
            raise TestDatabaseSafetyError("Synthetic snapshot requires an exact reserved name")
        reservation = (service_id, vehicle_id, user_id, name)
        if reservation in self._part_reservations:
            return name
        with self.connect(self.settings, read_only=True) as connection:
            existing = connection.execute(
                "SELECT p.id FROM public.service_parts AS p "
                "JOIN public.service_records AS s ON s.id = p.service_record_id "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s AND p.name = %s",
                (service_id, vehicle_id, user_id, name),
            ).fetchone()
        if existing is not None:
            raise TestDatabaseSafetyError("Synthetic part snapshot collision; existing record was not claimed")
        self._part_reservations.add((service_id, vehicle_id, user_id, name))
        self.cleanup_verified = False
        return name

    def remember_part_snapshot(self, snapshot_id, service_id, vehicle_id, user_id, name):
        """Record an exact ID returned by this fixture's own INSERT or API write.

        Capture before commit when available, or immediately on API receipt
        before assertions. Never call from discovery scans. Absent rolled-back
        IDs are harmless; a captured ID survives a lost acknowledgment.
        """
        self._require_service_fixture(service_id, vehicle_id, user_id)
        reservation = (service_id, vehicle_id, user_id, name)
        if reservation not in self._part_reservations:
            raise TestDatabaseSafetyError("Snapshot must be reserved before writing")
        if type(snapshot_id) is not int or not 1 <= snapshot_id <= 2147483647:
            raise TestDatabaseSafetyError("Snapshot requires an exact returned integer ID")
        if snapshot_id in self._parts and self._parts[snapshot_id] != reservation:
            raise TestDatabaseSafetyError("Snapshot ID already belongs to another fixture reservation")
        self._parts[snapshot_id] = reservation
        self.cleanup_verified = False

    def track_part_snapshot(self, snapshot_id, service_id, vehicle_id, user_id, name):
        self._require_service_fixture(service_id, vehicle_id, user_id)
        reservation = (service_id, vehicle_id, user_id, name)
        if reservation not in self._part_reservations:
            raise TestDatabaseSafetyError("Snapshot must be reserved before writing")
        with self.connect(self.settings, read_only=True) as connection:
            row = connection.execute(
                "SELECT p.id FROM public.service_parts AS p "
                "JOIN public.service_records AS s ON s.id = p.service_record_id "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE p.id = %s AND s.id = %s AND s.vehicle_id = %s AND v.user_id = %s AND p.name = %s",
                (snapshot_id, *reservation),
            ).fetchone()
        if row != (snapshot_id,):
            raise TestDatabaseSafetyError("Synthetic snapshot ownership could not be verified")
        self.remember_part_snapshot(snapshot_id, service_id, vehicle_id, user_id, name)

    def require_reserved_parts(self, service_id, vehicle_id, user_id):
        if not self.require_reserved_service(service_id, vehicle_id, user_id):
            return False
        with self.connect(self.settings, read_only=True) as connection:
            rows = connection.execute(
                "SELECT p.id, p.name FROM public.service_parts AS p "
                "JOIN public.service_records AS s ON s.id = p.service_record_id "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s",
                (service_id, vehicle_id, user_id),
            ).fetchall()
        for snapshot_id, name in rows:
            reservation = (service_id, vehicle_id, user_id, name)
            if self._parts.get(snapshot_id) != reservation:
                raise TestDatabaseSafetyError("Only reserved synthetic part snapshots may be accessed")
        return True

    def require_reserved_catalog_pair(self, manufacturer, part_number):
        with self.connect(self.settings, read_only=True) as connection:
            row = connection.execute(
                "SELECT id FROM public.parts WHERE manufacturer = %s AND part_number = %s",
                (manufacturer, part_number),
            ).fetchone()
        if row is not None and row[0] not in self._catalog_parts:
            raise TestDatabaseSafetyError("Only reserved synthetic catalog rows may be used")
        return row is not None

    def reserve_catalog_part(self):
        tag = uuid4().hex
        fields = {"manufacturer": f"gg-catalog-maker-{tag}", "part_number": f"gg-catalog-number-{tag}",
                  "name": f"gg-catalog-part-{tag}", "category": "Synthetic fixture"}
        pair = (fields["manufacturer"], fields["part_number"])
        with self.connect(self.settings, read_only=True) as connection:
            existing = connection.execute(
                "SELECT id FROM public.parts WHERE manufacturer = %s AND part_number = %s", pair,
            ).fetchone()
        if existing is not None:
            raise TestDatabaseSafetyError("Synthetic catalog collision; existing row was not claimed")
        self._catalog_reservations.add(pair)
        self.cleanup_verified = False
        return fields

    def remember_catalog_part(self, part_id, manufacturer, part_number):
        """Capture this fixture's exact INSERT RETURNING ID before commit."""
        pair = (manufacturer, part_number)
        if pair not in self._catalog_reservations:
            raise TestDatabaseSafetyError("Catalog row must be reserved before writing")
        if type(part_id) is not int or not 1 <= part_id <= 2147483647:
            raise TestDatabaseSafetyError("Catalog fixture requires an exact returned integer ID")
        if part_id in self._catalog_parts and self._catalog_parts[part_id] != pair:
            raise TestDatabaseSafetyError("Catalog ID already belongs to another fixture reservation")
        self._catalog_parts[part_id] = pair
        self.cleanup_verified = False

    def track_catalog_part(self, part_id, manufacturer, part_number):
        pair = (manufacturer, part_number)
        if pair not in self._catalog_reservations:
            raise TestDatabaseSafetyError("Catalog row must be reserved before writing")
        with self.connect(self.settings, read_only=True) as connection:
            row = connection.execute(
                "SELECT id FROM public.parts WHERE id = %s AND manufacturer = %s AND part_number = %s",
                (part_id, *pair),
            ).fetchone()
        if row != (part_id,):
            raise TestDatabaseSafetyError("Synthetic catalog identity could not be verified")
        self.remember_catalog_part(part_id, manufacturer, part_number)

    def _delete_catalog_fixtures(self, connection):
        if not self._catalog_reservations and not self._catalog_parts:
            return
        for pair in self._catalog_reservations:
            rows = connection.execute(
                "SELECT id FROM public.parts WHERE manufacturer = %s AND part_number = %s", pair,
            ).fetchall()
            for (part_id,) in rows:
                if self._catalog_parts.get(part_id) != pair:
                    raise TestDatabaseSafetyError("Unexpected catalog ID; a pair match cannot establish fixture ownership")
        for part_id in self._catalog_parts:
            row = connection.execute("SELECT id FROM public.parts WHERE id = %s FOR UPDATE", (part_id,)).fetchone()
            if row is None:
                continue
            linked = connection.execute(
                "SELECT EXISTS (SELECT 1 FROM public.service_parts WHERE part_id = %s) "
                "OR EXISTS (SELECT 1 FROM public.saved_parts WHERE part_id = %s) "
                "OR EXISTS (SELECT 1 FROM public.part_fitments WHERE part_id = %s)",
                (part_id, part_id, part_id),
            ).fetchone()
            if linked != (False,):
                raise TestDatabaseSafetyError("Synthetic catalog row has unexpected references; no SET NULL permitted")
            connection.execute("DELETE FROM public.parts WHERE id = %s", (part_id,))

    def _remaining_catalog_fixtures(self, connection):
        if not self._catalog_reservations and not self._catalog_parts:
            return []
        rows = connection.execute("SELECT id FROM public.parts WHERE id = ANY(%s)", (list(self._catalog_parts),)).fetchall()
        for pair in self._catalog_reservations:
            rows.extend(connection.execute(
                "SELECT id FROM public.parts WHERE manufacturer = %s AND part_number = %s", pair,
            ).fetchall())
        return rows

    def reserve_maintenance_schedule(self, vehicle_id, user_id):
        if user_id not in self._users or self._vehicles.get(vehicle_id) != user_id:
            raise TestDatabaseSafetyError("Schedule requires an exact tracked synthetic vehicle and owner")
        name = f"gg-service-schedule-{uuid4().hex}"
        with self.connect(self.settings, read_only=True) as connection:
            existing = connection.execute(
                "SELECT m.id FROM public.maintenance_schedules AS m "
                "JOIN public.vehicles AS v ON v.id = m.vehicle_id "
                "WHERE m.vehicle_id = %s AND v.user_id = %s AND m.name = %s",
                (vehicle_id, user_id, name),
            ).fetchone()
        if existing is not None:
            raise TestDatabaseSafetyError("Synthetic schedule collision; existing record was not claimed")
        self._schedule_reservations.add((vehicle_id, user_id, name))
        self.cleanup_verified = False
        return name

    def reserve_maintenance_completion(self, schedule_id, service_id, vehicle_id, user_id):
        self._require_service_fixture(service_id, vehicle_id, user_id)
        names = [name for parent, owner, name in self._schedule_reservations if (parent, owner) == (vehicle_id, user_id)]
        if not names:
            raise TestDatabaseSafetyError("Completion schedule must be reserved before writing")
        with self.connect(self.settings, read_only=True) as connection:
            schedule = connection.execute(
                "SELECT m.name FROM public.maintenance_schedules AS m "
                "JOIN public.vehicles AS v ON v.id = m.vehicle_id "
                "WHERE m.id = %s AND m.vehicle_id = %s AND v.user_id = %s AND m.name = ANY(%s)",
                (schedule_id, vehicle_id, user_id, names),
            ).fetchone()
            if schedule is None:
                raise TestDatabaseSafetyError("Completion schedule ownership could not be verified")
            existing = connection.execute(
                "SELECT c.id FROM public.maintenance_completions AS c "
                "JOIN public.service_records AS s ON s.id = c.service_record_id AND s.vehicle_id = c.vehicle_id "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE c.schedule_id = %s AND s.id = %s AND s.vehicle_id = %s AND v.user_id = %s",
                (schedule_id, service_id, vehicle_id, user_id),
            ).fetchone()
        if existing is not None:
            raise TestDatabaseSafetyError("Synthetic completion collision; existing record was not claimed")
        self._schedules[schedule_id] = (vehicle_id, user_id, schedule[0])
        self._completion_reservations.add((schedule_id, service_id, vehicle_id, user_id))
        self.cleanup_verified = False

    def _recover_linked_fixtures(self, connection):
        for service_id, vehicle_id, user_id, name in self._part_reservations:
            rows = connection.execute(
                "SELECT p.id FROM public.service_parts AS p "
                "JOIN public.service_records AS s ON s.id = p.service_record_id "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE s.id = %s AND s.vehicle_id = %s AND v.user_id = %s AND p.name = %s",
                (service_id, vehicle_id, user_id, name),
            ).fetchall()
            for (part_id,) in rows:
                if self._parts.get(part_id) != (service_id, vehicle_id, user_id, name):
                    raise TestDatabaseSafetyError("Unexpected snapshot ID; name matches cannot establish fixture ownership")
        for vehicle_id, user_id, name in self._schedule_reservations:
            rows = connection.execute(
                "SELECT m.id FROM public.maintenance_schedules AS m "
                "JOIN public.vehicles AS v ON v.id = m.vehicle_id "
                "WHERE m.vehicle_id = %s AND v.user_id = %s AND m.name = %s",
                (vehicle_id, user_id, name),
            ).fetchall()
            for (schedule_id,) in rows:
                self._schedules[schedule_id] = (vehicle_id, user_id, name)
        for reservation in self._completion_reservations:
            rows = connection.execute(
                "SELECT c.id FROM public.maintenance_completions AS c "
                "JOIN public.service_records AS s ON s.id = c.service_record_id AND s.vehicle_id = c.vehicle_id "
                "JOIN public.vehicles AS v ON v.id = s.vehicle_id "
                "WHERE c.schedule_id = %s AND s.id = %s AND s.vehicle_id = %s AND v.user_id = %s",
                reservation,
            ).fetchall()
            for (completion_id,) in rows:
                self._completions[completion_id] = reservation

    def _delete_linked_fixtures(self, connection):
        self._recover_linked_fixtures(connection)
        for completion_id, reservation in self._completions.items():
            connection.execute(
                "DELETE FROM public.maintenance_completions AS c USING public.service_records AS s, public.vehicles AS v "
                "WHERE c.id = %s AND c.schedule_id = %s AND c.service_record_id = %s AND c.vehicle_id = %s "
                "AND s.id = c.service_record_id AND s.vehicle_id = c.vehicle_id "
                "AND v.id = s.vehicle_id AND v.user_id = %s", (completion_id, *reservation),
            )
        for part_id, reservation in self._parts.items():
            service_id, vehicle_id, user_id, name = reservation
            connection.execute(
                "DELETE FROM public.service_parts AS p USING public.service_records AS s, public.vehicles AS v "
                "WHERE p.id = %s AND p.service_record_id = %s AND s.id = p.service_record_id "
                "AND s.vehicle_id = %s AND v.id = s.vehicle_id AND v.user_id = %s AND p.name = %s",
                (part_id, service_id, vehicle_id, user_id, name),
            )
        for schedule_id, (vehicle_id, user_id, name) in self._schedules.items():
            row = connection.execute(
                "SELECT m.id FROM public.maintenance_schedules AS m JOIN public.vehicles AS v ON v.id = m.vehicle_id "
                "WHERE m.id = %s AND m.vehicle_id = %s AND v.user_id = %s AND m.name = %s FOR UPDATE OF m",
                (schedule_id, vehicle_id, user_id, name),
            ).fetchone()
            if row is None:
                continue
            linked = connection.execute(
                "SELECT EXISTS (SELECT 1 FROM public.maintenance_completions WHERE schedule_id = %s AND vehicle_id = %s)",
                (schedule_id, vehicle_id),
            ).fetchone()
            if linked != (False,):
                raise TestDatabaseSafetyError("Synthetic schedule has unexpected completion links; no cascade permitted")
            connection.execute(
                "DELETE FROM public.maintenance_schedules AS m USING public.vehicles AS v "
                "WHERE m.id = %s AND m.vehicle_id = %s AND v.id = m.vehicle_id AND v.user_id = %s AND m.name = %s",
                (schedule_id, vehicle_id, user_id, name),
            )

    def _remaining_linked_fixtures(self, connection):
        if not (self._part_reservations or self._schedule_reservations or self._completion_reservations):
            return False
        parts = connection.execute(
            "SELECT id FROM public.service_parts WHERE id = ANY(%s) "
            "OR (service_record_id = ANY(%s) AND name = ANY(%s))",
            (list(self._parts), list({row[0] for row in self._part_reservations}),
             list({row[3] for row in self._part_reservations})),
        ).fetchall()
        schedules = connection.execute(
            "SELECT id FROM public.maintenance_schedules WHERE id = ANY(%s) "
            "OR (vehicle_id = ANY(%s) AND name = ANY(%s))",
            (list(self._schedules), list({row[0] for row in self._schedule_reservations}),
             list({row[2] for row in self._schedule_reservations})),
        ).fetchall()
        completions = connection.execute(
            "SELECT id FROM public.maintenance_completions WHERE id = ANY(%s) OR "
            "(schedule_id = ANY(%s) AND service_record_id = ANY(%s) AND vehicle_id = ANY(%s))",
            (list(self._completions), list({row[0] for row in self._completion_reservations}),
             list({row[1] for row in self._completion_reservations}), list({row[2] for row in self._completion_reservations})),
        ).fetchall()
        return bool(parts or schedules or completions)

    def _recover_and_delete_owned(self, connection):
        for email in self._emails:
            row = connection.execute(
                "SELECT id FROM public.users WHERE email = %s", (email,)
            ).fetchone()
            if row is not None:
                self._users[row[0]] = email
                sessions = connection.execute(
                    "SELECT id, token_hash FROM public.user_sessions WHERE user_id = %s", (row[0],)
                ).fetchall()
                for session_id, token_hash in sessions:
                    self._sessions[session_id] = (row[0], token_hash)
        self._delete_linked_fixtures(connection)
        self._delete_catalog_fixtures(connection)
        self._recover_and_delete_services(connection)
        self._recover_and_delete_vehicles(connection)
        for session_id, (user_id, token_hash) in self._sessions.items():
            connection.execute(
                "DELETE FROM public.user_sessions WHERE id = %s AND user_id = %s AND token_hash = %s",
                (session_id, user_id, token_hash),
            )
        for user_id, email in self._users.items():
            connection.execute(
                "DELETE FROM public.users WHERE id = %s AND email = %s", (user_id, email)
            )

    def cleanup(self):
        if not self._emails and not self._catalog_reservations and not self._catalog_parts:
            return
        try:
            with self.connect(self.settings, read_only=False) as connection:
                self._recover_and_delete_owned(connection)
            with self.connect(self.settings, read_only=True) as connection:
                remaining = connection.execute(
                    "SELECT id FROM public.users WHERE email = ANY(%s)",
                    (list(self._emails),),
                ).fetchall()
                sessions = connection.execute(
                    "SELECT id FROM public.user_sessions WHERE id = ANY(%s) OR user_id = ANY(%s)",
                    (list(self._sessions), list(self._users)),
                ).fetchall()
                vehicles = []
                if self._vehicle_reservations:
                    vehicles = connection.execute(
                        "SELECT id FROM public.vehicles WHERE id = ANY(%s) OR user_id = ANY(%s)",
                        (list(self._vehicles), list(self._users)),
                    ).fetchall()
                services = self._remaining_services(connection)
                links = self._remaining_linked_fixtures(connection)
                catalog = self._remaining_catalog_fixtures(connection)
                if remaining or sessions or vehicles or services or links or catalog:
                    pytest.fail("Synthetic cleanup verification failed; stop native testing", pytrace=False)
        except psycopg.Error:
            pytest.fail("Synthetic cleanup failed; stop native testing and resolve tracked fixtures", pytrace=False)
        self.cleanup_counts = (len(self._users), len(self._sessions))
        self.cleanup_vehicle_count = len(self._vehicles)
        self.cleanup_service_count = len(self._services)
        self.cleanup_link_counts = (len(self._parts), len(self._completions), len(self._schedules))
        self.cleanup_catalog_count = len(self._catalog_parts)
        self.cleanup_verified = True
        self._emails.clear()
        self._users.clear()
        self._sessions.clear()
        self._vehicle_reservations.clear()
        self._vehicles.clear()
        self._service_reservations.clear()
        self._services.clear()
        self._part_reservations.clear()
        self._schedule_reservations.clear()
        self._completion_reservations.clear()
        self._parts.clear()
        self._catalog_reservations.clear()
        self._catalog_parts.clear()
        self._schedules.clear()
        self._completions.clear()
