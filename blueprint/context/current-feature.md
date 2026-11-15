# Feature: View and update a vehicle profile

**From build-plan:** feature 4
**Build attempt:** 1
**Branch:** feature/view-and-update-a-vehicle-profile
**Archive:** blueprint/history/features/04-view-and-update-a-vehicle-profile.md
**Status:** verified

The final specification was approved on November 14, 2026. Steps 1-5 were approved,
including the user's November 14 browser observations and exact cleanup report.
Step 6 final verification and builder review passed. The verified specification
and evidence are frozen for the exact checkpoint proposal; checkpoint approval
and a fresh independent audit are pending. Step 6 remains unchecked because its
full done-when includes that later audit. No independent review has run yet.
No staging, commit, audit, completion, merge, push, or deployment is authorized.

## Goal

Let an authenticated owner open a vehicle from the garage, inspect its current
profile, and deliberately correct its details and readings. Protect ownership,
distinguish unknown from confirmed zero, and require fresh acknowledgment before
lowering or clearing a known reading. Never rewrite historical service readings
or maintenance baselines.

Planning baseline: local main and origin/main were both
`683e1933a77f7ba056811dbdc7bd97d16374ebc8`, the completed Feature 3 HEAD. The tree
and index were clean, Features 1-3 were archived and checked complete, Feature 4
was unchecked, and the three live context files were canonical stubs. The
Feature 4 archive path was absent with ordinary directory parents, no prior
Feature 4 build/archive use was found in available history, and the proposed
branch had no local ref or namespace conflict. Build attempt 1 is frozen.
Recheck these prerequisites before separately approved implementation.

## In scope

- Authenticated `GET /api/vehicles/{vehicle_id}` and
  `PATCH /api/vehicles/{vehicle_id}` only, extending the existing vehicle router.
- Strict canonical vehicle IDs; owner-scoped detail reads and updates.
- Partial updates of year, make, model, vehicle type, optional engine, mileage,
  and operating hours, with explicit omission/null/no-op behavior.
- Request-only `reading_confirmation` metadata and an owned-reading 409 contract.
- Locked comparison, atomic changes, exact reading timestamps, and safe errors.
- One protected `/vehicles/:vehicleId` detail/edit page and garage links to it.
- Existing authenticated-request, response-deadline, private-state, and route
  protection helpers, extended only where this feature requires it.
- Focused automated tests, guarded native PostgreSQL verification, manual
  development/preview browser verification, and durable Feature 4 evidence.

## Out of scope

- DELETE, vehicle ownership transfers, shared garages, and bulk changes.
- Service-record functionality, schedules, parts, expenses, dashboard summaries,
  reports, AI, and every later build-plan feature.
- Updates to historical service readings, maintenance baselines, creation time,
  IDs, ownership, or session records through the vehicle business queries.
- Schema changes, migrations, version columns, automatic schema creation,
  Django, ORMs, new dependencies, new test runners, or connection pooling.
- Optimistic locking, server-side idempotency, automatic PATCH retries, polling,
  background renewal, change history, and correction-reason storage.
- Unrelated overview, planning, dependency, lockfile, configuration, or scaffold
  cleanup. Existing verification and Feature 1-3 archive evidence stays intact.

## Build loop

- Use the installed Codex commands `$implement`, `$check`, `$audit`, and
  `$complete` in user-facing instructions.
- Follow configured Guided review: `workflow.stepReview: every`. Implement only
  the next explicitly approved step, run its applicable checks, explain each
  changed file in plain English, and stop for review before the next step.
- Checkpoint offers are enabled, but no stage or commit is authorized without
  approval of the exact checkpoint. Do not create the frozen branch until final
  specification and implementation approval; do not substitute another branch.
- Database-free steps must not connect to PostgreSQL. Native testing is a
  separate, explicit step authorization subject to all guards below.
- Ownership and persisted-data updates are sensitive. A fresh independent
  `$audit independent current` is required against an explicitly approved
  immutable checkpoint and the final verified specification. The builder must
  not self-review or automatically accept/apply findings.
- Complete verification and user-browser records before freezing the final
  checkpoint. Obtain explicit checkpoint commit approval, then audit that exact
  HEAD. Record reviewer-run and reused evidence separately. Do not rewrite
  specification/status bytes after passing review merely to record its outcome.
- `$complete` is separate and requires later authorization. Completion commits,
  landing, pushes, branch deletion, deployment, and Feature 5 are not authorized
  by this specification.

## Build steps

- [x] 1. Define detail/PATCH validation and confirmation schemas.

  Extend the focused vehicle schema module and reuse the existing text, Decimal,
  year-provider, serialization, and public read model. Add canonical ID parsing,
  a PATCH model that preserves supplied-field identity, and strict request-only
  confirmation metadata. Keep the comparison/confirmation decision testable as
  focused pure logic against an explicitly supplied current snapshot; the live
  query must invoke it again using the locked database row.

  **Acceptance and tests:**
  - Accept ID boundaries 1 and 2147483647. Reject leading zeroes, signs,
    fractions, whitespace, non-ASCII digits, zero, negatives, nonnumeric values,
    and overflow without echoing input. Inspect decoded path text before integer
    coercion can erase a forbidden representation.
  - Distinguish omitted fields from explicit null. Reject required-field nulls,
    empty objects, confirmation-only objects, ownership/read-only/extra fields,
    invalid JSON shapes, unsafe Unicode, and NUL.
  - Verify trimmed nonblank case-preserving text, blank/null engine clearing,
    every reading combination, canonical one-decimal serialization, decimal
    bounds, and no binary floating-point or rounding.
  - Inject the backend year provider: accept 1886 and current year plus one;
    reject both outside boundaries, booleans, strings, fractions, and explicit
    null. An omitted legacy year must not be validated as a new supplied year.
  - Preserve the existing public read-year range, including legacy rows outside
    the current create/PATCH-year policy.
  - Cover lower/clear confirmation, zero-to-null, unknown-to-known, equal values,
    stale acknowledgments, both readings, malformed confirmation objects, and
    whole-request rejection without partial changes.

  Run focused schema tests, the complete database-free backend suite, pip check,
  and whitespace checks. No routes, live queries, native tests, frontend work,
  dependencies, or branch-independent code changes in this step.

  **Done when:** Database-free tests prove the exact request/public contract and
  omission/null/confirmation rules, existing create/read behavior remains green,
  and the step has been presented for review.

  **Step 1 evidence - November 14, 2026:** Implemented only schemas, canonical
  ID validation, pure confirmation comparison, and focused database-free tests.
  The original approved specification is preserved byte-for-byte in ignored
  local state; its contracts remain unchanged apart from progress metadata.
  Focused vehicle schema command: 452 passed, one existing Starlette/AnyIO
  deprecation warning. Complete database-free backend suite: 945 passed,
  139 integration tests deselected, the same one warning. Pip check reported
  no broken requirements. Tracked/new-file whitespace checks passed. Native
  tests were not run, PostgreSQL was not contacted, and no query, route,
  frontend, dependency, or schema was added. No staging or commit occurred.
  At that handoff Step 2 was unstarted; it was subsequently authorized separately.

- [x] 2. Add owner-scoped detail/update queries and guarded fixture support.

  Extend `vehicle_queries.py` with detail lookup and partial update only. Reuse
  direct parameterized psycopg and public columns. GET uses a read-only business
  transaction; PATCH locks and re-reads the owner-scoped row, performs every
  comparison/acknowledgment check under the lock, and merges omitted fields from
  that snapshot. Keep transaction ownership explicit and short.

  Extend existing guarded fixture/manual-server support only as necessary to
  permit editing exact fixture-owned vehicles. Track vehicle ID plus fixture
  owner before updates; cleanup must not rely on mutable original descriptions
  or readings. Preserve the first-statement guard on each physical connection.

  **Acceptance and tests:**
  - Assert both ID and trusted actor ID are bound on each detail SELECT,
    `SELECT ... FOR UPDATE`, and UPDATE; no unscoped existence lookup or browser
    owner is accepted. Use explicit columns and only bound variable values.
  - Missing and foreign-owned rows raise the same safe not-found outcome without
    returning another owner's data or issuing an unscoped follow-up query.
  - Verify lock-before-compare ordering, latest-row merge, Decimal/null bindings,
    all-or-nothing confirmation, preserved creation time/owner, and public-only
    `RETURNING` fields.
  - Use `clock_timestamp()` only for actual reading changes. Text-only edits,
    equal normalized readings, and valid no-op PATCHes preserve the timestamp;
    clearing the final known reading records the change time.
  - Validate public results and prepare the response before commit. Return only
    after commit and closure. Cover preparation/query/commit/rollback/closure
    failures and the documented uncertain-commit case without exposing details.
  - Native tests prove detail/update isolation for two fixture owners, successful
    persistence, stale acknowledgment rejection after waiting, and merged omitted
    fields. Use two physical guarded connections, synchronization events, and
    PostgreSQL blocking evidence; never rely only on sleep timing.
  - Exercise both reading fields and stale confirmations whose proposals are no
    longer decreases. Verify no business field/timestamp changes on a 409.
  - Assert production SQL does not mutate service records or schedules. Do not
    introduce service/schedule application logic or broad cleanup to prove this.
  - Register exact cleanup before writes, prove edited vehicles are still
    removed before users, and verify absence through separate guarded connections
    even after setup failures or simulated lost acknowledgments.

  Run focused database-free query/fixture tests, the complete database-free
  backend suite, pip check, approved guarded native query tests and applicable
  existing regressions, exact cleanup verification, and whitespace checks.
  Native execution requires its separate explicit implementation-step approval.

  **Done when:** SQL/transaction tests and authorized native locking/isolation
  tests pass with verified exact cleanup, no schema/application-route changes
  exist, and the step has been presented for review.

  **Step 2 evidence - November 14, 2026:** Added only owned detail/update queries,
  exact fixture-ID guards/manual-query wrappers, and their tests. Detail queries
  use a read-only owned transaction. Updates lock with both IDs, compare the
  freshly locked readings, merge omitted raw stored fields, and prepare public
  responses before commit/closure. No API route or frontend change was made.

  Fresh results: focused query/fixture/database-access tests 159 passed; complete
  database-free backend suite 1025 passed with 174 integration cases deselected;
  complete authorized native suite 174 passed with 1025 database-free cases
  deselected. Native results comprise 35 new Step 2 profile-query cases and all
  139 existing native regressions. No failures, errors, or skipped selected tests.
  Each pytest run emitted the existing Starlette/AnyIO BlockingPortal deprecation.
  Pip check reported no broken requirements; tracked and new-file whitespace
  checks passed. No application/database schema/dependency configuration changed.

  Native settings loaded only `.env.test`, required `RUN_DB_TESTS=1` and effective
  `garageguide_app_test`, and verified `SELECT current_database()` first on each
  physical connection. Fixture finalizers produced 172 exact-cleanup receipts:
  252 tracked users, 218 sessions, and 59 vehicles verified absent through separate
  guarded connections. The two read-only health cases reserved no records.
  The 35 new cases contributed 35 receipts for 70 users, 70 sessions, 38 vehicles.
  Counts mean tracked absence, not affected DELETE rows. Edited vehicle cleanup
  used exact registered IDs/owners, independent of changed descriptions/readings.
  No cleanup failure occurred. No connection or write targeted another database.

  Real PostgreSQL evidence includes row-lock waits confirmed with
  `pg_blocking_pids`, stale acknowledgments after waiting (including newly
  non-dangerous proposals), latest omitted-field merges, post-lock clock sampling,
  and a test-local real lock timeout. Preparation and lost-commit-acknowledgment
  failures were explicitly injected simulations, not real outages. Native tests
  verified rollback before commit and a truly committed update after simulated
  acknowledgment loss, with no retry and verified cleanup. No browser run occurred.

  Commands actually executed from the repository root (native execution alone
  used explicit opt-in, with the previous environment value restored afterward):

  ```powershell
  backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_vehicle_profile_queries.py backend/tests/test_vehicle_queries.py backend/tests/test_vehicle_fixture_safety.py backend/tests/test_manual_registration_server.py backend/tests/test_database_access.py -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-4-step-2/focused.xml --tb=short
  backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-4-step-2/backend.xml --tb=short
  backend/.venv/Scripts/python.exe -m pip check
  # RUN_DB_TESTS=1; settings guard passed before native execution.
  backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-4-step-2/native.xml -o junit_logging=all -o junit_log_passing_tests=true --tb=short
  git diff --check
  ```

  Exact JUnit evidence and cleanup aggregation are retained under ignored
  `blueprint/.state/staging/feature-4-step-2/`. The approved original specification
  and prior feature evidence remain preserved. Nothing was staged or committed.
  At that handoff Step 3 was unstarted; it was subsequently authorized separately.

- [x] 3. Expose authenticated detail/PATCH APIs with safe boundaries.

  Extend the already registered vehicle router, reusing
  `require_authenticated_session`, query functions, response preparation, and
  `attach_session_deadline`. Extend the existing POST mutation-policy boundary
  to PATCH without weakening POST. Add vehicle-specific ID/PATCH/confirmation
  error handling; do not broaden credential-validation whitelists.

  **Acceptance and tests:**
  - Register GET/PATCH detail endpoints only; preserve GET/POST collection APIs,
    both public health endpoints, registration, login/session/logout, and cookie
    behavior. Do not add detail PUT or DELETE behavior.
  - Verify exact public 200 shapes, canonical ID rejection, existing legacy-year
    reads, unrelated edits with omitted legacy year, and all omission/null/no-op
    rules. Missing/foreign responses are indistinguishable in status/body/header
    policy and expose no existence indicator.
  - Cover the complete correction/clear acknowledgment exchange, fresh and stale
    confirmations, both-field atomic rejection, and empty-required-fields 409s
    after a stale acknowledgment ceases to describe a decrease.
  - Test every mutation-policy rejection before vehicle business writes: absent,
    null, malformed, duplicate, and untrusted Origin; absent/wrong/duplicate CSRF
    marker; absent/non-JSON/duplicate content type. Ordinary JSON charset
    parameters are accepted. GET does not require mutation headers.
  - Test fixed 401 and unusable-cookie deletion, 403, authentication 503 versus
    vehicle 503, generic 500, invalid body/JSON/extra fields, safe ID locations,
    sanitized nested confirmation errors, and redacted application logs.
  - Every response has `Cache-Control: no-store`. Only successful authenticated
    200 detail/update responses attach the actor's exact committed deadline.
    No failed operation fabricates a deadline or issues a session cookie.
  - Success is impossible before response preparation, commit, and closure.
    Failure and confirmation-required paths do not partially update vehicles.

  Run focused API tests, the complete database-free backend suite, pip check,
  the separately approved complete guarded native integration suite, exact
  vehicle/session/user cleanup verification, and whitespace checks. Regressions
  include authentication, session concurrency, registration, health, and Feature 3.

  **Done when:** Automated and approved native API evidence proves the contracts
  and cleanup, no frontend behavior is added, and the step is ready for review.

  **Step 3 evidence - November 14, 2026:** Added authenticated detail GET and
  PATCH routes using the existing trusted actor, canonical decoded-ID validator,
  owner-scoped queries, precommit response preparation, and deadline helper.
  PATCH mutation-policy enforcement precedes parsing/authentication/business
  work, while GET needs no mutation headers. Existing collection GET/POST and
  health/authentication behavior remain green; no PUT or DELETE was added.
  The boundary returns safe path/PATCH/metadata 422s, fixed missing/foreign 404,
  restricted 409 (including empty-fields stale cases), existing cookie-aware
  401, policy 403, distinct authentication/vehicle 503s, and fixed unexpected 500.
  Error-response preparation is also inside the redaction boundary. Failed
  prepared responses cannot release success or deadline metadata.

  Fresh focused API/query verification: 303 passed. Complete database-free
  backend suite: 1169 passed, 236 integration tests deselected. Complete authorized
  native PostgreSQL suite: 236 passed, 1169 database-free cases deselected,
  comprising 62 new API cases and all 174 prior native cases. No selected test
  failed, errored, or skipped. Each pytest run emitted the existing one
  Starlette/AnyIO BlockingPortal deprecation warning. Pip check reported no
  broken requirements; tracked and new-file whitespace checks passed.

  Native execution required `RUN_DB_TESTS=1`, loaded test settings only from
  `.env.test`, rejected any effective database other than `garageguide_app_test`,
  and retained first-statement `SELECT current_database()` verification on every
  physical connection. Cleanup was registered before writes and exact identities
  remained tracked through edits and uncertain outcomes. Separate guarded
  verification connections produced 234 receipts: 376 tracked users, 342 sessions,
  and 123 vehicles verified absent. The two read-only health cases reserved no
  records. New API cases contributed 62 receipts for 124 users, 124 sessions,
  and 64 vehicles. These are tracked-absence counts, not affected DELETE totals.
  No cleanup failure occurred and no other database was contacted.

  Native API evidence includes exact public responses/committed deadlines,
  missing/foreign isolation, null/no-op/legacy edits, full lower/clear confirmation,
  atomic rejection, stale and empty-fields 409s, policy rejection without session
  or vehicle writes, 401 deletion, 503 cookie preservation, precommit visibility,
  and one authentication validation per successful request. Preparation,
  availability, precommit, and lost-acknowledgment errors were injected failure
  simulations, not real outages. The simulated lost acknowledgment followed a
  real committed update; no automatic retry occurred and cleanup was verified.
  Existing real row-lock/concurrency tests passed again. No browser run occurred.

  Actual commands from the repository root (native execution used explicit
  opt-in, with the previous environment value restored afterward):

  ```powershell
  backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_vehicle_profile_api.py backend/tests/test_vehicles.py backend/tests/test_vehicle_profile_queries.py -m "not integration" -p no:cacheprovider --tb=short --junitxml=blueprint/.state/staging/feature-4-step-3/focused.xml
  backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --tb=short --junitxml=blueprint/.state/staging/feature-4-step-3/backend.xml
  backend/.venv/Scripts/python.exe -m pip check
  # RUN_DB_TESTS=1; settings guard passed before native execution.
  backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider --tb=short --junitxml=blueprint/.state/staging/feature-4-step-3/native.xml -o junit_logging=all -o junit_log_passing_tests=true
  git diff --check
  ```

  Exact JUnit evidence and cleanup aggregation are retained in ignored
  `blueprint/.state/staging/feature-4-step-3/`. Approved contracts and prior
  implementation/evidence remain preserved. No frontend, schema, dependency,
  session algorithm, or authentication architecture changes were made. Nothing
  was staged or committed. At that handoff Step 4 was unstarted; it was
  subsequently authorized separately for frontend-only work.

- [x] 4. Add frontend detail/PATCH request and state logic.

  Extend the existing relative API helper using explicit collection/detail and
  method distinctions; GET detail must not be parsed as a list and PATCH must
  not be parsed as creation. Reuse public response validation, deadline parsing,
  and authenticated-generation acceptance. Add a small detail/edit state module
  and focused Node tests rather than a new framework or generic data layer.

  **Acceptance and tests:**
  - Validate IDs as canonical ASCII text without JavaScript number coercion
    accepting forbidden forms. Build detail URLs only from validated IDs.
  - Prepare PATCH from genuinely changed business fields, not a full create
    payload. Preserve legacy years omitted from unrelated edits and distinguish
    blank optional controls from zero. Do not use floating-point reading math.
  - Use relative URLs, same-origin credentials, JSON mutation headers, the
    existing ten-second timeout, cancellation, and no automatic PATCH retry.
  - Parse exact detail/PATCH public objects, fixed 404, reviewed 409 fields/current
    readings, sanitized 422 including path errors, and existing fixed failures.
    Reject malformed/mismatched response shapes rather than rendering raw text.
  - Maintain original committed data, temporary draft, current confirmation
    snapshot, pending guard, and safe status. Confirmation is explicit; editing
    draft values invalidates it. A second 409 never resubmits automatically.
  - An empty-fields stale-confirmation 409 leads to deliberate reload/review,
    retaining the draft until that user action or a session/privacy boundary.
  - Preserve correctable drafts on validation/409 and vehicle-only/network
    failures while the current session remains valid. Treat uncertain PATCH
    outcomes as possibly committed and require deliberate reload/inspection.
  - Test late GET/PATCH/409 results, competing vehicle IDs, superseding loads,
    same-account relogin, account changes, logout, rejection, authentication 503,
    expiry, hidden/departed pages, and disposal. Stale work cannot restore data,
    draft, identity, confirmation, success text, or an older deadline.
  - Test exact deadline acceptance, absent/malformed/older headers, equality,
    local expiration without network work, and no automatic polling/retries or
    deadline-only session requests. Errors never extend the local deadline.

  Run focused frontend tests, the complete frontend Node suite including every
  new file, lint, production build, the complete database-free backend suite,
  pip check, and whitespace checks. No native connection is required for these
  frontend-only changes; no routed detail page is exposed until Step 5.

  **Done when:** Request/state/session regression tests pass, existing list/create
  requests remain correct, and the step has been presented for review.

  **Step 4 evidence - November 14, 2026:** Added canonical ID validation before
  URL construction, separate detail/PATCH response parsing, normalized changed-only
  PATCH preparation, strict 404/409/422 handling, and a focused private detail/edit
  store. Decimal readings use strings only; untouched legacy years and unknown
  readings are omitted/preserved correctly. Creation/collection parsing remains
  separate, with shared decimal normalization and unchanged mutation semantics.

  The store keeps committed data separate from temporary draft/confirmation and
  observes the existing session store's snapshot/subscription/request interface.
  It checks route ID, request generation, and authentication generation, without
  relying solely on user ID. Explicit Confirm alone sends acknowledgment. Per
  the Step 4 authorization, second or empty-fields stale 409s require deliberate
  reload/review; uncertain PATCHes may have committed and cannot be replayed.
  Reload has separate warning and confirmation actions and discards the draft
  only when deliberately accepted. Current-generation deadline acceptance rejects
  absent/malformed/older/expired metadata before the existing session store can
  replace a newer deadline; equal instants preserve its current representation.
  Existing local expiry clears private state without renewal or polling.

  Final focused Node run: 191 passed across both new test files, no failures,
  cancellations, skips, or TODOs. Complete Node command: 489 passed across all
  eight explicit test files, likewise no failures/cancellations/skips/TODOs.
  The focused run emitted two experimental MockTimers warnings; the complete run
  emitted five (one per participating test process using that API). Frontend lint
  passed without warnings. Final production build passed: Vite 6.4.5, 57 modules,
  1.13 seconds, using the established scoped esbuild parent-directory access.
  Complete database-free backend suite: 1169 passed, 236 integration deselected,
  with one existing Starlette/AnyIO BlockingPortal deprecation. Pip check reported
  no broken requirements. Tracked/new-file whitespace checks passed; Git's normal
  Windows LF/CRLF notices do not indicate whitespace failures.

  Final review corrected a method-classification gap so detail GET accepts only
  the approved path-ID 422, not PATCH-only body-validation responses. Its new
  regression passed, followed by all affected frontend tests/lint/build again.
  Fake-clock tests cover normal/ahead/behind device clocks, deadline equality,
  delayed expiry, and late success/409 data after navigation or authentication
  changes. Tests also cover synchronous repeat-submit blocking, confirmation
  invalidation, deliberate reload, disposal, cancellation, and no idle polling.

  Actual commands from the repository root:

  ```powershell
  node --test frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js
  node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js
  npm --prefix frontend run lint
  npm --prefix frontend run build
  backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --tb=short --junitxml=blueprint/.state/staging/feature-4-step-4/backend.xml
  backend/.venv/Scripts/python.exe -m pip check
  git diff --check
  ```

  Node stdout/stderr was retained with PowerShell Tee-Object while preserving
  native exit codes. Exact TAP/JUnit evidence is under ignored
  `blueprint/.state/staging/feature-4-step-4/`. No PostgreSQL connection, native
  test, server, or browser was run. Previous native/browser evidence remains
  historical and is not proof of a new detail interface. No backend, SQL schema,
  dependency, lockfile, session algorithm, authentication behavior, React page,
  provider wiring, or route was changed. Only frontend helpers/state/tests and
  this progress/testing-command record changed. Nothing was staged or committed.
  Step 5 was unstarted at that handoff and was subsequently authorized separately.

- [x] 5. Build the protected detail/edit page and verify browser behavior.

  Add `VehicleDetailPage.jsx`, link each garage heading to its vehicle, and
  extend the shared real route definitions and `App.jsx`. Reuse the existing
  `RequireSession resetPrivate` mechanism, public React Router matching, styles,
  form conventions, labels, focus, live regions, and in-memory state lifecycle.

  **Acceptance and browser checks:**
  - `/vehicles/:vehicleId` requires fresh route/session gating; private content
    is absent during loading, rejection, and authentication unavailability.
    Test direct load, refresh, Back/Forward, case/trailing-slash/encoded variants,
    navigation between IDs, and account changes. The static `/vehicles/new`
    route remains correct. Unrelated deeper paths do not display this profile.
  - Display all existing public profile data, including unknown versus zero,
    engine absence, and legacy years. Provide explicit Edit, Save, Cancel, and
    Back to garage controls. Cancel discards the draft; successful Save stays
    on the detail page, displays the committed result, and announces success.
  - Test text changes, all reading transitions, required-field/Unicode/year
    validation, lower/clear prompts for each/both readings, and canceling prompts.
    Show current and proposed readings in the inline confirmation panel. A
    changed server value requires a new review/confirmation, never blind replay.
  - An ordinary no-op API update is safe; the form avoids an empty PATCH and
    does not require users to resubmit an unchanged out-of-policy legacy year.
  - Pending submission blocks repeat clicks/Enter submissions. Labeled errors
    associate with controls and clear appropriately; focus moves to the first
    invalid field, confirmation heading, safe error, or relevant success state.
    Confirm/cancel controls are keyboard reachable and statuses are announced.
  - Cover unavailable/retry, 404, forbidden, rejected-session, malformed-response,
    uncertain-PATCH, and late-response states. Clearly label simulated failures
    as simulations, not real database outages. No automated mutation retries.
  - Two independent accounts cannot read or update each other's vehicle IDs;
    missing and foreign IDs produce the same safe UI/HTTP behavior.
  - Observe no-store/deadline headers, success-driven local deadline update
    without an extra session request solely for synchronization, no idle polling,
    and private identity/profile/draft clearing at the visible local deadline
    without expiry-triggered network work. Preserve server-authoritative expiry.
  - Verify keyboard operation, visible focus, labels, announcements, layouts at
    375/768/1440 pixels, and 200% zoom in development and production preview.
    Malformed direct paths rejected by Vite are server-boundary observations,
    not React browser coverage; separately test router-side malformed safety.
  - Use only the guarded prepared test backend and exact synthetic vehicles,
    users, and sessions for writes. Wait for verified cleanup after shutdown.
    Do not use ordinary development data for browser fixtures.

  Run the complete frontend suite, lint/build, database-free backend suite, pip
  check, and whitespace checks. Record actual browser/version/date, observations,
  simulated cases, limitations, and exact cleanup message. If no agent browser
  environment is available, provide exact manual steps and wait for observations;
  never infer a browser pass from source/unit tests. Native/manual-server writes
  still require explicit authorization and all test guards.

  **Done when:** Applicable development/preview browser acceptance is observed
  with accurate attribution and exact cleanup, supporting checks pass, and the
  user has reviewed Step 5. Unperformed browser criteria remain pending.

  **Step 5 implementation/automated evidence - November 14, 2026:** Added the
  protected profile route/page, garage heading Links, explicit edit/save/cancel,
  accessible confirmation and discard/reload controls. The actual shared route
  descriptor drives React Router rendering and protected matching; static new
  routing remains correct. The page consumes the existing session store through
  its provider without changing session algorithms, and owns its detail store
  across StrictMode setup/cleanup, navigation and private-state disposal.
  Focused route/detail API/state command: 288 passed. Complete eight-file Node
  command: 528 passed, no failures/skips/cancellations. Experimental MockTimers
  warnings: three focused and five complete. Complete database-free backend
  suite: 1169 passed, 236 integration tests deselected, one existing
  Starlette/AnyIO BlockingPortal deprecation, 11.16 seconds. Pip check passed.
  Frontend lint passed. Production build passed (Vite 6.4.5, 59 modules,
  1.21 seconds); initial sandboxed esbuild directory access was denied, then the
  approved scoped-access rerun passed. No dependency or configuration workaround
  was added. Tracked/new-file whitespace checks passed. No native tests,
  PostgreSQL connections, browser run or server startup occurred in this step.
  Full commands/results and limitations are in
  `docs/verification/VEHICLE_PROFILE_STATUS.md`; the exact guarded commands and
  dev/preview checklist are in `docs/verification/BROWSER_CHECKS.md`.
  At that automated handoff Step 5 remained unchecked pending user-performed
  browser observations and exact cleanup. Those were subsequently reported below.
  Earlier feature/browser/native evidence is preserved separately.

  **Step 5 user browser evidence - November 14, 2026:** The user reported the
  complete Feature 4 checklist passed in both Vite development and production
  preview, using Chrome 156.0.8078.73. Observations cover garage links, canonical/
  encoded/case/trailing routes and history, invalid/unrelated paths, static new
  precedence, private loading gates, view/edit/save/cancel/reload and persistence,
  all editable fields, omitted unchanged legacy year, null versus zero, explicit
  lower/clear confirmation, atomic two-reading confirmation, cancel/edit
  invalidation, stale confirmation without replay, missing/foreign safety and
  two-account isolation. Headers and deadline synchronization passed without an
  extra session request, polling or automatic mutation retry. Actual visible
  local expiry cleared private identity/vehicle state without a network request.
  Keyboard, focus, labels, error associations, announcements, repeat prevention,
  375/768/1440 layouts and 200% zoom passed. Validation and rejected/forbidden/
  unavailable/malformed/timeout/uncertain/late cases showed approved safe behavior;
  simulated failures were restored and remain separate from real backend/native
  evidence. An uncertain update required deliberate reload/inspection. Legacy
  response simulation does not establish a persisted legacy-row browser test;
  no unreported malformed-path behavior is inferred. The full attributed report
  and limitations are in `docs/verification/VEHICLE_PROFILE_STATUS.md`.
  Exact user-reported guarded cleanup:
  `Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.`
  No agent browser run, new test execution or PostgreSQL connection was performed
  to record these observations. Step 5 is complete and awaiting final review;
  Step 6 remains unstarted. No staging, commit or audit is authorized.

- [ ] 6. Verify the complete feature and prepare its immutable review checkpoint.

  Run the complete database-free backend suite; pip check; the complete frontend
  Node command including every new test file; lint; production build; separately
  approved complete guarded native suite; exact cleanup; whitespace; full Git
  status, untracked-file inventory, and builder diff review.

  **Acceptance and final review packet:**
  - Review every ID/validation boundary, owner-scoped query, lock and transaction,
    stale acknowledgment, reading timestamp, safe error, policy/cookie behavior,
    deadline path, protected route, stale-response guard, and uncertain update.
  - Record actual commands, totals, warnings, exact synthetic cleanup, current
    branch/HEAD/index status, every changed/untracked file and purpose, raw hashes,
    complete diff, frozen proposal, limitations, and proposed checkpoint message.
  - Confirm no schema, dependencies, lockfile, private environment, generated
    output, ignored recovery artifacts, or unrelated work is proposed for Git.
  - Preserve separate automated, native PostgreSQL, real user/agent-browser, and
    simulated-failure evidence. Attribute execution and reuse accurately; no
    current Feature 4 browser or native results exist at specification time.
  - Before auditing, obtain approval of the exact immutable checkpoint and its
    commit. Freeze the final verified spec/evidence before that checkpoint.
    Then run `$audit independent current` against the exact approved HEAD using
    the configured fresh reviewer. Report identity, target/spec hash, findings,
    reviewer checks, reused evidence, and receipt freshness. Do not self-review
    or automatically fix/accept findings. Changes require reviewed repairs and
    affected checks, new browser evidence where behavior changes, and fresh review.
  - Stop before `$complete`; no completion, landing, push, deploy, branch deletion,
    or later-feature work is part of this step.

  **Done when:** Final checks and cleanup pass, the approved checkpoint has a
  fresh passing independent receipt with no unresolved blockers, and the full
  review packet has been delivered for separate completion approval.

  **Step 6 verification/checkpoint proposal - November 14, 2026:** Complete
  database-free backend suite: 1169 passed, 236 integration tests deselected,
  12.36 seconds. Complete eight-file frontend command: 528 passed; no failures,
  cancellations, skips or todo. Pip check, frontend lint and production build
  passed. Build: Vite 6.4.5, 59 modules, 1.63 seconds, using the established
  scoped esbuild access. Complete separately authorized native suite: 236
  passed, 1169 database-free tests deselected, 255.25 seconds. No selected
  native case failed, errored or skipped. Each pytest run emitted one existing
  Starlette/AnyIO BlockingPortal deprecation; Node emitted five experimental
  MockTimers warnings. Lint/build/pip had no warnings. Windows Git emitted the
  existing LF-to-CRLF notice for this file; whitespace checks passed.

  Native execution required explicit `RUN_DB_TESTS=1`, loaded only `.env.test`,
  and passed the effective `garageguide_app_test` guard before execution. Every
  physical fixture/handler/cleanup connection used the first-statement
  `SELECT current_database()` guard. Exact cleanup was registered before writes,
  removed tracked vehicles by ID/owner before sessions/users, and verified
  absence on separate guarded connections. JUnit contains 234 exact cleanup
  receipts: 376 tracked users, 342 sessions and 123 vehicles verified absent.
  These are per-fixture tracked-absence counts, not affected DELETE row counts.
  The two remaining cases are read-only health checks without reserved records.
  No cleanup failure or connection/write to another database occurred.
  The first evidence-aggregation assertion assumed both read-only tests shared
  one module; their exact definitions were inspected and the report used both
  correct test identities. This was a reporting-script correction, with no
  application change, cleanup failure or native rerun.

  Builder review covered the full tracked/new-file diff: canonical IDs, strict
  omission/null/Decimal/year validation, owner-scoped SQL and row locks, fresh/
  stale confirmation and atomic rejection, timestamps, commit/rollback/closure
  and uncertainty, safe errors/logs/policy/headers, route precedence/matching,
  drafts/reload, session generations, stale work and local expiration. No
  confirmed application defect or unexplained file was identified; no product
  code or tests were changed during Step 6. This is builder review, not an
  independent audit. Features 1-3 archives and build-plan status are unchanged.

  The user's November 14 Chrome 156.0.8078.73 development/preview report and
  exact manual cleanup marker above are reused with user attribution; no agent
  browser run or new browser observations are claimed. Real native behavior,
  native injected failures, browser simulations and automated tests remain
  separate in `docs/verification/VEHICLE_PROFILE_STATUS.md`. No independent
  reviewer execution or evidence reuse is claimed in advance.

  Full commands/logs/XML/cleanup summary are preserved under ignored
  `blueprint/.state/staging/feature-4-step-6/`. The frozen 28-file proposal,
  complete builder diff and per-file purposes/raw SHA-256 hashes are in
  `blueprint/.state/staging/feature-4-checkpoint-proposal.json`,
  `feature-4-review.diff` and `feature-4-review-packet.md`. Index is empty;
  branch and parent HEAD remain the frozen Feature 4 branch and completed
  Feature 3 commit. Private env files, schema, dependencies, lockfiles, generated
  output and recovery artifacts are excluded. Nothing was staged or committed.
  Obtain approval of this exact checkpoint before committing or auditing; do
  not rewrite these frozen specification/evidence bytes merely to record review.

## Files / areas

- `backend/app/vehicle_schemas.py`: PATCH/confirmation models, canonical ID
  validation, shared create-year policy, pure correction checks, public models.
- `backend/app/vehicle_queries.py`: owner-scoped detail/update, locked comparison,
  safe domain outcomes, timestamp behavior, precommit response preparation.
- `backend/app/routes/vehicles.py`: GET/PATCH detail routes, PATCH policy coverage,
  safe ID/PATCH/409/404 handling, public responses and existing deadline helper.
- `backend/app/authentication.py`, `database.py`, and `session_queries.py`: reuse
  existing actor/deadline/transaction facilities; do not change the session
  database algorithm, cookies, connection settings, or architecture.
- `backend/app/main.py`: existing router/middleware already cover vehicle paths;
  no registration change is expected unless a concrete test proves it necessary.
- Existing vehicle schema/query/API tests and native counterparts: extend focused
  coverage; add narrowly named tests only when that improves reviewability.
- `backend/tests/database_support.py`, fixtures, manual server, and fixture-safety
  tests: exact tracked-ID update safety and cleanup, only where needed.
- `frontend/src/api.js`, `vehicleValidation.js`: detail/PATCH helpers and safe
  parsers without regressing collection/create behavior.
- New `frontend/src/vehicleDetailState.js` and focused
  `frontend/tests/vehicleDetailState.test.js`: testable draft/confirmation/request
  lifecycle, using the installed Node runner.
- `frontend/tests/vehicleDetailApi.test.js`: canonical IDs, PATCH preparation,
  strict response/error parsing, timeout/cancellation, and no automatic replay.
- New `frontend/src/VehicleDetailPage.jsx`; existing `VehiclesPage.jsx`,
  `vehicleRoutes.js`, `App.jsx`, and `styles.css`: garage links and protected page.
- Existing session/deadline/route helpers and frontend vehicle/session tests:
  reuse/extend only what dynamic profiles and current-request acceptance need.
- `docs/verification/VEHICLE_PROFILE_STATUS.md`: new Feature 4 evidence, without
  duplicating or rewriting Feature 3's status/history.
- `docs/verification/BROWSER_CHECKS.md`: add the scoped Feature 4 guide/evidence,
  preserving prior dated observations and their limitations.
- `blueprint/context/current-feature.md`: this approved-work contract and step
  progress; freeze exact verified bytes before the independent checkpoint.
- `blueprint/context/review.md` and `findings.md`: only during the separately
  authorized audit workflow; preserve historical evidence if repairs are needed.
- `database/01_schema.sql` and later SQL files: inspection/source of truth only;
  no feature change, execution, initialization, or migration is needed.

## Data / contracts

### Canonical vehicle IDs

Validate the framework-decoded path parameter as text matching `[1-9][0-9]*`
with value at most 2147483647 before coercing it. Reject leading zeroes, signs,
fractions, whitespace, nonnumeric/non-ASCII values, zero, negatives, and overflow.
Percent encoding must not bypass canonical validation: a decoded `01` is invalid.
Do not implement custom URL decoding; use framework/router decoding and matching.
Malformed paths must not crash the application or reveal cached profile data.
Never echo the raw ID in the validation response or application error logging.

### PATCH input and public output

The JSON body is a strict object allowing only the seven editable business
fields and optional `reading_confirmation`. Preserve the set of supplied fields;
do not dump default nulls over omitted values. At least one business field must
be supplied. A valid no-op is not an empty PATCH.

| Field | Supplied value rules |
| --- | --- |
| `year` | Strict JSON integer, 1886 through backend current calendar year plus one, inclusive. Reject bool/string/fraction/null. Reuse one injectable backend provider. |
| `make`, `model`, `vehicle_type` | Required when supplied: valid UTF-8-representable Unicode, no NUL/unpaired surrogate, trim, preserve case, reject blank or null. Vehicle type stays free text. |
| `engine` | Omitted preserves; null or trimmed blank clears; otherwise the same safe, trimmed, case-preserving text rules. |
| `mileage`, `operating_hours` | Omitted preserves; explicit null clears subject to confirmation; otherwise decimal strings using the existing exact parser. |
| `reading_confirmation` | Optional strict object; when supplied, reject null/non-object/unknown keys. Permit only `mileage` and `operating_hours`, each also supplied as a business field. Values must be non-null decimal strings under the same reading rules, normalized before Decimal comparison. An empty mapping supplies no acknowledgment. |

No new text-length limit or enum is introduced. Readings accept trimmed ASCII
digits with at most one fractional digit, from zero through `99999999999.9`.
Reject numeric JSON values, booleans, empty strings, signs, exponents, commas,
nonfinite/negative values, excess precision, and overflow. Never round/clamp.
Serialize exactly one fractional digit. Null means not recorded; `"0.0"` is a
confirmed zero. Blank optional form controls map to explicit null only when
that field changed; untouched controls are omitted.

An omitted legacy year is preserved even outside today's narrower input range.
Supplying that same out-of-policy year still fails supplied-year validation;
the form must not send an unchanged legacy year. Public reads continue to allow
the PostgreSQL positive SMALLINT range 1-32767. Keep the public `Vehicle` model's
exact ten fields: id, year, make, model, engine, vehicle_type, mileage,
operating_hours, readings_updated_at, created_at. Use aware ISO 8601 timestamps.
Reject client IDs, user_id, owner_id, timestamps, and every other unknown field.

### Locked reading confirmation

After owner-scoped lock acquisition, for each supplied reading compare normalized
Decimals/null against the current database value. It currently requires
confirmation exactly when the current value is non-null and the proposed value
is null or strictly smaller. Equal readings, null-to-null, increases, and
unknown-to-known need no acknowledgment. Known zero-to-null does require one.

Example initial request:

```json
{"mileage":"900.0"}
```

When current mileage is 1000.0, the safe 409 is:

```json
{
  "detail": "Reading changes require confirmation.",
  "fields": ["mileage"],
  "current_readings": {"mileage":"1000.0"}
}
```

After explicit confirmation the next PATCH is:

```json
{"mileage":"900.0","reading_confirmation":{"mileage":"1000.0"}}
```

Every supplied acknowledgment must match its current locked field value. Every
currently required field must have such an acknowledgment. If either condition
fails, reject the whole transaction with 409 and write no business fields.
`fields` contains only the supplied readings currently requiring confirmation,
in stable mileage/operating_hours order; `current_readings` has exactly those
keys and their canonical current values. It never contains unrelated readings,
arbitrary request echoes, vehicle ownership, or another user's information.
Both dangerous fields are listed if both currently require acknowledgment,
even if only one acknowledgment was missing/stale. A confirmation-required
response is not a partial save or a successful response.

A stale supplied acknowledgment is rejected even when a concurrent correction
means the proposed value is now an increase/no-op rather than a decrease.
In that case the same 409 may have `fields: []` and `current_readings: {}`
(or contain only the other reading that still requires confirmation). Never
list a field that no longer requires confirmation merely to signal staleness.
For an empty list, the UI requires deliberate reload and review before another
Save, rather than presenting an empty confirmation or auto-replaying the PATCH.
This preserves both approved requirements: stale acknowledgment cannot authorize
a write, and 409 only identifies fields currently requiring confirmation.

Do not cache a pre-lock comparison as authorization. Do not store confirmation
metadata, create signed confirmation tokens, or add version columns. The
acknowledged current value, not an all-record version, is the deliberate check.

### Ownership, SQL, transactions, and reading time

- Only `require_authenticated_session` supplies the actor. No request body,
  query/header owner, browser account ID, or router state can override it.
- GET selects explicit public columns with `WHERE id = %s AND user_id = %s` in
  a read-only business transaction. Missing/foreign records share one outcome.
- PATCH opens one owned writable transaction and selects explicit columns with
  those same predicates and `FOR UPDATE`. Only after the row lock is held may it
  compare readings, validate acknowledgments, merge omission, and update.
- The UPDATE also scopes by both IDs and binds all variable values. A static
  explicit-column UPDATE using the merged locked values is sufficient; no
  arbitrary browser-controlled SQL identifiers or generic repository is needed.
- Under the existing PostgreSQL transaction behavior, waiting updates inspect
  the current locked version after the prior updater finishes. Last committed
  values may win for overlapping supplied fields; omitted fields preserve the
  latest locked values. There is no general stale-edit detection for text fields.
- When either reading actually changes (null-safe Decimal comparison), set
  `readings_updated_at` using PostgreSQL `clock_timestamp()` in the write, after
  the lock wait. Do not use a pre-lock transaction-start time as the change time.
  Preserve the timestamp for text-only/unchanged-reading updates and whole no-ops.
  Clearing the final known reading stores change time, not null. Preserve
  `created_at`, ownership, historical service readings, and schedule baselines.
- A valid no-op may skip UPDATE, but still prepares its public response, commits
  the short owned transaction, closes, and returns ordinary 200.
- Validate/serialize the public result and prepare response/deadline attachment
  before commit. Only release a successful response after commit and closure.
  Exit/rollback/close before translating known failures or safe domain outcomes;
  lock/statement timeouts map to the existing vehicle-unavailable class.
- Keep connection/statement timeouts and direct psycopg architecture. A lost
  commit acknowledgment may hide a completed change: close and return safe
  failure without promising rollback of a transaction that may have committed.
- Authentication's separate validation/idle-extension transaction commits before
  returning the trusted actor. A later vehicle 404/409/failure does not undo that
  session activity. Do not change authentication locking, expiration, revocation,
  cookies, or multi-device behavior.

### API, policies, headers, and safe errors

GET detail and PATCH return 200 with exactly one complete public `Vehicle`,
without a wrapper or confirmation metadata. Retain existing collection GET/POST.
No DELETE or PUT endpoint is introduced.

GET needs authentication but no mutation headers. PATCH reuses the existing
exact configured trusted Origin, `application/json` (ordinary charset parameters
allowed), `X-GarageGuide-CSRF: 1`, and validated cookie transport policy. Apply
policy before vehicle business writes, including correction requests. No
permissive CORS or new CSRF mechanism. Frontend uses relative URLs and
`credentials: 'same-origin'`.

| Failure | Exact safe response policy |
| --- | --- |
| Invalid decoded ID | 422, `{"detail":[{"loc":["path","vehicle_id"],"msg":"Enter a vehicle ID from 1 through 2147483647 using digits without leading zeroes.","type":"value_error"}]}` for every invalid representation. Never echo it. |
| Invalid PATCH/JSON | 422, existing sanitized `detail` list of only `loc`, fixed `msg`, and approved fixed `type`. Use approved business-field locations, or `["body"]` for invalid JSON/object/unknown fields. No input/ctx/exception text. |
| Empty or confirmation-only PATCH | 422, `{"detail":[{"loc":["body"],"msg":"Provide at least one editable vehicle field.","type":"value_error"}]}`. |
| Required field explicitly null | Sanitized 422 for that field with fixed `This field cannot be cleared.` message and `value_error` type. |
| Invalid confirmation metadata | Sanitized 422 at `["body","reading_confirmation"]` with fixed `Provide confirmation values only for supplied reading fields.` and `value_error`; do not echo arbitrary nested keys/values. |
| Missing/foreign-owned vehicle | 404, exactly `{"detail":"Vehicle not found."}`; same body, cache/deadline/cookie policy for both, no existence indicator. No promise of identical timing is implied. |
| Missing/stale acknowledgment | 409, exactly the reviewed detail/fields/current_readings object. Only validated current readings from the locked owned vehicle may appear. |
| Missing/malformed/unknown/expired/revoked session | Existing 401 `{"detail":"Not authenticated."}`, matching unusable-cookie deletion, and private frontend gating/clearing. |
| Mutation policy rejection | Existing 403 `{"detail":"Request not allowed."}` before business writes, without automatic retry. |
| Authentication configuration/database unavailable | Existing 503 `{"detail":"Authentication unavailable. Please try again."}`; preserve potentially valid cookie and gate private UI. |
| Vehicle database unavailable, including statement/lock timeout | Existing 503 `{"detail":"Vehicles unavailable. Please try again."}`; preserve cookie, expose no driver/SQL detail. |
| Unexpected failure | Existing 500 `{"detail":"Internal server error"}`; fixed application logging only, without private values/tracebacks/request bodies. |

Reuse existing safe vehicle field messages/types for ordinary invalid fields.
The new confirmation and empty-request checks must have deliberate fixed safe
types/messages rather than passing Pydantic/driver text through. Keep auth and
credential whitelists separate. Framework authentication/policy rejection and
malformed-body handling must remain safe; invalid ID/body rules describe errors
once that boundary is reached, not a promise to bypass authentication/policy.

Every vehicle response, including errors and routing errors, has
`Cache-Control: no-store`. Only successful authenticated detail/PATCH 200s attach
`X-GarageGuide-Session-Expires-At` through the existing reusable helper, using the
validated actor's exact committed deadline. Do not calculate a new deadline in
the route. Errors/404/409 do not attach or fabricate deadlines. Preserve existing
creation 201 attachment. No vehicle endpoint creates a cookie, session, or token.
Logs must not contain vehicle values, confirmation snapshots, bodies, passwords,
hashes, tokens, cookies, SQL, driver details, or connection strings. The scoped
409 acknowledgment values are intentional authorized response data, not logging
or permission to expose raw inputs in other errors.

### React profile, confirmation, and private-state lifecycle

Use one protected `/vehicles/:vehicleId` page with view/edit states, reached by
React Router `Link` from garage headings. Reuse actual shared route definitions
in both rendered routes and session classification with public `matchRoutes`.
No pathname string comparisons or hand-written decoding. Keep static new-vehicle
routing and protect encoded/case/trailing-slash/history variants consistently.

On load, gate private content until the existing session check for that location
and the current vehicle GET succeed. Render safe text interpolation only.
Display `Not recorded` for nulls and `0.0` for confirmed zero. The edit form sends
only changed fields; preserve the loaded record separately from its temporary
draft. Save remains on this page and replaces loaded data with the committed
PATCH response. Cancel discards the draft and confirmation, returning to view.
Back to garage uses existing navigation/list loading; no dashboard is introduced.

On 409, show an inline labeled confirmation panel with each required current and
proposed reading (or `Not recorded` for a proposed clear). Focus its heading and
announce the requirement. Explicit confirm sends the draft plus freshly
acknowledged values. Cancel dismisses acknowledgment and retains the draft for
editing; it sends nothing. Editing any proposed business value invalidates
confirmation. An empty-fields stale response requires explicit reload/review.
Do not automatically confirm, refresh-and-confirm, or resubmit.

Prevent repeat submissions with the existing synchronous in-flight guard and
disabled controls, not only an asynchronously rendered disabled state. Use
associated labels/errors, aria-invalid/describedby, live announcements, deliberate
focus, visible focus styling, and keyboard-operable actions. Preserve temporary
draft values after correctable errors while authentication remains valid.

Keep the existing ten-second request timeout and cancellation. An uncertain PATCH
message says: `The update may have completed. Reload this vehicle and check its
current values before submitting again.` A dedicated reload action is deliberate
user activity, not automatic retry; it discards draft/acknowledgment and displays
freshly retrieved values after explaining this effect. No browser-side rollback
claim, automatic PATCH retry, or server-side idempotency is added.

Only the current authenticated generation, route/vehicle ID, and request
generation may accept data or a returned deadline. Abort/ignore superseded work;
user ID equality alone is insufficient, including logout/login as the same user.
Successful current responses update the existing local deadline without another
session request solely for synchronization. Missing/malformed/older/expired
deadlines cannot extend identity or replace a newer accepted deadline. Local
deadline equality clears identity and all private record/draft/confirmation state
without calling any endpoint, polling, or automatically retrying. PostgreSQL
remains authoritative for actual idle and absolute validity.

Reuse existing startup/refresh, deliberate protected-navigation, visibility-return,
and explicit-retry session validation. Logout, rejection, expiry, account change,
route departure, and authentication-unavailable gating invalidate private page
work and state. Vehicle-only unavailability may retain the current authenticated
draft with safe feedback; it does not extend the deadline. A stale result cannot
restore cleared identity, profile, draft, success state, or confirmation. Dispose
state and pagehide/BFCache content using the existing private-page patterns.

No private profile/draft/confirmation data goes in browser storage, URL query or
fragment, router state, logs, or telemetry. The canonical vehicle ID in the route
is permitted and never replaces server-side ownership authorization. No token or
cookie becomes JavaScript-visible. Invalid IDs and missing/foreign vehicles show
safe states with a garage link, not cached content from a previously loaded ID.

## Testing

No implementation, live database, browser, or new test results are claimed by
this specification. There is no combined Verify, typecheck, or Browser tests
command configured. Use installed pytest/Node tests, lint/build, and direct
manual browser evidence; do not install a runner.

Database-free backend gate from repository root:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pip check
```

Complete current frontend gate, including both new Feature 4 files and all six
existing files explicitly:

```powershell
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js
npm --prefix frontend run lint
npm --prefix frontend run build
```

Include every additional test file explicitly if implementation introduces one;
do not silently omit files. Use the existing fnm-managed Node 22.12+ installation
and backend Python 3.13 environment, without installs or dependency changes.

Only after explicit native-test authorization:

```powershell
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider
```

Native safety is mandatory for fixture, handler, concurrency, manual-server, and
cleanup connections:

- Load only `backend/.env.test`, never development `.env`; require explicit
  `RUN_DB_TESTS=1` and effective database exactly `garageguide_app_test`.
- Immediately on each new physical native connection, verify
  `SELECT current_database()` as its first statement before exposure or writes.
  Reject any database other than exactly `garageguide_app_test`. Query once per
  physical connection, not before every SQL statement. Health remains read-only.
- Register cleanup before writes, use unique synthetic accounts/sessions/vehicles,
  and restrict editable fixtures to exact owned synthetic IDs. Track vehicle
  identity before mutation, independent of mutable values or a returned response.
- Delete only exact tracked vehicles using both ID and fixture owner, before
  users; retain existing exact session/account cleanup. Verify absence on
  separate guarded connections. No prefix deletion, truncation, broad user
  cleanup, sequence reset, schema initialization, or ordinary-data writes.
- Cleanup runs after setup/assertion/request failure and uncertain outcomes.
  Failed guards stop writes; failed cleanup stops native verification and is
  reported as a blocker rather than waived. Never write to `garageguide_app`,
  `postgres`, or another database.
- Use deterministic row-lock evidence and bounded synchronization, not timing
  guesses, for concurrent owner-scoped merge and stale-confirmation tests.

Whitespace/status review uses `git diff --check`, complete changed/untracked
inventory, and review of new-file whitespace without staging. Only run staged
checks after staging is separately approved. Never stage to make a review diff.

Record browser evidence by actual executor, date, exact browser, development or
preview environment, real observed behavior, simulated failure cases, and exact
cleanup result. Do not infer runtime accessibility/visual/isolation/idle behavior
from unit tests or treat old Feature 3 observations as proof of new Feature 4 UI.
If later code changes affect observed behavior, identify and repeat the affected
browser checks before claiming acceptance. Preserve historical evidence unchanged.

## Notes for the AI

- This specification is the only active work item; keep the frozen Feature 4
  identity, branch, attempt, and archive destination. Do not create them early.
- Read the existing focused modules and tests; reuse known helpers instead of
  duplicating credential, CSRF, session, Decimal, or public-response logic.
- Treat lock acquisition as the comparison boundary. A frontend check, a
  pre-lock read, or a bare confirmation flag cannot authorize a correction.
- Validation and predictable domain outcomes must be translated only after
  connection cleanup. Preserve uncertainty when the commit outcome is unknown.
- The schema already supports this feature. Do not touch schema/dependencies,
  change automatic runtime setup, or connect to a database during planning.
- Do not begin any build step without approval of this complete specification
  and explicit implementation-step authorization. Stop at every configured
  review gate. No staging/commit/audit/complete/merge/push is implied.
