# GarageGuide
Project backbone: React (Vite and JavaScript) → FastAPI (Python 3.13) → PostgreSQL (psycopg). The only screen checks connectivity. Product features are deferred.

## Structure

| Directory | Purpose |
| --- | --- |
| `frontend/` | Vite configuration, npm scripts and dependency lockfile. |
| `frontend/src/` | React entry point, responsive shell, API helper and CSS. |
| `backend/` | Requirements, example environments and pytest tool configuration. Dependencies are declared only in requirements files. |
| `backend/app/` | App creation in `main.py`, settings in `config.py`, read-only psycopg checks in `database.py`. |
| `backend/app/routes/` | Health endpoints only. |
| `backend/tests/` | Health behavior, test database safeguards and opt-in native PostgreSQL check. |
| `database/` | Existing authoritative SQL and database instructions. |
| `docs/verification/` | Historical database evidence and current manual verification instructions. |

## Database setup

Install Python **3.13**, Node.js **22.12+** with npm, and native PostgreSQL with psql or pgAdmin. Run the examples from the repository root unless noted. SQL remains the source of truth; there is no ORM or automatic schema creation.

Create two empty databases through pgAdmin or your PostgreSQL administrator:

- `garageguide_app`: development only.
- `garageguide_app_test`: application tests only.

Use local PostgreSQL roles with appropriate access. Supply credentials privately. Apply `database/01_schema.sql`, then `database/02_views.sql`, once to each fresh database. Do not reapply the schema to initialized databases; it is not an upgrade script.

From the repository root, with psql on PATH, replace `YOUR_LOCAL_ROLE` and run each command, checking for success before continuing:

```powershell
psql -h localhost -U YOUR_LOCAL_ROLE -d garageguide_app -v ON_ERROR_STOP=1 -f database/01_schema.sql
psql -h localhost -U YOUR_LOCAL_ROLE -d garageguide_app -v ON_ERROR_STOP=1 -f database/02_views.sql
psql -h localhost -U YOUR_LOCAL_ROLE -d garageguide_app_test -v ON_ERROR_STOP=1 -f database/01_schema.sql
psql -h localhost -U YOUR_LOCAL_ROLE -d garageguide_app_test -v ON_ERROR_STOP=1 -f database/02_views.sql
```

Passwords are prompted when needed. See [database instructions](database/README.md) for pgAdmin and full psql paths. Inherited `garageguide`/`garageguide_test` references in SQL comments and historical evidence describe the original SQL package; use the application database names above for this backbone.

## Backend

From the repository root, create the backend virtual environment with Python 3.13, then use `backend/.venv/Scripts/python.exe` for all subsequent backend Python commands:

```powershell
py -3.13 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
Copy-Item backend/.env.example backend/.env
Copy-Item backend/.env.test.example backend/.env.test
```

Do not overwrite existing private environment files. Edit the private files to supply `PGUSER` and `PGPASSWORD`, keeping the database names distinct. Exported PostgreSQL environment variables override file values. Remove unintended `PGDATABASE` overrides before tests. Tests never load the development `.env`.

For runtime-only installation use `backend/requirements.txt`; `requirements-dev.txt` includes it and adds testing dependencies. `pyproject.toml` contains tool settings only.

From the repository root, start FastAPI; `--app-dir backend` makes the backend application importable:

```powershell
backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

- `/api/health`: API liveness without PostgreSQL.
- `/api/health/db`: `SELECT 1` plus expected public table/view presence. This checks availability, not full schema-definition equivalence.

Checks use read-only transactions and bounded connection/query waits. They never apply SQL or read product records. Failures return HTTP 503 with generic messages.

## Frontend

In another terminal from the repository root:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to FastAPI at `127.0.0.1:8000`. React receives no database credentials. Servers bind to loopback; use browser device emulation for responsive checks.

```powershell
npm run lint
npm run build
npm run preview
```

Preview is available at `http://127.0.0.1:4173` and also proxies to the running backend. Production hosting is outside this milestone.

## Tests and verification

From the repository root, select the backend pytest configuration and test directory explicitly:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration"
$env:RUN_DB_TESTS = '1'
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests
Remove-Item Env:RUN_DB_TESTS
```

The first command requires no running database. The full run needs initialized `garageguide_app_test` and private test credentials. Without `RUN_DB_TESTS=1`, the native PostgreSQL test explicitly skips; with it enabled, connection errors fail the test.

Application tests reject every database name except `garageguide_app_test` before connecting. They never reset databases, insert fixtures, delete rows, or load development credentials. Their database check is read-only.

From the repository root, run the existing SQL assertions separately against `garageguide_app_test` only:

```powershell
psql -h localhost -U YOUR_LOCAL_ROLE -d garageguide_app_test -v ON_ERROR_STOP=1 -f database/03_database_tests.sql
```

The SQL suite creates transactional fixtures and rolls them back; identity counters can advance. Never run it or the optional practice script on `garageguide_app`.

Follow [manual browser checks](docs/verification/BROWSER_CHECKS.md) for connection, responsive behavior, failure and retry. [Historical verification](docs/verification/VERIFICATION.md) records the original PGlite run only, not native application connectivity.
