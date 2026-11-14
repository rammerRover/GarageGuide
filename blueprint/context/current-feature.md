# Feature: Create and list vehicles in a digital garage

**From build-plan:** feature 3
**Build attempt:** 1
**Branch:** feature/create-and-list-vehicles-in-a-digital-garage
**Archive:** blueprint/history/features/03-create-and-list-vehicles-in-a-digital-garage.md
**Status:** verified
Implementation Steps 1 through 5 and final builder verification are complete.
Steps 1 through 4 and the user browser evidence are approved. The revised
checkpoint awaits explicit commit approval and required independent review.
Feature 3 is not complete; no passing audit receipt or landing is claimed.

## Goal

Let an authenticated user manually create vehicles and see only their own
vehicles in a small digital garage. Support mileage, operating hours, both, or
neither while preserving the difference between unknown and confirmed zero.

The approved contract is recorded here for review. Writing this specification
does not authorize implementation, branch creation, installation, database
connections, staging, commits, merging, pushing, or deployment.

## In scope

- Authenticated `GET /api/vehicles` and `POST /api/vehicles`.
- Model year, make, model, optional engine, free-text vehicle type, and optional
  current mileage and operating hours using the existing `vehicles` table.
- An owned-vehicle list at `/vehicles` and create form at `/vehicles/new`.
- Server-session ownership, safe validation/errors, existing mutation policy,
  explicit transactions, and exact guarded test cleanup.
- Reusable successful-response session-deadline attachment and client parsing
  with session and request-generation protection.
- Focused automated tests, native PostgreSQL verification, manual browser
  verification in development and production preview, and independent review.
- Correct the reviewed scaffold-era routing, authentication, and frontend-test
  statements in `coding-standards.md`. Those documentation corrections are part
  of this specification review, not evidence of Feature 3 implementation.

## Out of scope

- Feature 4 vehicle detail/edit endpoints and pages, including
  `GET /api/vehicles/{vehicle_id}`, PATCH/PUT, reading corrections, downward
  confirmation, and reading-history changes.
- Vehicle deletion, cascading deletion, uniqueness constraints, server-side
  idempotency, pagination, search, vehicle lookup/decoding services, or type enums.
- Dashboard summaries, services, schedules, parts, expenses, reports, shared
  garages, additional roles, and other future product work.
- ORM, generic repositories, connection pooling, new dependencies, schema
  changes/migrations, automatic schema creation, database initialization, and
  runtime/tool installation.
- Authentication redesign, periodic session requests, automatic mutation
  retries, browser storage of private state, and changes to existing expiration
  or cookie contracts.

## Build loop

1. Review and approve this final specification before `$implement`. Remain on
   `main` during specification review. Implementation must recheck prerequisites
   and create only the frozen feature branch after approval.
2. Follow configured Guided review: `workflow.stepReview: every`. Implement one
   approved step, run its checks, explain every changed file and any limitations,
   and stop for review before the next step. Checkpoint commits are enabled as
   optional offers after approval; no commit is authorized automatically.
3. Include focused logic tests with each logic-bearing step. Keep the application
   working, preserve registration/authentication and both health endpoints, and
   avoid exposing partially assembled vehicle endpoints.
4. Native writes require the explicit opt-in and guards below. Unavailable test
   infrastructure is a reported prerequisite, not permission to initialize it.
   Stop native verification on guard or cleanup failure.
5. Use `$check` for observed behavior and `$check guide` for a manual walkthrough.
   Clearly distinguish instructions, automated tests, native tests, user browser
   observations, and simulations. Never report a guide or source inspection as
   executed browser verification.
6. Ownership and private persisted data are sensitive. Require
   `$audit independent current` at the completed, explicitly approved immutable
   review checkpoint. A passing receipt must bind to its exact HEAD and this
   specification. Audit fixes require approval and fresh affected verification;
   behavior changes require identified repeat browser checks.
7. Stop after the final review packet. `$complete`, archive/reset, staging,
   commits, landing, pushing, and deployment retain their separate approval
   boundaries. Do not begin Feature 4.

## Build steps

- [x] **1. Define vehicle validation and public schemas.**

  Add focused request/response models and a testable current-calendar-year
  provider. Use Python `Decimal`, never binary floating-point for readings.
  Define exact allowed fields, decimal parsing/serialization, Unicode validation,
  and safe field-error vocabulary. Do not add routes or database operations.

  **Acceptance and tests:** Database-free schema tests cover 1886, the injected
  current year plus one, both rejected year boundaries, strict integer years,
  booleans, missing required fields, whitespace/case preservation, blank engine,
  valid non-ASCII text, NUL and invalid Unicode, unknown/ownership/read-only
  fields, each reading combination, null versus zero, decimal precision/range,
  and public serialization. Tests inject the year rather than assuming today's
  year. Run focused tests and the complete database-free backend suite.

  **Done when:** Models accept exactly the approved contract, produce canonical
  one-decimal strings or null without rounding, and the complete database-free
  backend suite passes. Existing endpoints remain unchanged.

  **Observed Step 1 evidence:** Focused vehicle schema tests: 188 passed.
  Complete database-free backend suite: 548 passed, 87 integration tests
  deselected. Both runs reported the existing Starlette/AnyIO deprecation
  warning. Pip check: no broken requirements. Tracked and new-file whitespace
  checks passed. No PostgreSQL connection or native integration test was run.
  Only vehicle schemas/tests were added; no routes, queries, frontend changes,
  or dependencies. Stop for Step 1 review before Step 2.

- [x] **2. Implement owner-scoped queries and guarded vehicle fixtures.**

  Add `vehicle_queries.py` for owned listing and creation only. Assign ownership
  from the trusted actor, parameterize every variable, own short transactions,
  and prepare validated public results before successful commit. Extend existing
  native fixtures and the guarded manual server to reserve and clean exact
  synthetic vehicles before fixture-owned users, including failure paths.
  Preserve session and registration query behavior and read-only health access.

  **Acceptance and tests:** Database-free fake-connection tests prove owner
  parameters on SELECT and INSERT, explicit columns, null/Decimal bindings,
  timestamp expressions, deterministic ordering, transaction ownership, commit
  before returning success, and rollback/close before translated failures.
  Guard tests prove settings rejection and once-per-physical-connection
  `current_database()` verification, including handler and cleanup connections.
  Approved opt-in native tests exercise two users, empty lists, all reading
  combinations, Unicode, identical vehicles, persisted values, database-owned
  timestamps, ownership isolation, and exact cleanup through guarded connections.
  Test setup/assertion failures must still clean their owned vehicles and users.

  **Done when:** Focused and complete database-free tests and pip check pass;
  guarded native query tests pass in `garageguide_app_test`, and exact owned
  vehicle/user/session cleanup is verified. No vehicle HTTP endpoint is exposed.
  If native verification cannot run, report it and stop for review without
  claiming this criterion passed.

  **Observed Step 2 evidence:** Focused database-free query/fixture/guard/manual
  support tests: 85 passed. Complete database-free backend suite: 590 passed,
  96 integration tests deselected. Full guarded native integration suite with
  `RUN_DB_TESTS=1`: 96 passed, 590 database-free tests deselected, including nine
  new vehicle tests and the existing registration, authentication/session,
  concurrency, and health regressions. Every physical native connection used
  the existing settings and first-statement database-name guard for
  `garageguide_app_test`; cleanup finalizers passed with separate guarded
  absence checks. New tests include two-user isolation, all reading combinations,
  identical vehicles, rollback on preparation failure, lost-response recovery,
  and a simulated lost acknowledgment after a real commit. The latter is
  simulation evidence of an uncertain outcome, not a claim that PostgreSQL
  suffered an actual network failure. Pip check found no broken requirements;
  tracked/new-file whitespace checks passed. Runs reported one existing
  Starlette/AnyIO deprecation warning each. Native JUnit evidence is ignored
  local state at `blueprint/.state/staging/feature-3-step-2-native.xml`.
  No HTTP routes, frontend behavior, schema changes, installs, commits, or
  manual browser verification were performed. Stop before Step 3.

- [x] **3. Wire the authenticated API and reusable deadline attachment.**

  Register only the GET and POST collection routes. Reuse the authenticated
  session dependency and existing trusted-Origin/JSON/CSRF helper. Add a focused
  vehicle error boundary with safe vehicle fields/messages, not the
  credential-specific route's email/password whitelist. Add a reusable public
  session-deadline response helper. Do not create detail/edit endpoints.

  **Acceptance and tests:** Database-free API tests cover 200 empty/owned lists,
  201 only after commit, exact public shapes, no ownership input, safe 422,
  invalid JSON/extra fields/Unicode, 401 and cookie deletion, every mutation
  policy rejection before writes, 503 and cookie preservation, unexpected 500,
  no-store headers, committed session-deadline attachment, and redacted logs.
  Test authentication, business-query, response-preparation, and commit failures.
  GET needs no mutation headers; POST accepts ordinary JSON charset parameters.
  Guarded native API tests cover real committed creation/listing, two-account
  isolation, identical submissions creating distinct rows, readings/timestamps,
  and exact cleanup. Run registration, login/session/logout, concurrency, and
  public health regressions within the complete applicable backend suites.

  **Done when:** Focused and complete database-free backend tests, pip check,
  guarded native vehicle API tests, and whitespace checks pass. Responses match
  the contract and cleanup is verified. No React behavior has changed.

  **Observed Step 3 evidence:** Focused database-free vehicle API/query/manual
  support tests: 139 passed, including 89 vehicle API tests. Complete
  database-free backend suite: 681 passed, 139 integration tests deselected.
  Complete guarded native suite with `RUN_DB_TESTS=1`: 139 passed, 681
  database-free tests deselected, zero failures/errors/skips; this includes
  43 new vehicle API cases plus existing registration, authentication/session,
  concurrency, vehicle-query, and health regressions. Native JUnit evidence at
  ignored `blueprint/.state/staging/feature-3-step-3-native.xml` captured 137
  exact-cleanup receipts: 182 tracked synthetic users, 148 sessions, and 21
  vehicles verified absent across the suite. The 43 new API cases captured
  43 cleanup receipts for 86 users, 86 sessions, and 11 vehicles. These are
  tracked-record absence totals, not SQL affected-row counts. Physical
  connections retained the settings and first-statement database-name guards;
  cleanup used separate guarded verification connections. No cleanup failed.
  API evidence covers owned/empty lists, committed creation and deadline
  equality with stored session expiry, all reading combinations, duplicate
  submissions, isolation, sanitized validation, policy denials before writes,
  401 cookie deletion, and safe failures without deadline/cookie issuance.
  Availability, preparation, pre-commit, and lost-acknowledgment failures were
  injected simulations around guarded native operations, not observed database
  outages. Pip check found no broken requirements; tracked/new-file whitespace
  checks passed. Test runs each reported the existing Starlette/AnyIO
  deprecation warning. No frontend changes, browser checks, schema/dependency
  changes, staging, commits, or audit were performed. Stop before Step 4.

- [x] **4. Build the protected garage and creation interface.**

  Add `/vehicles` and `/vehicles/new` with the existing router and one mounted
  `BrowserRouter`. Share real protected route definitions between rendering and
  React Router matching in session navigation. Add navigation from the existing
  Account page; retain existing login destination and connection screen.
  Add reusable deadline parsing/acceptance helpers with session-generation and
  request-generation checks. Do not add detail links, edit controls, or future
  product pages.

  **Acceptance and tests:** Extend the existing Node tests for relative URLs,
  same-origin credentials, mutation headers, request/body/response validation,
  decimal strings, 10-second cancellation, no automatic retry, uncertain POST
  outcomes, deadline parsing, stale requests, logout/account changes, and local
  expiry without network activity. Test actual protected route variants,
  including case, trailing slash, encoding, direct entry/refresh, and history
  state; unrelated paths must not become protected vehicle pages accidentally.
  Session tests must prove that old vehicle data/deadlines cannot restore cleared
  identity or reveal another user's garage, and failed/unavailable revalidation
  gates cached content. Run the complete frontend suite including new test
  files, lint, production build, database-free backend suite, and pip check.

  Perform guarded manual browser checks in development and production preview:
  two-user list isolation; create with miles, hours, both, neither, and zero;
  validation/focus/error clearing; empty/loading/success/unavailable states;
  repeated submission prevention; uncertain timeout followed by checking the
  garage; expired/rejected/unavailable sessions; logout and Back/Forward;
  stale responses and deadline updates; no expiry polling; keyboard operation,
  labels/announcements, 375/768/1440-pixel layouts and 200% zoom. Use only the
  guarded test backend and exact synthetic cleanup. Record simulations as such.

  **Done when:** Automated frontend and backend regressions pass and the browser
  evidence demonstrates the stated behaviors with verified cleanup. If browser
  execution is unavailable, provide precise manual steps and leave browser
  acceptance pending until observations are supplied and reviewed.

  **Observed Step 4 evidence:** Protected `/vehicles` and `/vehicles/new` pages,
  Account navigation, safe vehicle request helpers, string-only reading
  normalization, and generation-bound deadline/data acceptance are implemented.
  New focused frontend tests: 128 passed. The complete six-file Node command
  below passed all 298 tests (zero failures, cancellations, or skips), including
  the original 170 tests and all three new files. Frontend lint,
  production build, complete database-free backend suite (681 passed, 139 native
  tests deselected), pip check, and tracked/new-file whitespace checks passed.
  The build first encountered the existing sandbox esbuild directory-access
  restriction and passed on the approved scoped retry outside the sandbox.
  Node tests report the experimental MockTimers warning; backend tests report
  the existing Starlette/AnyIO deprecation warning. No browser-control tool or
  configured browser harness was available at the implementation handoff, so
  no agent-run browser checks are claimed.
  `docs/verification/BROWSER_CHECKS.md` contains the guarded development/preview
  procedure, including two-user isolation, all reading combinations, failures,
  uncertain writes, deadline updates, stale work, accessibility, and cleanup.
  Browser acceptance was pending at that handoff; the subsequent user report
  and cleanup confirmation below satisfy it. No PostgreSQL connection/native
  suite, backend/schema/dependency
  changes, audit, staging, commit, or later-step work occurred in Step 4.

  **User browser report, November 13, 2026:** Chrome 156.0.8078.73, both Vite
  development and production preview. The user reported protected vehicle
  routes/direct loads/refresh/history; Account navigation; empty/create/cancel
  flows; miles/hours/both/neither/zero with correct null/zero display; GET reload
  after successful POST; repeat-submission prevention; validation, error clearing,
  focus, announcements; two-account isolation; no-store/deadline headers;
  deadline synchronization without an extra authentication request; no idle
  polling; full visible idle clearing without an expiry request/retry; keyboard,
  focus, 375/768/1440-pixel layouts, and 200% zoom. Unavailable/retry,
  rejected-session, uncertain-POST, and stale-response cases were user-performed
  browser simulations, not real PostgreSQL outages. No unreported cases are
  inferred. The user subsequently supplied the exact guarded-backend message:
  `Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.`
  This is user-reported browser-run cleanup, not a new agent-run database check
  or a reuse of prior native cleanup. Together with the recorded automated
  results and browser observations, it satisfies Step 4 acceptance. Step 4 is
  marked complete for review; Step 5 remains unchecked and unauthorized.
  See `docs/verification/VEHICLES_STATUS.md` for the attributed record and
  `BROWSER_CHECKS.md` for the repeatable guide. No test rerun or application edit
  occurred while recording these observations. Stop before Step 5.

- [x] **5. Perform final verification and prepare independent review.**

  Run the complete database-free backend suite, all approved guarded native
  integration tests, exact cleanup verification, complete frontend tests, pip
  check, frontend lint, production build, whitespace checks, and full Git
  status/diff review. Record actual commands/totals and distinguish native,
  automated, manual browser, and simulated evidence in a focused
  `docs/verification/VEHICLES_STATUS.md` and the browser guide.

  **Acceptance and tests:** Review ownership on every query, safe errors,
  transaction ordering, null/zero precision, session-deadline freshness, protected
  routes, secret/private-data handling, exact cleanup, and regressions. Prepare
  an exact file/hash checkpoint proposal and proposed commit message for approval
  before staging or committing. Once that checkpoint is separately approved,
  run `$audit independent current`. Record reviewer-run checks and reused
  evidence accurately, preserve receipts/findings, and do not stale a passing
  receipt with unnecessary specification edits.

  **Done when:** All builder verification checks and cleanup pass, browser
  evidence is accepted, and the complete exact checkpoint review packet is
  prepared. Independent review is a separate mandatory quality gate after the
  approved immutable commit and before `$complete`; it must cover that exact
  HEAD and specification and leave no open/fixed P0 or P1 findings. Completing
  this implementation step does not satisfy or waive that review gate.

  **Follow-up user confirmation:** The user confirmed all manual checks are
  complete, specifically including idle timeout, GET/POST session behavior,
  adding vehicles, and comparing visibility between two accounts. This is
  user-performed evidence supplementing the November 13 browser record, not a
  new agent-run browser check. All five implementation steps are checked;
  required independent review remains pending and is not waived by manual tests.

  **Observed Step 5 verification:** The complete database-free backend suite
  passed 681 tests (139 integration tests deselected); the complete six-file
  frontend Node suite passed 298 tests with zero failures/cancellations/skips;
  pip check, frontend lint, and production build passed. The freshly executed
  full guarded native suite passed 139 tests (681 database-free tests
  deselected), with zero failures/errors/skips. Its 137 exact-cleanup receipts
  verified absence of 182 tracked synthetic users, 148 sessions, and 21
  vehicles, through separate guarded verification connections. Two read-only
  health cases reserved no records. Both settings and first-statement physical
  connection guards retained `garageguide_app_test`; only test configuration
  was loaded. There was no schema initialization or alteration.

  Complete tracked/new-file whitespace and builder diff/status checks passed.
  Builder review covered every owner-scoped query, validation/error path,
  transaction, successful-response deadline attachment, protected route, and
  stale-response guard. No confirmed in-scope blocker was found by this builder
  review; this is not an independent audit or passing receipt. No application
  behavior changed in Step 5, so the approved November 13 user-performed Chrome
  156.0.8078.73 development/preview observations are preserved and reused without
  claiming another browser run. Native and browser failure simulations remain
  separate from real successful database/browser behavior.

  Dependency declarations, lockfiles, SQL/schema, and configuration are
  unchanged. Private environment files stayed ignored/unstaged and their
  internally compared content fingerprints did not change during verification.
  Ignored build output and local verification artifacts were generated, but are
  excluded from the proposed checkpoint. The unrelated `backend/prepapp.txt`
  edit is preserved and excluded. Exact commands, warnings, limitations, flow,
  and evidence are in `docs/verification/VEHICLES_STATUS.md`; the frozen proposal,
  complete inventory with raw hashes/purposes, and full builder diff are under
  ignored `blueprint/.state/staging/feature-3-*` review artifacts. Stop for
  approval of the exact checkpoint before staging, committing, or running
  `$audit independent current`. This implementation verification/preparation
  step is complete; the separate required independent-review gate is pending.

## Files / areas

Specification review changes only:

- `blueprint/context/current-feature.md`: this Feature 3 specification.
- `blueprint/context/coding-standards.md`: narrowly correct existing routing,
  authentication, and frontend testing descriptions.
- No build-plan changes: Feature 3 remains create/list, Feature 4 remains detail/edit.

Expected implementation areas after approval:

- New `backend/app/vehicle_schemas.py`, `backend/app/vehicle_queries.py`, and
  `backend/app/routes/vehicles.py`; router registration in `backend/app/main.py`.
- `backend/app/authentication.py`: small reusable successful-response deadline
  attachment helper. Reuse the existing session dependency and policy rather
  than duplicating session validation or changing its database algorithm.
- Focused new `backend/tests/test_vehicle_schemas.py`,
  `test_vehicle_queries.py`, `test_vehicles.py`, and native vehicle tests;
  existing `conftest.py`, `database_support.py`, guarded manual-server support,
  and their tests where exact ownership/cleanup must expand.
- New focused garage/form React components, such as `VehiclesPage.jsx` and
  `CreateVehiclePage.jsx`; `App.jsx`, `AccountPage.jsx`, `api.js`, session store/
  context, shared protected route definitions, and `styles.css` as needed.
  A small shared route/deadline helper is justified by existing Account and new
  vehicle routes; no generic client/server framework is required.
- Existing frontend Node tests plus focused vehicle-validation/request tests
  where needed. Include every new test file in documented complete commands.
- `README.md`, `docs/verification/BROWSER_CHECKS.md`, and the new vehicle status
  record for actual feature usage and observed verification during implementation.
- No dependency/lockfile, environment configuration, SQL schema, or existing
  archive changes are required. Unexpected need for one is a review decision.

## Data / contracts

### Validation and public vehicle shape

`VehicleCreate` accepts only these fields:

| Field | Input and normalization |
| --- | --- |
| `year` | Required strict JSON integer, inclusive 1886 through backend current calendar year plus one. Reject booleans, numeric strings, and fractional values. Obtain the year from one injectable backend provider using the backend's calendar date, not the browser or an import-time frozen constant. |
| `make` | Required text; trim surrounding whitespace, reject blank, preserve display case. |
| `model` | Required text; trim surrounding whitespace, reject blank, preserve display case. |
| `vehicle_type` | Required free text with the same trim/nonblank/case rules. UI examples such as Car, Motorcycle, Dirt bike, ATV, and RZR are suggestions, not an enum. |
| `engine` | Optional text or null; omission or trimmed blank becomes null; otherwise trim and preserve case. |
| `mileage` | Optional decimal string or null; omission becomes null. Miles, not kilometers. |
| `operating_hours` | Optional decimal string or null; omission becomes null. |

Validate all supplied text as valid Unicode representable in PostgreSQL UTF-8;
reject NUL and unpaired surrogates before database access. Render user text through
normal React text interpolation, never HTML injection. No new text-length limits
or case transformations are introduced. Reject unknown fields, including
`user_id`, `owner_id`, IDs, and timestamps, rather than silently ignoring them.

For readings, trim surrounding string whitespace, accept ASCII digits with an
optional decimal point and one fractional digit, and canonicalize to exactly
one fractional digit. Thus `"12"` becomes `"12.0"`. Reject JSON numbers,
booleans, empty strings, signs, exponents, commas, NaN/infinity, negative values,
more than one fractional digit, and values above `"99999999999.9"`. Never round
or clamp to fit. Blank form controls must map to null before submission, not to
an empty-string reading. Leading zeros may be normalized away.

Both readings may be null. Null means not recorded, not zero and not a stored
declaration that a vehicle cannot track that measurement. `"0.0"` means a
confirmed zero. No measurement-mode column is required.

The exact public `Vehicle` response fields are:

```json
{
  "id": 123,
  "year": 2020,
  "make": "Honda",
  "model": "CRF250R",
  "engine": null,
  "vehicle_type": "Dirt bike",
  "mileage": null,
  "operating_hours": "0.0",
  "readings_updated_at": "2026-11-13T18:00:00Z",
  "created_at": "2026-11-13T18:00:00Z"
}
```

IDs are positive database-generated integers; timestamps are timezone-aware ISO
8601 values. `created_at` comes from PostgreSQL. On creation,
`readings_updated_at` is PostgreSQL-generated time when either reading is known,
including zero, and null when both are unknown. Do not accept either timestamp
from the client. Public output omits `user_id`, credentials, hashes, and session
identifiers. Read models must not reject existing stored vehicles solely because
their year falls outside today's narrower create-time policy; SQL permits older
or future rows and this feature does not rewrite them.

The SQL source already provides an identity key, user FK, `SMALLINT` year,
required nonblank make/model/type, optional engine, nonnegative nullable
`NUMERIC(12,1)` readings, timestamp columns, and an ownership index. The narrower
create-time year policy is application validation; no migration is needed.
Identical vehicle descriptions are allowed and create distinct rows. No service
history or other child records are touched.

### Authentication, ownership, and transactions

- Derive identity only from `require_authenticated_session`. Do not accept an
  owner via JSON, query parameters, headers, or router state.
- The dependency's existing atomic session validation/extension commits before
  returning trusted identity. Preserve row-lock ordering, strict expiration,
  revocation, idle/absolute limits, and existing cookies. Business transactions
  are separate short transactions: a later vehicle failure does not undo a
  previously committed session extension.
- List with explicit public columns and `WHERE user_id = %s`, binding only the
  authenticated user's ID. Order by `created_at DESC, id DESC`. Use a read-only
  business connection/transaction; authentication itself can still extend idle
  expiry. An empty result is an ordinary successful list.
- Create with explicit columns and parameterized values, assigning `user_id`
  from the actor. Bind `Decimal` or null for readings and use PostgreSQL time
  for reading timestamps. Use `RETURNING` for public columns.
- Prepare and validate the public result inside the owned transaction before
  commit; return 201 only after successful commit and connection cleanup.
  Response-preparation or commit failure rolls back where possible and closes
  before translating errors. A lost connection at commit can leave the client
  uncertain; do not promise rollback if the server may already have committed.
- No global ID-existence probe, unscoped list, owner override, background writes,
  generic repository layer, or automatic schema setup. Feature 3 has no
  vehicle-ID endpoint through which another owner's existence can be disclosed.

### API and errors

| Request | Success | Requirements |
| --- | --- | --- |
| `GET /api/vehicles` | 200, exactly `{"vehicles": [Vehicle, ...]}` | Valid server session; owned vehicles only; no mutation headers required. |
| `POST /api/vehicles` | 201, exactly one `Vehicle` | Valid server session plus existing exact trusted Origin, `application/json` with ordinary charset parameters allowed, and `X-GarageGuide-CSRF: 1`. |

Use relative URLs and `credentials: 'same-origin'`. Add no permissive CORS.
Reuse approved local/preview/production origins and cookie transport validation.
Policy rejection must occur before business writes. No new login, cookie, or
session token is created by a vehicle request.

Every vehicle response, including errors, has `Cache-Control: no-store`.
Successful authenticated 200/201 responses also carry
`X-GarageGuide-Session-Expires-At`, a timezone-aware ISO 8601 value from the
validated, committed server session. It is public deadline metadata, not an
authentication credential. Attach it through a reusable helper, not repeated
vehicle-specific timestamp/header logic. Never derive a fresh deadline in React.

| Failure | Fixed behavior |
| --- | --- |
| Invalid data or JSON | 422, `{"detail": [{"loc": ["body", "field"], "msg": "safe fixed message", "type": "safe fixed type"}]}`. Only approved fields may appear in locations; use `["body"]` for object/JSON/unknown-field errors. No raw input, `ctx`, arbitrary exception text, or unexpected field names. |
| Missing/malformed/unknown/expired/revoked session | Existing 401 `{"detail":"Not authenticated."}` and matching unusable-cookie deletion. Clear/gate private client data. |
| Mutation-policy rejection | 403 `{"detail":"Request not allowed."}` before business writes. No automatic retry. |
| Session dependency/database unavailable | Existing 503 `{"detail":"Authentication unavailable. Please try again."}`; preserve potentially valid cookie. |
| Vehicle database unavailable | 503 `{"detail":"Vehicles unavailable. Please try again."}`; preserve cookie. Treat existing connection/interface/statement-timeout classes consistently. |
| Unexpected failure | 500 `{"detail":"Internal server error"}`; safe fixed logging only. |

Validation messages must identify the relevant approved constraint without
echoing the value: required/nonblank text, valid Unicode, integer year within
the computed range, or nonnegative one-decimal reading within its storage range.
The frontend must accept only the reviewed safe error shape and field vocabulary.
Expected valid-shaped requests must not disclose SQL, driver details, request
bodies, private vehicle values, passwords, hashes, cookies, or tokens in logs or
errors. Avoid exception tracebacks that contain such data. Preserve existing
auth and registration validation redaction rather than broadening it unsafely.

No duplicate-vehicle 409 exists. Two deliberate identical submissions create two
vehicles. Pending UI protection limits accidental repeats; it does not provide
server-side exactly-once semantics. A timeout/network loss, malformed success,
or lost commit acknowledgment may hide a completed POST. Show safe uncertainty
feedback and a route to check the garage before explicitly resubmitting. Never
retry POST automatically or claim an uncertain request definitely failed.

No detail/update/delete contracts are implemented here. Unknown application
paths use existing safe not-found behavior, without exposing vehicle existence.

### Session deadline and private client-state lifecycle

- Use reusable header parsing and session-store acceptance helpers. Capture an
  opaque in-memory authentication generation and request/navigation generation
  when starting authenticated vehicle work. User ID equality alone is not enough:
  logging out and back in as the same user must invalidate old responses too.
- Accept public vehicle data and its returned deadline only when the request is
  still current, not aborted, belongs to the current authenticated generation,
  and the current route/session gate permits it. New login/logout, rejected
  session, local expiry, protected-route revalidation, departure, or superseding
  work must invalidate old acceptance. Coordinate metadata with that generation;
  do not let it create a guest-to-authenticated transition.
- Parse and validate the successful header as an aware timestamp. Missing or
  malformed metadata is an unexpected response, not permission to fabricate an
  extension. A stale or out-of-order response must not overwrite a newer accepted
  deadline. A deadline already reached cannot renew identity; use the existing
  safe session-ended behavior. Never restore private data cleared by expiry.
- Successful current requests can update the existing local deadline timer from
  the committed server value without issuing an extra session GET. Error headers
  cannot extend it. PostgreSQL remains authoritative for actual validity.
- At local deadline equality, immediately gate/clear public identity and vehicle
  data. The timer never requests `/api/auth/session`, polls, retries, or extends
  idle activity. Only startup/refresh, deliberate protected navigation,
  visibility return, or explicit retry may validate again.
- Abort/ignore stale work on route changes, logout, identity changes, and expiry.
  Authentication unavailable gates private pages and cached vehicle data even
  if a potentially valid cookie remains. Vehicle-only unavailable states may
  retain the authenticated shell, but must not show a different user's data.
- Keep private vehicle responses and public user/session data in transient React
  memory only. No browser storage, URLs containing vehicle form values, logs,
  telemetry, token exposure, or router-state caches of private results.

### React behavior

- `/vehicles`: protected list of basic vehicle summaries with both units labeled;
  unknown readings display `Not recorded`, confirmed zero displays `0.0`.
  Include empty-state and ordinary Add vehicle navigation. Do not render fake
  cards, detail/edit links, future summaries, or maintenance information.
- `/vehicles/new`: protected labeled year/make/model/type/engine/mileage/hours
  form, optional/unknown guidance, free-text type examples, Save vehicle and
  Cancel/Back to garage. Year is manually entered with no presumed vehicle year.
  Use decimal-capable string inputs without JavaScript float conversion; backend
  validation is authoritative. Cancel does not write.
- Success clears the submitted form and navigates to the freshly loaded garage
  with a safe announced confirmation, not a second POST. A failed list reload
  after confirmed 201 must not be described as a failed creation.
- Preserve correctable inputs on validation or transient request failure; clear
  private form/list state on logout, session end, ownership change, or departure
  from the form. No automatic replay after login or reconnecting.
- Provide explicit loading, empty, success, validation, forbidden, unauthenticated,
  unavailable, timeout/network, and unexpected-response states. GET retry is an
  explicit user action, bounded by the existing 10-second request limit. Disable
  repeat submission while pending with an immediate in-flight guard.
- Use associated labels/errors, visible keyboard focus, a focused error summary
  or first invalid field after rejection, error clearing when that field changes,
  status announcements, and focus on destination heading after navigation.
  Render submitted text safely and preserve readable layouts at the tested sizes.
- Use `Routes`, `Route`, and `Link`. Share actual protected Account and vehicle
  route definitions with `matchRoutes`; preserve decoded/case/trailing-slash and
  Back/Forward protection. Malformed paths must not crash React or accidentally
  match a private page; distinguish Vite HTTP-boundary observations from React
  tests. Keep `/`, `/register`, `/login`, and `/account` behavior available.

## Testing

No verification command or database connection is run by writing this
specification. The repository has no combined Verify or configured browser-test
command. Use the installed runners only; do not install tooling incidentally.

Required implementation commands from the repository root:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pip check
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js
npm --prefix frontend run lint
npm --prefix frontend run build
git diff --check
git status --short
```

Extend the explicit Node test command to include all new feature test files and
record the final complete command in the verification record. Focused commands
do not replace complete-suite runs at the relevant review gates.

Native verification is separately opt-in:

```powershell
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider
```

- Load only `backend/.env.test`. Never fall back to development credentials.
- Require the effective database to equal `garageguide_app_test` before connect.
  Immediately on each physical native connection, verify
  `SELECT current_database()` once as its first SQL statement before exposing
  it or allowing writes. Include handler, fixture, and cleanup connections; do
  not repeat this query before every statement. Health stays read-only.
- Register exact cleanup ownership before writes. Track exact unique synthetic
  users, their sessions, and vehicle identities. Arrange recovery for uncertain
  create outcomes using only fixture-owned users and exact reserved synthetic
  markers, never global/prefix-wide deletion or an ordinary user's data.
- Delete fixture-owned vehicles before their users; target exact IDs plus
  fixture-owned user IDs. Delete exact owned sessions as required. Verify all
  reserved records absent through guarded connections even after test failure.
  Extend manual server restrictions so only its reserved test owners can create
  vehicles and its final cleanup includes them. Do not broaden general test-user
  cleanup to delete arbitrary pre-existing vehicles.
- No truncation, broad deletion, sequence resets, schema scripts, initialization,
  or writes to `garageguide_app`, `postgres`, or any other database. Failed cleanup
  stops native verification and is a blocker, not a warning to waive.
- Two-user native tests prove neither user's list includes the other's vehicles,
  an unauthenticated request cannot create/list, and supplied ownership fields
  never redirect assignment. Test all reading combinations and exact storage.

Browser checks use the guarded test backend only and require verified exact
cleanup. Do not enter real account/vehicle data. Keep screenshots free of
credentials/tokens/private identifiers. If browser execution is user-performed,
record the supplied date/browser/environment and attribute the observations to
the user. Mark unavailable browser checks pending and separate simulated 401,
403, 503, timeouts, and malformed responses from native database behavior.

Final review records every changed/untracked file, commands and complete totals,
native database/cleanup evidence, browser observations, limitations, ignored and
unstaged private environment files, branch/status, proposed checkpoint message,
and the complete React to FastAPI to psycopg to PostgreSQL flow. Do not claim
old evidence covers behavior changed by a repair; name required repeat checks.

## Notes for the AI

- Preserve Feature 1 and Feature 2 contracts and archives. The existing SQL files
  remain the source of truth; no dependency or schema change is approved.
- Current prerequisites were verified on clean `main` at
  `46128d31c7e3d928636668804bad4a6ce74c1b9a`, also present on `origin/main`,
  before this documentation work. Features 1 and 2 are archived and checked;
  Feature 3 is unchecked. Build attempt 1 has no prior selected archive record,
  the frozen archive leaf is absent with ordinary directory parents, its Git
  history is unused, and the frozen branch has no conflicting local ref.
- Recheck prerequisites when implementation is approved. Do not create the
  branch, connect to PostgreSQL, or implement from specification approval alone
  unless the user actually authorizes `$implement` and its step scope.
- No edits to project-plan/build-plan are needed: the approved feature boundary
  is unchanged. Leave Feature 4 detail/edit for its own review.
- Reuse the existing validated actor, request policy, safe cookie/error handling,
  direct psycopg connection helpers, Node tests, and exact native fixture guards.
  Add only the small vehicle and deadline helpers required by this contract.
- The list is intentionally unpaginated for the current small garage. Duplicate
  descriptions and uncertain POST outcomes are documented limitations, not
  reasons to add deduplication, idempotency storage, or speculative abstractions.
- The final specification, Steps 1 through 4, and the user-attributed browser
  evidence were approved; Step 5 verification/checkpoint preparation was
  authorized. Stop for exact checkpoint staging/commit approval. Independent
  review must target that later approved immutable HEAD. Do not edit the frozen
  specification merely to record a later receipt. No `$complete` or landing is
  authorized.
