# GarageGuide - Project Overview

<!-- blueprint:source-hash b98fa8086c6c38cfa6cd934b2adc822d4173eb65b820a4ec076e54bf340e0fee -->

> Maintenance records, recurring work, parts, and recorded service costs for a
> personal garage of vehicles using miles, operating hours, or both.

Generated from `blueprint/project-plan.md` and `blueprint/build-plan.md`.
Change those plans and rerun `/overview` when product decisions change. The
existing SQL in `database/` is authoritative for schema fields and constraints.

## Problem

Vehicle owners otherwise rely on scattered records or memory to track service,
parts, costs, and recurring maintenance. GarageGuide keeps that information
together per vehicle, preserves historical readings, and distinguishes unknown
values from real zeroes.

## Users

- Individuals maintaining one or more personal cars, motorcycles, dirt bikes,
  or other wheeled vehicles.
- Each account can access only its own vehicles and associated records.
- Repair shops, fleet operators, organizations, shared garages, and team roles
  are outside the MVP.

## Usage model

- Private owner-scoped data requires authentication and ownership checks in
  FastAPI. SQL relationships alone do not authorize requests.
- Hash passwords and session tokens. Sessions require secure cookies, expiry,
  revocation, and CSRF protection. Never persist plaintext passwords or raw
  session tokens.
- Use parameterized SQL. Health checks remain read-only and expose neither
  product records nor credentials or sensitive database errors.
- User count, traffic, availability targets, and production internet exposure
  are undecided. Do not infer scale or compliance requirements.
- Exclude monetization, account deletion, external catalog synchronization,
  email/push notifications, AI reports, and shop/fleet workflows unless a
  separate product decision changes the plans.

## Features

**Existing foundation:** the responsive connection-status screen, FastAPI
health endpoints, and PostgreSQL schema/view scripts. These are pre-build
foundation, not completed product features. All ten items below remain planned.

The main workflow is owner-scoped vehicle maintenance: select a vehicle, record
service, and understand recurring work. Preserve this build-plan order and IDs:

1. **Accounts and sessions** - registration, sign-in, sign-out, and secure private sessions.
2. **Vehicles** - manage vehicles and current mileage and/or operating hours.
3. **Service history** - record and review dated service history per vehicle.
4. **Recurring maintenance** - define schedules and calculate upcoming, due, and overdue work.
5. **Maintenance completion** - link a service record to one or more schedules.
6. **Catalog search and fitment** - search curated parts and show only verified vehicle fitments.
7. **Saved vehicle parts** - save catalog references or manual part entries.
8. **Service part history** - preserve identifying details of parts used during a service.
9. **Service expenses** - summarize known costs per vehicle and distinguish unknown costs.
10. **Garage dashboard** - show vehicle readings, service history, maintenance status, and calculated in-app reminders.

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

## Tech stack

- **Frontend:** React 19, Vite, JavaScript/JSX, and the existing plain CSS.
  npm uses `frontend/package-lock.json`.
- **Backend:** Python 3.13 and FastAPI; keep application creation separate from
  route handlers. Use the existing `backend/.venv` runtime.
- **Database:** PostgreSQL with direct psycopg access and parameterized SQL.
  Hand-managed SQL is authoritative; there is no ORM or automatic schema setup.
- **API boundary:** React calls relative `/api` URLs. Only FastAPI receives
  PostgreSQL credentials and accesses private data.
- **Verification:** backend pytest, frontend ESLint and production build, plus
  direct browser evidence where applicable. Exact commands and the test gate
  are in `AGENTS.md`; no frontend unit-test runner or combined Verify/CI command
  is currently configured.

## Monetization

Outside the initial MVP. No subscriptions, advertising, or payments are planned
without a separate product decision.

## UI/UX

- Practical, clear, vehicle-centered, and responsive on desktop and mobile.
- Main planned flows: vehicle selection/readings, service timeline, maintenance
  status and completion, catalog search, saved parts, and expenses/dashboard.
- Distinguish unknown readings/costs from zero. Explain the interval that causes
  maintenance to be due and avoid presenting incomplete fitments as compatible.
- Preserve accessible keyboard controls, readable status messages, and visible
  loading, unavailable, and retry states from the current foundation.
- `/` currently hosts the connection check. Product screen URLs are not defined
  by the plans; choose them in feature specs rather than assuming routes exist.

## Deployment

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
| Health endpoints | `/api/health` for liveness without PostgreSQL; `/api/health/db` for connectivity and expected table/view presence. |
| Background work | No workers or cron required by this plan; reminders are calculated in the app. |

> TODO: Select production hosting, public domain, release process, provider
> environment configuration, and deployment-specific commands.

## Open questions

The two plans agree on scope and build order. Resolve decisions in the plans or
the relevant approved feature spec; do not silently turn TODOs into requirements.

- **Catalog curation:** decide how verified seed data is entered and maintained
  before catalog search can return useful real fitments. No admin UI or external
  synchronization is authorized by the current plans.
- **Maintenance details:** define upcoming thresholds, completion-baseline
  selection, and behavior when required readings are unavailable during the
  recurring-maintenance and completion specs.
- **Product navigation:** concrete screen routes and detailed product layouts
  are not yet specified. Static prototypes remain optional before UI features.
- **Deployment and usage:** hosting, release details, traffic, availability
  targets, and internet exposure remain undecided.
