import psycopg

from app.config import Settings


EXPECTED_TABLES = (
    "users", "vehicles", "service_records", "user_sessions",
    "maintenance_schedules", "maintenance_completions", "parts",
    "part_fitments", "saved_parts", "service_parts",
)


def check_database(settings: Settings) -> bool:
    # Read-only transactions also protect against accidental writes in this check.
    with psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.database,
        user=settings.user,
        password=settings.password,
        connect_timeout=3,
        options="-c default_transaction_read_only=on -c statement_timeout=3000",
    ) as connection:
        if connection.execute("SELECT 1").fetchone() != (1,):
            return False
        rows = connection.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "AND table_name = ANY(%s)",
            (list(EXPECTED_TABLES),),
        ).fetchall()
        view = connection.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.views "
            "WHERE table_schema = 'public' AND table_name = %s)",
            ("vehicle_expense_summary",),
        ).fetchone()
        return len(rows) == len(EXPECTED_TABLES) and view == (True,)
