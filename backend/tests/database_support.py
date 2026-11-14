from uuid import uuid4

import psycopg
import pytest

from app.config import TEST_DATABASE
from app.security import hash_session_token


VEHICLE_FIELDS = ("year", "make", "model", "engine", "vehicle_type", "mileage", "operating_hours")
VEHICLE_MATCH = " AND ".join(f"{field} IS NOT DISTINCT FROM %s" for field in VEHICLE_FIELDS)


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
        self.cleanup_verified = False
        self.cleanup_counts = (0, 0)
        self.cleanup_vehicle_count = 0

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
        except psycopg.Error:
            pytest.fail("Prepared users/session/vehicle schema could not be verified; schema was not changed", pytrace=False)

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
        if not self._emails:
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
                if remaining or sessions or vehicles:
                    pytest.fail("Synthetic cleanup verification failed; stop native testing", pytrace=False)
        except psycopg.Error:
            pytest.fail("Synthetic cleanup failed; stop native testing and resolve tracked fixtures", pytrace=False)
        self.cleanup_counts = (len(self._users), len(self._sessions))
        self.cleanup_vehicle_count = len(self._vehicles)
        self.cleanup_verified = True
        self._emails.clear()
        self._users.clear()
        self._sessions.clear()
        self._vehicle_reservations.clear()
        self._vehicles.clear()
