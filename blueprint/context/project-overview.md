# GarageGuide - Project Overview

<!-- blueprint:source-hash 5bf34eadc710fd1ae902c2cada1ed89a158eeb262fce47f50d588e6e6194ec10 -->

> Know Your Vehicle's History. Plan Its Future.

Generated from `blueprint/project-plan.md` and `blueprint/build-plan.md`.
Change those plans and rerun `/overview` when product decisions change. The
existing SQL in `database/` is authoritative for schema fields and constraints.

## Problem

Vehicle owners otherwise rely on scattered records or memory to track service,
parts, costs, and recurring maintenance. GarageGuide keeps that information
together per vehicle, preserves historical readings and part details, and
distinguishes unknown values from real zeroes. Grounded AI-assisted reports
help explain recorded information without diagnosing mechanical problems or
determining part compatibility.

## Users

- Individual owners, families, and at-home mechanics maintaining cars,
  motorcycles, dirt bikes, ATVs, RZRs, or similar recreational vehicles using
  mileage, operating hours, or both. Shared household accounts are outside the MVP.
- Each account can access only its own vehicles and associated records.
- Repair shops, fleet operators, organizations, shared garages, and team roles
  are outside the MVP.

## Usage model

- Private owner-scoped data requires authentication and ownership checks in
  FastAPI. SQL relationships alone do not authorize requests.
- Hash passwords and session tokens. Sessions require secure cookies in
  production, expiry, revocation, and CSRF protection. Never persist plaintext
  passwords or raw session tokens.
- Use parameterized SQL. Health checks remain read-only and expose neither
  product records nor credentials or sensitive database errors.
- The browser-based MVP will initially be free to people the developer knows.
  Traffic and availability targets are unspecified; do not infer scale or
  compliance requirements. Deployed connections must be encrypted.
- AI requests use only necessary verified records for the selected vehicle.
  Never send passwords, session tokens, complete account information, unrelated
  vehicles, or another owner's records. Never sell user or vehicle data.
- Exclude VIN decoding, owner's-manual scanning/extraction, complete parts
  compatibility coverage, automatic catalog synchronization, receipt/document scanning,
  external notifications, shared garages, shop/fleet workflows, and payments.
  Additional scope or paid services require review against the course timeline.

## Features

**Existing foundation:** the responsive connection-status screen, FastAPI
health endpoints, and PostgreSQL schema/view scripts. These are pre-build
foundation, not completed product features. Historical SQL verification is
separate from native application connectivity and browser verification, which
remain pending in the scaffold evidence. All fifteen items below remain planned.

The main workflow is owner-scoped vehicle maintenance: select a vehicle, record
service, and understand recurring work. Preserve this build-plan order and IDs:

1. **Register a user account** - validate email/password input, prevent duplicates, hash passwords, and show safe success/error results.
2. **Sign in, sign out, and protect private sessions** - verify credentials, enforce expiry/revocation, protect private routes, and prove owner isolation.
3. **Create and list vehicles in a digital garage** - manually add vehicle details and miles/hours, then list only the authenticated owner's vehicles.
4. **View and update a vehicle profile** - correct vehicle details and current readings while preserving historical service readings.
5. **Record and review service history** - create, list, edit, and remove owned service records with dates, readings, costs, descriptions, and notes.
6. **Record parts used during a service** - preserve catalog-backed or manual part snapshots independently of later catalog or saved-part changes.
7. **Create and update maintenance schedules** - validate positive day/mile/hour intervals and matching baselines, with source notes and duplicate-task review.
8. **Calculate maintenance status and in-app reminders** - calculate upcoming/due/overdue work using the first reached limit and identify missing or stale inputs.
9. **Complete scheduled maintenance** - record or link service to schedules atomically, prevent duplicate links, and calculate the next occurrence without duplicate expenses.
10. **Search the limited parts catalog** - search names, categories, or part numbers and show sourced, verified fitment information without claiming uncertain compatibility.
11. **Save parts to a vehicle** - save, edit, and remove catalog or manual references, prevent duplicates, and preserve service-part history.
12. **Review vehicle expenses** - summarize known service costs, identify unknown costs, link contributing records, and reflect service changes.
13. **Generate an AI-assisted vehicle report** - summarize selected verified records through an approved provider, label output, explain missing data, link sources, and handle provider failures.
14. **Build the responsive garage dashboard and navigation** - connect completed features and show vehicles, services, maintenance, reminders, and costs with clear loading/empty/failure states.
15. **Deploy and verify the complete MVP** - deploy React, FastAPI, and PostgreSQL with private configuration; verify persistence, HTTPS, sessions, owner isolation, responsive use, and recovery.

## Data model

The ten existing tables in `database/01_schema.sql` and the live view in
`database/02_views.sql` define the starting model. The fields below describe
stored data, not implemented API routes. Do not replace or automatically recreate
this schema when implementing features.

All table primary keys are `id INTEGER GENERATED ALWAYS AS IDENTITY`.
`created_at`, where listed, is `TIMESTAMPTZ` with a current-timestamp default.
`?` means nullable; other listed columns are required.

| Table | Stored fields excluding `id` | Relationships and contracts |
| --- | --- | --- |
| `users` | `email TEXT`, `password_hash TEXT`, `created_at` | Unique, trimmed lowercase email. One user owns many vehicles and sessions. Password hashing belongs in Python. |
| `user_sessions` | `user_id INTEGER`, `token_hash TEXT`, `created_at`, `expires_at TIMESTAMPTZ`, `revoked_at TIMESTAMPTZ?` | User FK with cascade cleanup; unique token hash; expiry after creation. FastAPI must enforce expiry/revocation and cookie behavior. |
| `vehicles` | `user_id INTEGER`, `year SMALLINT`, `make TEXT`, `model TEXT`, `vehicle_type TEXT`, `engine TEXT?`, `mileage NUMERIC(12,1)?`, `operating_hours NUMERIC(12,1)?`, `readings_updated_at TIMESTAMPTZ?`, `created_at` | User FK; positive year, nonempty make/model/type, nonnegative known readings. Owner boundary for private child records. |
| `service_records` | `vehicle_id INTEGER`, `service_date DATE`, `service_type TEXT`, `description TEXT`, `mileage NUMERIC(12,1)?`, `operating_hours NUMERIC(12,1)?`, `cost NUMERIC(12,2)?`, `notes TEXT?`, `created_at` | Vehicle FK; type is `maintenance`, `repair`, `inspection`, or `diagnostic`; nonempty description and nonnegative known readings/cost. Historical readings remain independent of current vehicle readings. |
| `maintenance_schedules` | `vehicle_id INTEGER`, `name TEXT`, `interval_days INTEGER?`, `interval_miles NUMERIC(12,1)?`, `interval_hours NUMERIC(12,1)?`, `baseline_date DATE?`, `baseline_mileage NUMERIC(12,1)?`, `baseline_hours NUMERIC(12,1)?`, `source_notes TEXT?`, `created_at` | Vehicle FK; at least one positive interval with its matching baseline. Any configured limit reaching its threshold makes a combined schedule due. |
| `maintenance_completions` | `vehicle_id INTEGER`, `schedule_id INTEGER`, `service_record_id INTEGER`, `created_at` | Composite FKs enforce that schedule and service belong to the same vehicle; unique schedule/service pair. Date, readings, and cost come from the service. Links cascade when a linked schedule or service is deleted. |
| `parts` | `manufacturer TEXT`, `part_number TEXT`, `name TEXT`, `category TEXT` | Shared, initially empty catalog; unique manufacturer/part-number pair. No guessed compatibility data. |
| `part_fitments` | `part_id INTEGER`, `year SMALLINT`, `make TEXT`, `model TEXT`, `engine TEXT`, `configuration_notes TEXT` (default empty), `source_url TEXT`, `verified_on DATE` | Part FK; unique part/configuration tuple. Required identifying fields and source URL are nonempty. Application matching must respect configuration notes and verified sources. |
| `saved_parts` | `vehicle_id INTEGER`, `part_id INTEGER?`, `origin TEXT`, `name TEXT`, `part_number TEXT`, `manufacturer TEXT?`, `notes TEXT?`, `created_at` | Vehicle FK and optional catalog FK. `catalog` origin requires a part ID; `manual` requires none. Unique vehicle/catalog-part pair. |
| `service_parts` | `service_record_id INTEGER`, `part_id INTEGER?`, `name TEXT`, `part_number TEXT?`, `manufacturer TEXT?`, `quantity INTEGER` (default 1), `notes TEXT?` | Service FK with cascade cleanup; optional catalog FK becomes NULL on catalog deletion. Positive quantity. Historical identity fields remain independent of saved-part edits/deletion. |

### Expense view and computed status

`vehicle_expense_summary` groups service records once per vehicle and includes
vehicles without services. It exposes:

- `vehicle_id INTEGER` and `user_id INTEGER` for identity and ownership filtering.
- `service_count BIGINT` for the number of service records.
- `recorded_total_usd NUMERIC` for the sum of known service costs, returning zero
  when there are no known costs.
- `unknown_cost_count BIGINT` to preserve the distinction between unknown and free.

The view is not an authorization boundary. Filter by the authenticated owner.
Do not multiply costs through joins to completion links or service parts, and
do not add part costs separately to a service's total. This is recorded service
spending, not fuel, insurance, depreciation, or full ownership cost.

Maintenance status and reminders are calculated from schedules, applicable
service completions, dates, and available current readings. Missing miles/hours
remain unknown. Do not add stored notification/status records merely to support
the planned dashboard.

### AI report inputs

Feature 13 uses the selected vehicle's verified service, expense, and maintenance
data. Reports are labeled summaries with source links and explicit missing-data
information, not substitutes for stored records. The plans do not specify
persisting generated reports or adding a reports table.

## Tech stack

- **Frontend:** React 19, Vite, JavaScript/JSX, and the existing plain CSS.
  npm uses `frontend/package-lock.json`.
- **Backend:** Python 3.13 and FastAPI; keep application creation separate from
  route handlers. Use the existing `backend/.venv` runtime.
- **Database:** PostgreSQL with direct psycopg access and parameterized SQL.
  Hand-managed SQL is authoritative. No Django, ORM, migration framework, or
  automatic schema creation without an approved architectural change.
- **API boundary:** React calls relative `/api` URLs. Only FastAPI receives
  PostgreSQL credentials and accesses private data.
- **AI integration:** an approved external AI API receives only the necessary
  selected records through FastAPI. Provider credentials stay private.
- **Vehicle data:** manual entry is required. An optional vehicle-data API may
  be evaluated, but the MVP cannot depend on a paid vehicle-data service.
- **Verification:** backend pytest, frontend ESLint and production build, plus
  direct browser evidence where applicable. Exact commands and the test gate
  are in `AGENTS.md`; no frontend unit-test runner or combined Verify/CI command
  is currently configured.

## Monetization

The course MVP is free and contains no payments, subscriptions, or advertising.
Possible post-course funding models include subscriptions/freemium and verified
retailer affiliate links, subject to a separate product decision. User and
vehicle data will not be sold.

## UI/UX

- Practical, clear, vehicle-centered, and responsive on desktop and mobile.
- Main planned flows: registration and sign-in, vehicle selection/readings,
  service timeline and part history, maintenance status/completion, catalog
  search, saved parts, expenses, AI-assisted reports, and garage dashboard.
- Distinguish unknown readings/costs from zero. Explain the interval that causes
  maintenance to be due and avoid presenting incomplete fitments as compatible.
- Preserve accessible keyboard controls, readable status messages, and visible
  loading, unavailable, and retry states from the current foundation.
- `/` currently hosts the connection check. Product screen URLs are not defined
  by the plans; choose them in feature specs rather than assuming routes exist.

## Deployment

Feature 15 delivers a browser-based deployment. Vercel is the tentative frontend
host, with a compatible FastAPI host and managed PostgreSQL provider selected for
project compatibility and available free or educational hosting. Final providers
and deployment details remain undecided.

Current operation is local development, with separate `garageguide_app` and
`garageguide_app_test` databases. Development database verification remains
deferred; this overview does not initialize or verify any database.

| Component | Current command or contract |
| --- | --- |
| Frontend dev | From root: `npm --prefix frontend run dev`; `http://127.0.0.1:5173`; Vite proxies `/api` to FastAPI. |
| Frontend build | From root: `npm --prefix frontend run build`; output `frontend/dist/`. |
| Backend dev | From root: `backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`. |
| Database provisioning | Separate PostgreSQL service and manually applied SQL from `database/`; never create schema during application startup. |
| Private backend environment | `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`; keep values out of frontend bundles and source control. |
| AI provider configuration | Provider and variable names remain undecided; AI credentials belong only in private backend configuration. |
| Health endpoints | `/api/health` for liveness without PostgreSQL; `/api/health/db` for connectivity and expected table/view presence. |
| Background work | No workers or cron required by this plan; reminders are calculated in the app. |

Deployment acceptance includes the complete user journey, persisted records,
HTTPS, rejected missing/expired/revoked sessions, wrong-owner rejection,
responsive interaction, and failure recovery.

> TODO: Finalize production providers, public domain, frontend-to-API routing,
> release process, environment configuration, and deployment-specific commands.

## Open questions

The two plans agree on MVP scope; the Build Plan supplies the fifteen-feature
implementation order. Resolve decisions in the plans or the relevant approved
feature spec; do not silently turn TODOs into requirements.

- **Catalog curation:** decide how verified seed data is entered and maintained
  before catalog search can return useful real fitments. No admin UI or external
  synchronization is authorized by the current plans.
- **Maintenance details:** define upcoming thresholds, completion-baseline
  selection, and behavior when required readings are unavailable during the
  recurring-maintenance and completion specs.
- **Product navigation:** concrete screen routes and detailed product layouts
  are not yet specified. Static prototypes remain optional before UI features.
- **AI provider:** select the approved provider, cost limits, configuration, and
  failure behavior for Feature 13. Keep data selection and access owner-scoped.
- **Deployment and usage:** final hosting, release details, traffic, and
  availability targets remain undecided.
- **Verification wording:** the Build Plan calls database verification completed,
  while `docs/verification/PROJECT_SCAFFOLD_STATUS.md` marks native PostgreSQL
  integration and browser checks pending. Historical PGlite assertions do not
  establish current native application connectivity; clarify this in the source
  plan when it is next reviewed.
