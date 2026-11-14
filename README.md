# GarageGuide
Application stack: React (Vite and JavaScript) → FastAPI (Python 3.13) → PostgreSQL (psycopg). The connection screen is at `/`; completed account registration is at `/register`, with its original browser report recorded November 4, 2026. Feature 2's authentication API and React interfaces have passed final implementation checks, with user-performed development/preview browser observations recorded November 6, 2026. An approved review checkpoint and independent audit remain required before completion.

## Structure

| Directory | Purpose |
| --- | --- |
| `frontend/` | Vite configuration, npm scripts and dependency lockfile. |
| `frontend/src/` | One React Router, public connection/registration/login pages, protected account/garage/create-vehicle pages, in-memory session state, API helpers and responsive CSS. |
| `backend/` | Requirements, example environments and pytest tool configuration. Dependencies are declared only in requirements files. |
| `backend/app/` | App creation, private settings, credential validation/hashing, and direct psycopg queries with explicit transaction boundaries. |
| `backend/app/routes/` | Public health endpoints, registration, login/session/logout, and authenticated vehicle list/create APIs with safe errors and mutation CSRF enforcement. |
| `backend/tests/` | Database-free health/registration tests, guarded opt-in native transaction/API checks, and a synthetic-account-only manual browser backend launcher. |
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

Passwords are prompted when needed. See [database instructions](database/README.md) for pgAdmin and full psql paths. Inherited `garageguide`/`garageguide_test` references in SQL comments and historical evidence describe the original SQL package; use the application database names above for this application.

## Backend

From the repository root, create the backend virtual environment with Python 3.13, then use `backend/.venv/Scripts/python.exe` for all subsequent backend Python commands:

```powershell
py -3.13 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
Copy-Item backend/.env.example backend/.env
Copy-Item backend/.env.test.example backend/.env.test
```

Do not overwrite existing private environment files. Edit the private files to supply `PGUSER` and `PGPASSWORD`, keeping the database names distinct. Exported PostgreSQL environment variables override file values. Remove unintended `PGDATABASE` overrides before tests. Tests never load the development `.env`.

Authentication, including registration, now requires the explicit `AUTH_*` keys
shown in the corresponding environment example. For loopback development use
`AUTH_ENVIRONMENT=development`, `AUTH_COOKIE_SECURE=false`,
`AUTH_API_ORIGIN=http://127.0.0.1:8000`, and an empty `AUTH_FRONTEND_ORIGIN`.
The guarded manual test backend instead requires `AUTH_ENVIRONMENT=testing`
in `.env.test`. Existing private files were not automatically edited. Missing
or invalid auth settings fail closed with a generic 503; health remains public.
Production requires Secure=true and explicitly configured, matching HTTPS
API/frontend origins. No production hostname is supplied by default.

For runtime-only installation use `backend/requirements.txt`; `requirements-dev.txt` includes it and adds testing dependencies. `pyproject.toml` contains tool settings only.

From the repository root, start FastAPI; `--app-dir backend` makes the backend application importable:

```powershell
backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

- `/api/health`: API liveness without PostgreSQL.
- `/api/health/db`: `SELECT 1` plus expected public table/view presence. This checks availability, not full schema-definition equivalence.

Health checks use read-only transactions and bounded connection/query waits.
They never apply schema scripts or read product records. Failures return HTTP
503 with generic messages.

`POST /api/auth/register` accepts JSON fields `email`, `password`, and
`password_confirmation`. It trims and validates email before lowercasing the
normalized identifier. Passwords must match after NFC normalization and contain
15-128 Unicode code points, preserving case and spaces. Only an Argon2 hash is
stored. After commit, HTTP 201 returns exactly `id`, `email`, and `created_at`.
Registration creates no session, cookie, or token. The frontend page uses the
same relative API endpoint and remains on `/register` after success.

Registration failures use sanitized HTTP 422 field errors, the documented 409
duplicate-email message, generic 503 database-unavailable errors, or a generic
500 for unexpected failures. Raw validation input, request bodies, credentials,
hashes, SQL, and driver details are excluded from responses and application logs.

Registration, login, and logout require JSON (ordinary charset parameters are
accepted), the exact trusted browser Origin, and `X-GarageGuide-CSRF: 1`.
Trusted local frontend origins are `http://127.0.0.1:5173` and
`http://127.0.0.1:4173`; use these addresses rather than substituting localhost.
The browser supplies Origin; the registration helper supplies the custom header
and explicit same-origin credentials. Rejections return fixed 403 feedback
before parsing the body or performing business writes. No permissive CORS is added.

- `POST /api/auth/login`: email/password only; 200 returns exactly public `user`
  and `expires_at` after session commit. Unknown email and wrong password share
  `401 {"detail":"Invalid email or password."}` without disturbing an old session.
- `GET /api/auth/session`: cookie-based trusted identity and atomic idle extension.
  Unusable sessions return 401 and clear the cookie; database failure returns 503
  and preserves it. No mutation headers are required for this GET.
- `POST /api/auth/logout`: JSON `{}` plus CSRF headers; revoke the current browser
  session, commit, clear its cookie, and return an empty 204. Repetition is safe;
  other devices remain signed in. Database failure preserves the cookie.

The `garageguide_session` cookie is HttpOnly, SameSite=Lax, Path=/, host-only,
with no Domain and no persistent lifetime attributes when issued. Secure=false
is permitted only in validated loopback development/testing. PostgreSQL stores
only the lowercase SHA-256 token hash. Server validity requires an unrevoked
session strictly before its 30-minute idle deadline and eight-hour absolute cap;
activity extends only to the earlier limit. All authentication responses use
`Cache-Control: no-store`, and tokens/hashes never appear in JSON responses.
Login rate limiting remains a separate production-security decision.

See [authentication evidence](docs/verification/AUTHENTICATION_STATUS.md) for
separate frontend, database-free backend, and native API results. New browser
observations are recorded separately from tests; final independent review is
still pending for Feature 2.

## Frontend

In another terminal from the repository root:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to FastAPI at `127.0.0.1:8000`. React receives no database credentials. Servers bind to loopback; use browser device emulation for responsive checks.

React Router keeps the connection screen at `/` and the registration page at
`/register`; header links navigate without a document reload. Registration uses
a single POST with a 10-second timeout and no automatic retry. Correctable
validation or network failures retain passwords only in temporary component
state. Success, other failures, and leaving the page clear them.

`/login` uses the same credential rules and ten-second/no-replay request bound.
`/account` displays only the validated public email and session deadline, with a
current-browser sign-out control. Session restoration uses GET /api/auth/session
on startup. At the known local session deadline, React clears the public account
identity and enters the session-ended flow without calling /api/auth/session.
The expiration timer does not poll, retry, or extend idle activity. Later
deliberate protected navigation, refresh, visibility return, or selecting Retry
may request server validation. PostgreSQL remains authoritative for the actual
idle and absolute session deadlines. Loading/unavailable states gate private
content. A 401 clears private React state; a network/503 failure permits
deliberate retry without claiming logout. Stale responses cannot restore an old
identity after navigation or sign-out.

Only validated public user data, expiry, and UI state live in React memory.
HttpOnly cookies transport tokens without JavaScript reading them. Authentication
data is never put in browser storage, URLs, or router state. Login passwords stay
only in temporary form state after correctable validation/credential/network
failures and clear after success, other failures, or departure. The guarded manual
guide covers these behaviors; they are not browser-verified by a production build.

Focused frontend checks use the installed Node runtime's built-in test tooling;
no external test runner or dependency was installed:

```powershell
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js
```

For browser tests that create accounts, replace the ordinary backend command
with the guarded test-only launcher in [the browser guide](docs/verification/BROWSER_CHECKS.md).
It loads only test settings, enforces the connection guard, accepts only its
reserved synthetic emails, and verifies exact cleanup on normal shutdown. Do
not use the ordinary development backend for registration verification.

```powershell
npm run lint
npm run build
npm run preview
```

Preview is available at `http://127.0.0.1:4173` and also proxies to the running backend. Production hosting is outside this milestone.

## Vehicle creation and listing

Sign in, open Account, and select Open your garage. `/vehicles` lists only the
validated session owner's vehicles; `/vehicles/new` creates one. Detail, editing,
and deletion are outside Feature 3. Blank readings mean not recorded; confirmed
zero remains `0.0`. Reading values travel as decimal strings, not floating-point
numbers. The backend validates model years from 1886 through its current year
plus one. Vehicle type is free text.

- `GET /api/vehicles` returns `200 {"vehicles":[...]}`; an empty list is success.
- `POST /api/vehicles` accepts year/make/model/type, optional engine, and optional
  mileage/hours. It assigns ownership from the server session and returns a
  public vehicle with 201 only after commit and connection cleanup. It uses the
  same trusted-Origin, JSON, and custom CSRF-header policy as authentication.
- All vehicle responses use `Cache-Control: no-store`. Successful responses
  include the validated session's committed `X-GarageGuide-Session-Expires-At`.
  React accepts data/deadlines only for current session/navigation/request work;
  this does not issue an extra authentication request or create an expiry poll.
- Identical vehicles are allowed. A timeout or lost acknowledgment can conceal
  a committed create. Check the garage before deliberately resubmitting; POSTs
  are never retried automatically.

Recorded automated/native evidence and the user's November 13, 2026 browser
observations are separated in [vehicle verification](docs/verification/VEHICLES_STATUS.md).
The guarded [browser guide](docs/verification/BROWSER_CHECKS.md) uses only exact
synthetic fixtures in `garageguide_app_test`, with verified vehicle/session/user
cleanup. It must never run against ordinary development data.

## Tests and verification

From the repository root, select the backend pytest configuration and test directory explicitly:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration"
$env:RUN_DB_TESTS = '1'
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests
Remove-Item Env:RUN_DB_TESTS
```

The first command requires no running database. The full run needs initialized `garageguide_app_test` and private test credentials. Without `RUN_DB_TESTS=1`, the native PostgreSQL test explicitly skips; with it enabled, connection errors fail the test.

Application tests reject every database name except `garageguide_app_test`
before connecting and never load development credentials. Existing health
integration checks are read-only. Opt-in feature integration tests may write
unique synthetic fixtures only in `garageguide_app_test`: immediately after
opening each writable test connection, run `SELECT current_database()` once as
its first statement and verify the exact name before allowing writes. This
includes fixture, API-handler, and cleanup connections; new physical connections
need a new check, while later statements on the same connection do not;
register cleanup before writing; remove only records created by that test in
finalizers and verify removal. Never reset databases, truncate tables, or write
to `garageguide_app` or `postgres`. A guard or cleanup failure stops database
testing. Tests must not initialize missing schema or recreate databases. See
[the test policy](blueprint/context/coding-standards.md#testing) for the complete
boundary. Native fixtures verify the existing users schema before writes and
never provision it. Step 2 tests exercise direct queries and transactions.
With `RUN_DB_TESTS=1`, run these checks from
the repository root and stop on the first failure:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_user_queries_integration.py -m integration -p no:cacheprovider --maxfail=1
```

Step 3's guarded HTTP registration checks use the same opt-in and cleanup rules:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_registration_integration.py -m integration -p no:cacheprovider --maxfail=1
```

Observed registration/query test results are recorded in
[registration verification](docs/verification/REGISTRATION_STATUS.md).

From the repository root, run the existing SQL assertions separately against `garageguide_app_test` only:

```powershell
psql -h localhost -U YOUR_LOCAL_ROLE -d garageguide_app_test -v ON_ERROR_STOP=1 -f database/03_database_tests.sql
```

The SQL suite creates transactional fixtures and rolls them back; identity counters can advance. Never run it or the optional practice script on `garageguide_app`.

Follow [manual browser checks](docs/verification/BROWSER_CHECKS.md) for guarded registration, routing, password lifetime, accessibility, responsive behavior, failure and retry. The user's November 4, 2026 results are recorded separately from automated and native tests in [registration verification](docs/verification/REGISTRATION_STATUS.md). [Historical verification](docs/verification/VERIFICATION.md) records the original PGlite run only, not native application connectivity.
