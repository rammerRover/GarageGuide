# Project Plan

## 1. Problem - What problem are we solving?

GarageGuide helps people keep maintenance information for their wheeled
vehicles in one place. Owners can track current mileage or operating hours,
preserve service history, plan recurring maintenance, and keep notes about parts
and costs instead of relying on scattered records or memory. A vehicle may use
miles, hours, or both; missing readings and costs must remain unknown rather
than being treated as zero.

The current application is a technical backbone with a connectivity screen and
health checks, not a finished product. The features below describe the intended
MVP.

## 2. Users - Who is this for?

People managing maintenance for one or more personal vehicles, including cars,
motorcycles, dirt bikes, and other wheeled rides. The initial workflow is for an
individual owner who wants to keep their own garage organized, not a repair
shop or fleet operator.

Each user has a private account and can access only their own vehicles and
associated records. Shared garages, teams, and role-based access are not part
of the MVP.

## 3. Features - What does the MVP need?

- Account registration, sign-in, sign-out, and secure sessions.
- Create and manage vehicles with current mileage and/or operating hours.
- Record dated maintenance, repair, inspection, and diagnostic history.
- Define recurring maintenance intervals and calculate upcoming, due, and
  overdue work.
- Complete maintenance by linking a service record to one or more schedules.
- Search a curated parts catalog and show only verified vehicle fitments.
- Save catalog or manually entered parts to a vehicle.
- Record parts used by a service while preserving a historical snapshot.
- Summarize known service costs per vehicle without counting unknown costs as
  zero.
- Show a garage dashboard with vehicle status, service history, schedules, and
  in-app reminders.

## 4. Data - What are we storing?

- **Users and sessions:** normalized email, password hash, and hashed session
  token with creation, expiry, and revocation timestamps. Never store plaintext
  passwords or raw session tokens.
- **Vehicles:** owner, year, make, model, vehicle type, optional engine, current
  mileage and/or operating hours, and when readings were last updated.
- **Service records:** vehicle, date, service type, description, optional
  readings, optional total cost in USD, and notes. Historical readings describe
  that service and do not change when current vehicle readings change.
- **Maintenance schedules:** vehicle, name, optional day/mile/hour intervals,
  matching date/mileage/hour baselines, and source notes. A schedule may combine
  intervals and becomes due when any configured limit is reached.
- **Maintenance completions:** links between a vehicle's schedule and service
  record. Completion date, readings, and cost come from the service record
  rather than duplicated values.
- **Parts catalog and fitments:** shared part manufacturer, part number, name,
  category, supported year/make/model/engine configuration, configuration
  notes, source URL, and verification date. Incomplete fitment data must not be
  presented as confirmed compatibility.
- **Saved vehicle parts:** either a catalog reference or a manual entry, with
  name, part number, optional manufacturer, and notes.
- **Service parts:** historical snapshots of parts used on a service, including
  optional catalog reference, identifying details, quantity, and notes. Part
  costs are not added separately to the service total.

The PostgreSQL scripts in `database/` are the schema source of truth. Expense
summaries are computed from service-record costs; maintenance status and
reminders are computed from schedules and current readings. The catalog starts
empty, so its initial data-entry and ongoing curation process still needs a
product decision.

## 5. Tech - What stack are we using?

- **Frontend:** React 19 with Vite and JavaScript.
- **Backend:** FastAPI on Python 3.13.
- **Database access:** psycopg with parameterized SQL.
- **Database:** PostgreSQL, defined by the existing hand-managed SQL scripts.
- **Testing:** pytest for the backend and the existing frontend lint/build
  scripts.

There is no ORM or automatic schema creation. Product features are implemented
in the frontend and FastAPI; database ownership checks and validation must be
enforced in application code as well as by database constraints.

## 6. Monetize - How will this make money?

No monetization model has been chosen. Monetization is outside the initial MVP;
do not add subscriptions, advertising, or payment processing without a separate
product decision.

## 7. UI/UX - How should this look and feel?

The interface should feel practical, clear, and vehicle-centered. A user should
be able to select a vehicle, understand its current readings and maintenance
status, review its service timeline, and find its saved parts without confusing
records from different vehicles. Keep forms straightforward and responsive on
desktop and mobile.

Show unknown mileage, hours, or costs distinctly from a real zero. Make due
status and the interval that triggered it understandable. Present a part as
compatible only when its saved fitment data is sufficiently complete and
verified. The current responsive screen is only a connectivity check; the
product screens are future work.

## 8. Deployment - Where and how will this ship?

Production hosting, public domain, and release process have not been selected.
The current setup is local development: Vite serves the frontend on
`127.0.0.1:5173`, proxies `/api` to FastAPI on `127.0.0.1:8000`, and FastAPI
connects to PostgreSQL.

- Frontend build: run `npm run build` in `frontend/`; output is `frontend/dist/`.
- Backend: run `uvicorn app.main:app --app-dir backend` with the backend
  dependencies installed.
- Database: a separately provisioned PostgreSQL database using the SQL in
  `database/`; schema creation is not automatic.
- Backend environment variables: `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`,
  and `PGPASSWORD`. Keep credentials private and never expose them to the
  frontend.
- Health paths: `/api/health` for API liveness and `/api/health/db` for database
  connectivity and expected public tables/views.
- Workers or cron jobs: none are required by the current plan; reminders are
  calculated in the application, not delivered as email or push notifications.

Deployment-specific start commands, environment configuration, hosting
provider, and domain details should be filled in after a target is selected.

## 9. Usage model and constraints

- Expected user count, traffic, availability target, and whether production
  hosting is internet-facing have not been established. Do not design for
  hypothetical scale or claim compliance requirements.
- The data model supports individual accounts, with private owner-scoped
  vehicles and records. There are no organizations, shared garages, or fleet
  workflows in the MVP.
- Authentication and per-vehicle ownership checks are required before private
  records are exposed. Passwords are hashed; only hashes of session tokens are
  stored; sessions use secure cookies, expiry, revocation, and CSRF protection.
- Use parameterized SQL. Database health checks are read-only and must not
  expose credentials, product data, or sensitive database errors.
- Do not add a delete-account workflow, external catalog synchronization,
  email/push notifications, AI-generated reports, or shop/fleet features without
  a separate product decision.
