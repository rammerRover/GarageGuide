-- GarageGuide: full MVP starting PostgreSQL schema (10 tables)
-- Stack: React frontend -> Python/FastAPI backend -> PostgreSQL database.
-- This file only defines the database. It does not implement API routes or login.
--
-- SETUP
-- 1. Create a new, empty database named garageguide in PostgreSQL/pgAdmin.
-- 2. Open the Query Tool connected to that database.
-- 3. Run this entire file once.
-- Use a fresh database for this restart, not the previous eight-table starter.
-- No Docker, ORM, migration framework, extension, or sample data is required.
-- This replaces the earlier starter file; it is NOT an upgrade script for an
-- existing database. Do not delete existing data to apply it; use a migration.

BEGIN;

-- One account can own many vehicles.
CREATE TABLE users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- FastAPI will trim/lowercase emails and validate their format.
    CONSTRAINT users_email_normalized
        CHECK (email = lower(trim(email)) AND email <> '')
);

-- A car may use mileage, a dirt bike may use hours, or a vehicle may use both.
CREATE TABLE vehicles (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    year SMALLINT NOT NULL CHECK (year > 0),
    make TEXT NOT NULL CHECK (trim(make) <> ''),
    model TEXT NOT NULL CHECK (trim(model) <> ''),
    vehicle_type TEXT NOT NULL CHECK (trim(vehicle_type) <> ''),
    engine TEXT,
    mileage NUMERIC(12, 1) CHECK (mileage >= 0),
    operating_hours NUMERIC(12, 1) CHECK (operating_hours >= 0),
    readings_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Each service belongs to one vehicle. Its readings describe that past service,
-- not the vehicle's current readings, so later updates do not rewrite history.
CREATE TABLE service_records (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    service_date DATE NOT NULL,
    service_type TEXT NOT NULL
        CHECK (service_type IN ('maintenance', 'repair', 'inspection', 'diagnostic')),
    description TEXT NOT NULL CHECK (trim(description) <> ''),
    mileage NUMERIC(12, 1) CHECK (mileage >= 0),
    operating_hours NUMERIC(12, 1) CHECK (operating_hours >= 0),
    cost NUMERIC(12, 2) CHECK (cost >= 0),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id, vehicle_id)
);

-- Server-side login sessions: a proposed simple authentication approach.
-- Python generates a random token; only its hash is stored here. The raw token
-- belongs in an HttpOnly cookie. Sign-out revokes the session; expiry is checked
-- by FastAPI on each protected request. SQL alone does not implement login.
CREATE TABLE user_sessions (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    CHECK (expires_at > created_at)
);

-- Recurring work. At least one interval and its matching baseline are required.
-- A combined schedule becomes due when any one limit is reached.
-- Days are calendar days, miles are odometer distance, hours are operating hours.
CREATE TABLE maintenance_schedules (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    name TEXT NOT NULL CHECK (trim(name) <> ''),
    interval_days INTEGER CHECK (interval_days > 0),
    interval_miles NUMERIC(12, 1) CHECK (interval_miles > 0),
    interval_hours NUMERIC(12, 1) CHECK (interval_hours > 0),
    baseline_date DATE,
    baseline_mileage NUMERIC(12, 1) CHECK (baseline_mileage >= 0),
    baseline_hours NUMERIC(12, 1) CHECK (baseline_hours >= 0),
    source_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id, vehicle_id),
    CHECK (interval_days IS NOT NULL OR interval_miles IS NOT NULL OR interval_hours IS NOT NULL),
    CHECK (interval_days IS NULL OR baseline_date IS NOT NULL),
    CHECK (interval_miles IS NULL OR baseline_mileage IS NOT NULL),
    CHECK (interval_hours IS NULL OR baseline_hours IS NOT NULL)
);

-- One service can satisfy multiple schedules, but only once per schedule.
-- Composite foreign keys guarantee both records belong to the same vehicle.
-- Completion date/readings/cost come from the service, avoiding duplicate costs.
CREATE TABLE maintenance_completions (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vehicle_id INTEGER NOT NULL,
    schedule_id INTEGER NOT NULL,
    service_record_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (schedule_id, service_record_id),
    FOREIGN KEY (schedule_id, vehicle_id)
        REFERENCES maintenance_schedules(id, vehicle_id) ON DELETE CASCADE,
    FOREIGN KEY (service_record_id, vehicle_id)
        REFERENCES service_records(id, vehicle_id) ON DELETE CASCADE
);

-- Small shared catalog, initially empty. Do not insert guessed part numbers.
CREATE TABLE parts (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    manufacturer TEXT NOT NULL CHECK (trim(manufacturer) <> ''),
    part_number TEXT NOT NULL CHECK (trim(part_number) <> ''),
    name TEXT NOT NULL CHECK (trim(name) <> ''),
    category TEXT NOT NULL CHECK (trim(category) <> ''),
    UNIQUE (manufacturer, part_number)
);

-- Each row documents one supported configuration, independent of users' cars.
-- The same part can have multiple fitment rows. Python handles search/matching
-- and must not present incomplete configurations as confirmed compatibility.
CREATE TABLE part_fitments (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    part_id INTEGER NOT NULL REFERENCES parts(id),
    year SMALLINT NOT NULL CHECK (year > 0),
    make TEXT NOT NULL CHECK (trim(make) <> ''),
    model TEXT NOT NULL CHECK (trim(model) <> ''),
    engine TEXT NOT NULL CHECK (trim(engine) <> ''),
    configuration_notes TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL CHECK (trim(source_url) <> ''),
    verified_on DATE NOT NULL,
    UNIQUE (part_id, year, make, model, engine, configuration_notes)
);

-- A user's reference list for a vehicle. Manual references need no catalog row.
CREATE TABLE saved_parts (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    part_id INTEGER REFERENCES parts(id),
    origin TEXT NOT NULL CHECK (origin IN ('catalog', 'manual')),
    name TEXT NOT NULL CHECK (trim(name) <> ''),
    part_number TEXT NOT NULL CHECK (trim(part_number) <> ''),
    manufacturer TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (vehicle_id, part_id),
    CHECK ((origin = 'catalog' AND part_id IS NOT NULL)
        OR (origin = 'manual' AND part_id IS NULL))
);

-- Historical snapshots: removing/editing saved_parts never rewrites past work.
-- A service can contain several replacement parts, including manual entries.
-- Cost stays on service_records as the total, so it is counted only once.
CREATE TABLE service_parts (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_record_id INTEGER NOT NULL REFERENCES service_records(id) ON DELETE CASCADE,
    part_id INTEGER REFERENCES parts(id) ON DELETE SET NULL,
    name TEXT NOT NULL CHECK (trim(name) <> ''),
    part_number TEXT,
    manufacturer TEXT,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    notes TEXT
);

-- Support looking up an owner's vehicles and a vehicle's service history.
CREATE INDEX vehicles_user_id_idx ON vehicles(user_id);
CREATE INDEX service_records_vehicle_date_idx
    ON service_records(vehicle_id, service_date DESC);
CREATE INDEX user_sessions_user_id_idx ON user_sessions(user_id);
CREATE INDEX maintenance_schedules_vehicle_id_idx ON maintenance_schedules(vehicle_id);
CREATE INDEX maintenance_completions_service_idx ON maintenance_completions(service_record_id, vehicle_id);
CREATE INDEX part_fitments_configuration_idx ON part_fitments(year, make, model, engine);
CREATE INDEX saved_parts_part_id_idx ON saved_parts(part_id);
CREATE INDEX service_parts_service_record_id_idx ON service_parts(service_record_id);
CREATE INDEX service_parts_part_id_idx ON service_parts(part_id);

COMMIT;

-- STARTING RULES
-- Mileage is in miles; operating_hours is elapsed engine usage.
-- Cost is in USD for the initial version. NULL means unknown; 0 means free.
-- Missing mileage/hours also remain NULL, not an invented zero.
-- password_hash must contain a hash produced by the future authentication code,
-- never a plain-text password. This schema does not hash passwords itself.
-- FastAPI must check vehicle ownership before reading/changing private records.
-- Foreign keys preserve relationships; they do not enforce account permissions.
-- Parent deletion is restricted while child records exist, avoiding accidental
-- deletion of a user's entire history. Completion links, service-part details and
-- sessions have explicit cleanup rules when their parent is removed.
-- No delete-account workflow is added here.
-- Use parameterized database queries in Python, never assembled SQL strings.

-- APPLICATION LOGIC TO ADD IN PYTHON/FASTAPI
-- Registration validates input and hashes passwords; sessions require secure
-- token generation, cookie settings, expiry/revocation checks and CSRF protection.
-- Enforce ownership for each private query through vehicles.user_id.
-- Confirm lower current readings, update readings_updated_at when changed, and
-- preserve historical service readings. Confirm deletion of services/saved parts.
-- Completing maintenance creates/links a service and completion in one transaction.
-- Validate that the service has date/readings for all active schedule intervals.
-- Compute next due from the latest applicable completion or original baseline.
-- Recalculate after service edits/deletion; never store stale computed status.
-- Missing current readings must be reported as unknown, not as up-to-date.
-- Review similarly named schedules and duplicate manual parts before saving.
-- Catalog matching must respect configuration_notes and verified source details.
-- Normalize catalog search keys and validate source URLs in the application.
-- Expenses: SUM(service_records.cost) per vehicle; report unknown costs separately.
-- Aggregate costs before joining parts/completions so joins cannot multiply totals.
-- Dashboard: query vehicles and their related service records and schedules.
-- In-app reminders: calculate upcoming/due/overdue from schedules and current
-- readings/date. A separate notifications table is not needed for this MVP.
-- AI reports: summarize selected-vehicle data through FastAPI; no AI table needed
-- unless saved reports become a requirement. Do not send account credentials.
-- Future schema changes can be tracked with migrations when needed.
