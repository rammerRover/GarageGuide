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


<!-- blueprint:completion {"schemaVersion":2,"specBytes":66557,"specSha256":"ea12c29060490b2fbc0ddb61b723fe764768e8432b6481bffa8be66342175879","branch":"refs/heads/feature/view-and-update-a-vehicle-profile","head":"bc2db9fc712f03cfab93268076b9662b14dba334","baseRef":"refs/heads/main","baseCommit":"683e1933a77f7ba056811dbdc7bd97d16374ebc8","sourceTree":"ecf18281820a1db6170d15baba54c6ddd54afab5","landing":"local-merge","absentOptional":[]} -->

## Completion preparation and evidence attribution

Prepared for explicit completion-commit review only, at 2026-11-15T03:40:30.786971+00:00.
No commit, stage in the normal index, merge, push, deployment or branch deletion
was performed. Local landing remains separately gated. The user explicitly
requires the existing overview fingerprint to remain unchanged; the entire
overview file is preserved byte-for-byte, overriding generic fingerprint refresh.

The first 66557 bytes are the exact verified original specification,
SHA-256 `ea12c29060490b2fbc0ddb61b723fe764768e8432b6481bffa8be66342175879`. Its historical Step 6 checkbox and pending-review
wording remain unchanged because this was the exact independently reviewed
input. Step 6's verification and independent-review requirements are now met by
the recorded final results and passing receipt below; no product criterion is
waived. The original proposal is historical preapproval material; its pending
approval fields describe its creation time, not the later checkpoint approval.

The independent receipt remains bound to original checkpoint `bc2db9fc712f03cfab93268076b9662b14dba334`,
not a future completion commit. Reviewer: Codex `gpt-6.1-terra`, automatic execution
in a fresh isolated subagent. Findings: none; the exact original empty ledger is
preserved. The full receipt is copied without changing target, identity, date,
model, commands or evidence-reuse declarations.

## Completion checks

| Check | Actual completion-session result |
| --- | --- |
| Database-free backend | 1169 passed; 236 integration cases deselected; 11.04 seconds |
| Complete frontend Node command | All eight files; 528 passed; no failures, skips, cancellations or todo |
| Pip check | No broken requirements found |
| Frontend lint | Passed |
| Production build | Passed; Vite 6.4.5; 59 modules; 1.36 seconds |
| Whitespace | Tracked and added-archive checks required and verified in completion packet |
| Archive/recovery | Exact prefix, passing receipt, empty findings, input payloads and source tree validated before context reset; final read-back checks recorded in packet |

Exact commands:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-4-completion/backend.xml --tb=short
backend/.venv/Scripts/python.exe -m pip check
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js
npm --prefix frontend run lint
npm --prefix frontend run build
git diff --check
git diff --no-index --check /dev/null blueprint/history/features/04-view-and-update-a-vehicle-profile.md
```

The build used the established scoped access needed for esbuild; no configuration
or dependency workaround was added. Backend emitted one existing Starlette/AnyIO
BlockingPortal deprecation. Node emitted five experimental MockTimers warnings.
Pip/lint/build had no warnings. Git may emit ordinary LF-to-CRLF notices. No
browser or PostgreSQL connection/native test was run during completion.

Native evidence is reused from the builder's 236 guarded PostgreSQL passes,
including 234 exact-cleanup receipts verifying 376 tracked synthetic users,
342 sessions and 123 vehicles absent through separate guarded connections.
These are tracked-absence counts, not DELETE affected-row counts. The two other
native tests were read-only/no-record health checks. RUN_DB_TESTS=1, .env.test,
effective and connected garageguide_app_test, first-statement current_database()
verification, registered cleanup before writes, exact vehicle-before-user cleanup
and separate absence checks belong to that original native run, not this completion.

Browser evidence is the user's November 14, 2026 Chrome 156.0.8078.73 report from
both Vite development and production preview, reused without a new browser run.
The independent reviewer also reused native/browser evidence rather than
rerunning them. No reviewer browser execution or repeated idle observation is
claimed. Real persisted behavior, native fault injection and browser simulations
remain separate. Exact user-reported manual cleanup:

```text
Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.
```

Remaining limitations: last-committed supplied text edits, no version/idempotency
or automatic PATCH retry, uncertain commit acknowledgment requiring deliberate
reload, device-clock-dependent local gating with PostgreSQL authoritative for
server validity, and no configured browser/component DOM runner. Failure shims
are not PostgreSQL-outage evidence. Legacy response simulation is not persisted
legacy-row browser evidence. Malformed HTTP rejection before React is Vite-boundary
evidence; no unreported malformed-path observation is inferred. The native
cleanup parser's original module-name assumption was corrected without rerunning
the suite or changing application code; that note remains in original evidence.

## Implementation history

Full feature-branch implementation range: `683e1933a77f7ba056811dbdc7bd97d16374ebc8..bc2db9fc712f03cfab93268076b9662b14dba334`.
The exact step-by-step history/results are retained in the original specification
prefix; the immutable checkpoint and its 28-file inventory/hashes are retained
below. Commit listing (commit, parent(s), subject):

```text
bc2db9fc712f03cfab93268076b9662b14dba334 683e1933a77f7ba056811dbdc7bd97d16374ebc8 feat: view and update vehicle profiles
```

Completion adds only this archive, the Feature 4 checkbox, and canonical live
context resets. Features 1-3 archives, application/test code, SQL, dependencies,
lockfiles, overview body/fingerprint and verification documents are unchanged.
Findings was already its canonical empty stub; its bytes are preserved below.

## Recovery metadata explanation

The compact blueprint:completion annotation above records build attempt 1's
original branch, reviewed HEAD, local main/base, exact spec bytes/hash, landing
policy, and verified source tree. No optional evidence was absent. The source
tree was captured with an isolated temporary index; the normal index remained
empty and byte-identical. It differs from the reviewed HEAD only in the exact
passing review receipt. No commit or recovery ref was created. Retain the local
source-tree Git object and ignored raw evidence for interrupted-completion proof;
archive/history annotations do not themselves authorize a commit or landing.


## Findings

Exact original evidence follows; its input bytes are preserved.

# Findings

> **Generated file.** The findings ledger: review findings raised by `/audit`
> against the work in progress, each with a durable ID, severity (P0-P3), and
> status. `/implement` marks repaired findings `fixed`, a later `/audit` pass
> moves them to `closed`, and `/complete` refuses to land while any P0 or P1
> finding is `open` or `fixed`, then archives resolved findings with the work
> and resets this file.

_No findings recorded. `/audit` appends findings here when it finds them._


## Independent review

Exact original evidence follows; its input bytes are preserved.

# Independent Review

**Status:** passed
**Target commit:** bc2db9fc712f03cfab93268076b9662b14dba334
**Base commit:** 683e1933a77f7ba056811dbdc7bd97d16374ebc8
**Base ref:** main
**Spec hash:** ea12c29060490b2fbc0ddb61b723fe764768e8432b6481bffa8be66342175879
**Prepared by:** codex
**Builder model:** unknown (runtime did not expose exact model)
**Requested reviewer:** codex
**Requested model:** gpt-6.1-terra
**Requested execution:** automatic
**Requested at:** 2026-11-15T03:28:54.077940+00:00
**Workflow:** regular
**Check required:** no
**Reviewer adapter:** codex
**Reviewer model:** gpt-6.1-terra
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-15T03:31:08.317967+00:00
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** passed
**Check result:** not-required

## Handoff

Review the active spec and the complete `683e1933a77f7ba056811dbdc7bd97d16374ebc8..bc2db9fc712f03cfab93268076b9662b14dba334` delta in a fresh
isolated subagent without the builder conversation. Run all Audit lenses from scratch.
Run Check when required above. Do not edit product code, accept findings, or
reuse the existing findings as the review scope.

The user explicitly authorized independent review of this exact committed HEAD
and frozen verified specification. The only unchecked item is Step 6 because
its own done-when includes this fresh audit; implementation, user browser
acceptance and final automated/native verification are recorded as complete.
This explicit user instruction takes precedence over the generic Phase A
all-checkboxes precondition. Do not edit the specification to tick the review
step or change its hash. This is not permission to waive an unfinished product
criterion or an audit finding.

Reviewer: use the installed project-local Audit skill and independent-review
reference, then perform Phase B. Review quality, security, performance and tests,
including the user's listed ownership/concurrency/transaction/validation/privacy/
React-route/state/accessibility/cleanup boundaries and Features 1-3 regressions.
Run the complete database-free backend suite, backend pip check, all eight
frontend Node test files, frontend lint/build and tracked/untracked whitespace.
Use the existing installed Python 3.13 and fnm Node 22.23.4; install nothing.
The production build may need the established scoped esbuild access.

Existing evidence may be reused: 236 guarded native passes recorded in
VEHICLE_PROFILE_STATUS.md and ignored feature-4-step-6 logs/XML/cleanup summary,
and the user's November 14, 2026 Chrome 156.0.8078.73 development/preview browser
report. Identify reuse explicitly. Native/browser reruns are not required here;
do not connect to PostgreSQL or start a server merely to repeat evidence.
Do not claim an independent reviewer browser run. Native fault injection,
browser simulations, persisted native behavior and user observations stay separate.
The exact manual cleanup report is: Verified cleanup: all reserved synthetic
accounts, sessions, and vehicles are absent.

Only blueprint/context/review.md and blueprint/context/findings.md may be
edited for the durable audit. Do not repair code, edit specification/status,
accept or dismiss findings automatically, install, stage, commit, complete,
merge, push, deploy, delete branches or start Feature 5. Report any real new
findings with severity, file/line, evidence and smallest recommended resolution.
Record actual reviewer identity/model/context/execution, exact target/spec,
reviewer-run commands, reused evidence, limitations and truthful receipt verdict.

## Commands

- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider -q`: passed; 1169 passed, 236 deselected, one existing Starlette/AnyIO deprecation warning.
- `backend/.venv/Scripts/python.exe -m pip check`: passed; no broken requirements.
- `node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js`: passed; 528 passed, no failures, skips, cancellations or todo.
- `npm --prefix frontend run lint`: passed.
- `npm --prefix frontend run build`: passed using scoped elevated access after sandboxed esbuild could not read an ancestor directory; 59 modules transformed.
- `git diff --check 683e1933a77f7ba056811dbdc7bd97d16374ebc8 bc2db9fc712f03cfab93268076b9662b14dba334` and `git diff --check`: passed; Git reported a line-ending notice on the review record. No untracked files were present.
- `git status --short --untracked-files=all`, `git merge-base main HEAD`, and `Get-FileHash blueprint/context/current-feature.md -Algorithm SHA256`: confirmed target tree, base and frozen spec before review.

## Evidence

- Independently reviewed the complete Feature 4 delta and affected callers across ownership, authentication and mutation policy, validation, locking and transaction boundaries, safe errors and privacy, route/session state, accessibility, fixture cleanup, tests and Features 1-3 regression paths.
- Reused builder-recorded 236 guarded native PostgreSQL passes and exact-cleanup evidence in `docs/verification/VEHICLE_PROFILE_STATUS.md`; this reviewer did not rerun native tests or connect to PostgreSQL. Simulated driver and commit failures remain distinct from real database outages.
- Reused the user's November 14, 2026 Chrome 156.0.8078.73 development and preview browser observations and cleanup report in `docs/verification/VEHICLE_PROFILE_STATUS.md`; this reviewer did not run a browser or server. Failure and legacy-response simulations remain distinct from real persisted behavior.
- User-reported manual cleanup: Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.

## Findings

- None.

## Remaining risk

- Browser observations and native database results were reused as attributed above, not independently rerun. The project has no configured browser test command or automated component DOM runner; actual outage and persisted legacy-row browser behavior were not established by the simulations.
- Overlapping supplied text edits use last-committed behavior; a lost commit acknowledgment remains uncertain and requires deliberate reload, as documented in the feature evidence.


## Vehicle profile implementation and verification evidence

Exact original evidence follows; its input bytes are preserved.

# Feature 4 vehicle profile verification

Build Steps 1-5 were approved separately, with user-performed Step 5 browser
observations recorded below. Step 6 final verification and builder review have
passed; the frozen checkpoint proposal awaits approval before an independent
audit. Step 6 is not fully complete because that review is still pending.
Earlier schema, query, API, automated and native evidence remains in
`blueprint/context/current-feature.md`; it is not a new Step 5 database run.

## Step 5 implementation - November 14, 2026

- One shared `/vehicles/:vehicleId` descriptor drives rendered routing and public
  React Router protected-route matching. Static `/vehicles/new` retains priority.
- Garage headings link to the owned profile. The page displays all public fields,
  exact readings, nulls as `Not recorded`, and unchanged legacy years.
- The page connects the approved detail store to the existing session store;
  session algorithms, cookies, API contracts, SQL and dependencies are unchanged.
  The mounted page owns the store and subscription, including StrictMode effect
  replay, route departure, pagehide, authentication changes and disposal.
- View/edit, changed-only Save, Cancel, inline explicit reading confirmation,
  safe errors and deliberate draft-discard reload are implemented. Uncertain
  saves may already have committed; there is no automatic replay or retry.
- Labels, field errors, live status, deliberate focus, disabled pending controls
  and existing responsive styles support the browser accessibility checks.
- Current-generation successful responses may advance the deadline through the
  existing helper; no deadline-only session request, polling or expiry renewal
  is added. Local expiry clears private state through the existing session gate.

During the agent's Step 5 implementation and automated verification, no
browser-controlled runtime tool was available, no dev/manual server was started,
and no PostgreSQL connection or native test was run. The user's subsequent
manual browser execution and reported cleanup are recorded separately below.

## Step 5 automated results

Executed November 14, 2026 with the installed fnm Node 22.23.4 and backend Python
3.13 environment, without installs. Exact repository-root commands:

```powershell
node --test frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js
npm --prefix frontend run lint
npm --prefix frontend run build
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-4-step-5/backend.xml
backend/.venv/Scripts/python.exe -m pip check
git diff --check
```

| Check | Actual result |
| --- | --- |
| Focused route/detail API/state tests | 288 passed; 0 failed, skipped, cancelled or todo |
| All eight frontend test files | 528 passed; 0 failed, skipped, cancelled or todo |
| Database-free backend suite | 1169 passed; 236 native tests deselected; 11.16 seconds |
| Pip check | No broken requirements found |
| Frontend lint | Passed |
| Production build | Passed; Vite 6.4.5; 59 modules; 1.21 seconds |
| Tracked and untracked source/document whitespace | Passed |

Focused tests reported three experimental Node MockTimers warnings; the complete
frontend run reported five. Backend tests reported one existing Starlette/AnyIO
BlockingPortal deprecation. Lint and the successful build had no warnings. The
initial sandboxed build failed because esbuild could not read ancestor
directories; an approved scoped-access rerun passed without source/configuration
changes. Windows Git may report LF-to-CRLF notices; these are not whitespace
failures. New files were checked with `git diff --no-index --check /dev/null
<path>` without staging (exit 1 with no diagnostics means ordinary differences).

Route regressions use the public matcher and memory-router history: canonical,
encoded, case and trailing variants, static creation precedence, invalid IDs,
deeper unrelated paths, rejection/unavailability and stale history work. Detail
state regressions also cover effect cleanup/replay and replacement mounted
resources. These are logic tests; there is no component DOM/browser runner.
These tests alone do not establish focus, visuals, keyboard, persistence or
real-time idle behavior; the user observations below are separate evidence.
Existing detail, collection, create, credential and session tests stay
in the complete command. Final logs/XML are retained in ignored
`blueprint/.state/staging/feature-4-step-5/`.

## User-performed Step 5 browser observations - November 14, 2026

Executor: the user. Browser: Google Chrome 156.0.8078.73. Environments: both
Vite development and production preview. The user reported completing the
complete Feature 4 manual checklist and that everything worked as specified.
These are user-provided observations, not an agent-controlled browser run or
an independent-review result.

Reported real browser behavior:

- Garage vehicle headings linked to the correct protected profile. Direct
  loads, refresh, Back/Forward, trailing-slash, case and encoded route variants
  worked. Invalid IDs and unrelated paths did not reveal cached vehicle data.
  `/vehicles/new` retained precedence over the dynamic detail route. Private
  profile data stayed hidden while authentication and vehicle loading were
  unresolved.
- View, Edit, Save, Cancel, Back to garage and deliberate reload worked.
  Successful updates persisted after refresh. Cancel discarded temporary edits
  without changing the saved vehicle. Null readings displayed `Not recorded`;
  confirmed zero displayed `0.0`. Text, engine, year, mileage and operating-hours
  updates worked. An unchanged legacy year was omitted during unrelated edits;
  the report does not establish a persisted legacy-row browser test beyond the
  checklist's separately labeled legacy response simulation.
- Lowering or clearing either reading required explicit confirmation. Confirming
  both reading changes worked atomically. Canceling confirmation sent no update
  and retained the draft. Changing a proposed value invalidated confirmation.
  Stale confirmation required renewed review or deliberate reload and was never
  automatically replayed.
- Missing and foreign-owned IDs produced the same safe behavior. Two
  authenticated accounts could not read or update each other's vehicles.
- An uncertain update was not automatically retried and required deliberate
  reload and inspection.
- Vehicle responses had `Cache-Control: no-store`; successful responses had
  `X-GarageGuide-Session-Expires-At`. No extra `/api/auth/session` request occurred
  solely to synchronize a returned deadline. No automatic mutation retry or
  idle polling occurred. Waiting until the visible local deadline cleared
  private identity and vehicle state without an expiry-triggered request.
- Keyboard controls, focus movement, labels, error associations, live
  announcements and repeat-submission prevention worked. Layouts worked at
  375, 768 and 1440 pixels and 200% zoom. Both environments produced the expected
  behavior.

Validation and failure-case browser evidence: the user reported approved safe
feedback for validation, rejected-session, forbidden, unavailable,
malformed-response, timeout, uncertain-update and late-response cases. Simulated
failure cases were restored afterward. These simulation observations are
separate from real backend behavior; they do not establish a genuine PostgreSQL
outage, actual server revocation or rollback of a possibly committed update.
The report does not assign each error case to a real versus simulated trigger,
so no additional trigger details are inferred.

User-reported guarded-backend cleanup, verbatim:

```text
Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.
```

No tests or database connections were rerun by the agent to record this report.
Automated totals above and earlier native PostgreSQL results remain separate.

## Evidence boundaries and review status

The repeatable Step 5 procedure is at the beginning of `BROWSER_CHECKS.md`.
Run it in development and production preview using only the guarded test backend.
Wait for the exact cleanup marker before reporting completion. An absent marker
or failed cleanup blocks acceptance and further native verification.

The dated report above records browser/version, both environments, observations,
simulated cases and exact cleanup with user attribution. The November 13 Feature 3 observations
do not prove this new page. Native results from Steps 2/3 do not prove browser
behavior. Malformed HTTP paths rejected before React loads are Vite-boundary
observations only. Legacy-year browser shims and failure shims are simulations,
not persisted legacy-row or PostgreSQL-outage evidence. Full visible idle expiry
must be observed separately, without replacing it with a short simulated timer.

Step 5 and its user-browser evidence were approved before Step 6 was authorized.
The report and exact manual cleanup above remain unchanged. No new browser
execution or additional observations are claimed by the final verification below.

## Step 6 final verification - November 14, 2026

Executed fresh for this checkpoint with no application/test repairs, dependency
installation, schema change or server startup. There is no combined Verify
command; the configured tests and applicable lint/build gates were run.

Exact commands, from the repository root (Node PATH set to the existing fnm
installation as in the browser guide):

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-4-step-6/backend.xml --tb=short
backend/.venv/Scripts/python.exe -m pip check
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js
npm --prefix frontend run lint
npm --prefix frontend run build
# Settings-only load_settings(testing=True) guard passed without opening a connection.
# Native invocation used RUN_DB_TESTS=1; its prior process value was restored afterward.
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-4-step-6/native.xml -o junit_logging=all -o junit_log_passing_tests=true --tb=short
git diff --check
```

Every untracked proposed file is also checked without staging, using
`git diff --no-index --check /dev/null <path>`; exit 1 with no diagnostics denotes
ordinary added-file differences. Complete status/index, file inventory, diff,
exclusions and raw hashes are recorded in the checkpoint review packet.

| Final check | Actual result |
| --- | --- |
| Complete database-free backend suite | 1169 passed; 236 deselected; 12.36 seconds |
| Complete eight-file frontend Node suite | 528 passed; no failures, skips, cancellations or todo |
| Pip check | No broken requirements found |
| Frontend lint | Passed |
| Production build | Passed; Vite 6.4.5; 59 modules; 1.63 seconds |
| Complete guarded native suite | 236 passed; 1169 deselected; 255.25 seconds |
| Exact cleanup | 234 verified receipts; 376 users, 342 sessions and 123 vehicles verified absent |
| Tracked/untracked-file whitespace | Passed |

Final warnings: each of the two pytest runs emitted the existing Starlette/AnyIO
BlockingPortal deprecation; frontend tests emitted five experimental Node
MockTimers warnings. Pip/lint/build reported no warnings. The build used the
previously established scoped access needed by esbuild; it passed on this final
run without a configuration workaround. Git reports an ordinary LF-to-CRLF
notice for current-feature.md, not a whitespace error.

### Fresh native PostgreSQL and cleanup evidence

The explicit opt-in was set only for native execution. The settings preflight
and fixture code require effective database exactly `garageguide_app_test` and
load only `backend/.env.test`. The native fixture wraps application and test
connections with `SELECT current_database()` as the first statement on each
new physical connection, before exposure or business writes. Cleanup is
registered before writes, operates on exact fixture identities (vehicle ID plus
fixture owner, before sessions/users), and checks absence through separate
guarded connections. No schema initialization, truncation, sequence reset,
broad deletion, or connection/write to another database was performed.

JUnit records 234 exact-cleanup receipts covering 376 tracked synthetic users,
342 sessions and 123 vehicles. These counts describe per-fixture verified
absence, including rows already removed within a test; they are not DELETE
affected-row totals. The two other native cases reserve no records:
`tests.test_health::test_real_database_health` and
`tests.test_user_queries_integration::test_health_transaction_is_read_only_on_native_database`.
All 236 selected native cases passed with no skips, failures or errors, and
there was no cleanup failure. The cleanup aggregator initially assumed both
read-only tests were in the health module; source inspection confirmed the two
exact identities above and the report was corrected without a DB rerun or
application change. Raw XML and the aggregate JSON retain this distinction.

Real PostgreSQL checks cover ownership/isolation, persistence, locked fresh
comparisons, stale/empty-field acknowledgment rejection, atomicity, legacy-year
omission, null/zero, timestamps, and transaction outcomes. Concurrency cases use
synchronization and `pg_blocking_pids` evidence; lock timeout is exercised for
real. Injected preparation/driver/commit acknowledgment failures are simulations
around native transactions, not real PostgreSQL outages. Lost-acknowledgment
tests deliberately demonstrate a real commit followed by a simulated lost
response; cancellation or safe failure does not promise rollback.

### Builder review, exclusions and remaining gates

The builder reviewed the complete tracked/untracked Feature 4 diff and all
specified validation, ownership, locking, confirmation, timestamp, transaction,
safe-error/redaction, mutation-policy, cache/deadline, route, form and lifecycle
boundaries. No confirmed application defect or unexplained file was identified.
No application code or tests changed during this final step. New structures
trace to the approved profile, confirmation and stale-request requirements;
no generic repository, dependency, schema or session-algorithm change was added.
Features 1-3 remain covered by both complete suites and their archives are unchanged.

The 28-file candidate excludes database SQL, dependencies, lockfiles, private
environment files, generated dist/cache output, local recovery/proposal files
and unrelated work. `backend/.env` and `.env.test` remain ignored and untracked;
the index remains empty. `backend/prepapp.txt` is unchanged and excluded.

Limitations remain: overlapping supplied text values use last-committed behavior;
there is no optimistic version or automatic mutation retry/idempotency. A lost
commit acknowledgment requires deliberate reload and inspection. Browser
accessibility, responsive layouts and visible idle evidence are the user's
November 14 report, reused by the builder, not an agent browser run. Simulated
failure statuses and legacy responses are not real outage/persisted legacy-row
browser evidence. Malformed direct HTTP paths rejected by Vite are server-boundary
evidence only; no additional malformed-path observation is inferred. PostgreSQL
remains authoritative for real idle and absolute expiration.

The verified current specification and evidence are frozen for the proposal at
`blueprint/.state/staging/feature-4-checkpoint-proposal.json`; the matching full
diff and review packet are `feature-4-review.diff` and `feature-4-review-packet.md`
in the same ignored directory. Proposed message: `feat: view and update vehicle profiles`.
No independent audit has run for this checkpoint. A future reviewer must state
its actual executed checks and any reused native/user-browser evidence; no
reviewer browser run or receipt freshness is claimed in advance. Step 6 remains
unchecked until its independent-review gate is satisfied. No staging, commit,
audit, completion, merge, push, deployment or later feature is authorized here.


## User browser observations and repeatable Feature 4 procedure

Exact original evidence follows; its input bytes are preserved.

# Manual browser verification

## Feature 4 Step 5: complete and awaiting final review

The user reported completing the complete Feature 4 checklist on November 14,
2026 using Google Chrome 156.0.8078.73 in both Vite development and production
preview, with everything working as specified. The full attributed report is in
[vehicle profile verification](VEHICLE_PROFILE_STATUS.md). It covers routing and
gating, view/edit/save/cancel/reload, persistence, null versus zero, confirmation
and stale acknowledgment, two-account isolation, safe feedback, headers/deadline
synchronization, no polling/retry, visible local expiry without network work,
keyboard/focus/announcements, all three viewport widths and 200% zoom.

The user reported that simulated failure cases were restored afterward; those
are browser simulation evidence, not genuine PostgreSQL-outage or server
revocation evidence. Legacy response simulation remains separate from persisted
legacy-row behavior. No unreported malformed-path server behavior is inferred.
Automated tests and earlier native PostgreSQL results remain separate. No agent
browser run, new test execution or database connection is claimed by this update.

The user reported this exact guarded-backend cleanup confirmation:

```text
Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.
```

Step 5 and this browser record were subsequently approved. Step 6 final automated/
native verification and checkpoint preparation are recorded separately in
VEHICLE_PROFILE_STATUS.md; they add no browser observations or reviewer claims.
The following procedure is retained for repeatability. Its instructions and example
scripts do not add unreported execution details to the user's observations.
Historical Feature 1-3 evidence below remains unchanged.

### Guarded setup and commands

Use repository-root PowerShell terminals. Stop ordinary backends on port 8000.
Use only the existing initialized `garageguide_app_test`; do not run schema SQL.
Remove unintended database overrides privately without printing credentials.
The launcher requires `RUN_DB_TESTS=1`, loads only `backend/.env.test`, verifies
the effective database and `SELECT current_database()` as the first statement
on every physical connection, and registers exact cleanup before writes.

Terminal 1 (guarded backend; leave running until both environments finish):

```powershell
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe backend/tests/manual_registration_server.py
```

It prints three **reserved email addresses**, not accounts or passwords.
Register accounts A and B at `/register` using two of these addresses and your
own temporary passwords (15-128 Unicode characters, matching confirmation).
Use those same passwords at `/login`. Do not use real users/vehicles, print
passwords, inspect/copy cookie values, or export requests/screenshots with secrets.
Use two independent Chrome profiles, or normal plus incognito; two incognito
windows can share cookies. Give every synthetic vehicle a recognizable unique
model, for example `GG-F4-DEV-A-<suffix>`. Both accounts must use only this launcher.

Terminal 2 (set the existing Node PATH in each terminal that uses npm):

```powershell
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173`. Repeat the checklist in preview, rebuilding first:

```powershell
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
npm --prefix frontend run build
npm --prefix frontend run preview
```

Open `http://127.0.0.1:4173`. Cookies are shared across ports on this host;
check the signed-in account when changing environments. Do not start the ordinary
uvicorn command, which uses development settings. The user starts these servers;
the agent has not connected to PostgreSQL for Step 5.

### Real routing, editing, confirmation and isolation

1. Signed out, direct-load a known `/vehicles/ID` URL. No identity or profile may
   flash before the session gate/login flow. Sign in as A, open the garage, and
   use a heading Link. Test direct load, refresh, Back/Forward and switching
   between two A-owned IDs. Repeat `/vehicles/ID/`, `/VEHICLES/ID`,
   `/%76ehicles/ID` and an encoded digit (ID `7` would use `%37`; substitute your
   actual ID). Every protected navigation validates the session before the
   vehicle loads. `/vehicles/new` and encoded/case variants must open creation,
   not a profile. `/vehicles/ID/other` must not display the profile.
2. Invalid IDs (`01`, `0`, `-1`, `+1`, `1.0`, `2147483648`, letters, encoded
   whitespace or non-ASCII digits) show a safe ID error and never old data.
   Direct malformed percent paths may be rejected by Vite before React loads;
   record that as a server-boundary result, not React browser coverage.
3. Create A-owned vehicles with both readings, neither, confirmed zero and no
   engine. Open each heading. Check ID, year/make/model/type/engine, readings,
   creation time and reading-update time. Unknown is `Not recorded`; zero is
   `0.0`. Edit text, preserve case/trim behavior, clear optional engine, Cancel
   and verify no PATCH and no retained draft. Save must remain on the profile,
   announce success and show committed data. Refresh to prove persistence.
   Empty/unchanged edits must not send PATCH. Exercise blank required fields,
   changed year boundaries, invalid decimal precision and field-error clearing.
4. Exercise each reading: unknown to zero/positive, increase, equal value,
   known to lower, known to null, zero to null, and both readings lowered or
   cleared in one save. Lower/clear shows an inline focused confirmation with
   exact current/proposed values (`Not recorded` for clearing). Cancel sends
   nothing and preserves the draft. Editing any business field removes the
   acknowledgment. Only Confirm and save changes sends the second PATCH.
   Repeated click/Enter attempts during pending work produce one request.
   No partial business update may appear after the first 409.
5. For a real stale snapshot, keep two independent windows visibly open and
   sign both into A. In window 1 propose a lower reading and stop at confirmation.
   In window 2 change that same vehicle's reading, then confirm in window 1.
   Expect another 409, no update, and required reload/review; no automatic replay.
   Repeat with window 2 lowering below window 1's proposed value, so the stale
   acknowledgment yields empty `fields`. Window 1 must require reload/review,
   not an empty confirm panel. If a visibility recheck clears the draft first,
   record that privacy behavior and repeat with both windows visible, or use
   the explicitly labeled 409 simulations below for that branch.
6. Reload vehicle first explains that the draft and confirmation will be
   discarded. Keep current draft sends nothing. Discard draft and reload sends
   GET only and shows the current row. A no-op/text-only save preserves reading
   time; an actual reading change, including clearing the final known value,
   updates it. Readings must never become floating-point artifacts.
7. Sign B into the independent profile, create a B vehicle, and use B's ID in
   A's address bar. Repeat A's ID as B. Missing and foreign-owned IDs show the
   same safe 404; no foreign fields appear. For PATCH isolation, leave A's edit
   page visible, sign into B in another tab of the **same** profile, return and
   verify session revalidation clears A's draft before B can view/update it.
   Real two-user API PATCH isolation is separately covered by guarded native
   tests; do not claim this UI check sends a foreign PATCH it does not send.
8. Test logout, same-account relogin, switching accounts, rejected sessions,
   hidden tabs, page departure and Back/Forward with pending GET/PATCH. Delayed
   responses must never restore old identity, vehicle, draft or confirmation.
   A vehicle-only outage may retain a correctable draft; authentication
   unavailability must hide/clear all private content behind the session gate.
9. Inspect only safe Network metadata: successful detail GET/PATCH are 200 with
   `Cache-Control: no-store` and `X-GarageGuide-Session-Expires-At`. Errors have
   no-store and no deadline. PATCH has JSON, CSRF marker and trusted browser
   Origin. No session request is made solely to synchronize a successful
   vehicle response's deadline. No periodic vehicle/session polling or mutation
   retry occurs. Keep the detail/edit page visible and truly idle until its
   full current local deadline: identity, profile, draft and confirmation must
   clear without any expiry-triggered request. Deliberate later navigation,
   refresh, visibility return or Retry may validate again. Record real duration.
10. Verify keyboard-only Edit/Save/Cancel/confirm/reload/navigation, visible
    focus, associated labels/errors, first-error focus, confirmation heading
    focus, success/status announcements and unavailable/not-found focus. Check
    375/768/1440-pixel widths and 200% zoom without horizontal scrolling.
    Repeat registration, login/logout, account, garage and create smoke checks.

### Browser simulations - separate from real persistence/native evidence

Use only the guarded backend. Install the following optional shim in DevTools
on a canonical synthetic profile URL. Set `profileCheck.path` to the exact
relative `/api/vehicles/ID` for that fixture and select `method` GET or PATCH.
It reads no request body, password or cookie and logs nothing. Restore it before
real tests and do not layer it over older shims. Counts are safe request totals.

```javascript
(() => {
  const original = window.fetch.bind(window)
  const check = { path: '/api/vehicles/REPLACE_WITH_SYNTHETIC_ID', method: 'PATCH', mode: 'off', calls: 0 }
  check.restore = () => { window.fetch = original; delete window.profileCheck }
  window.profileCheck = check
  window.fetch = async (resource, options = {}) => {
    if (resource !== check.path || (options.method ?? 'GET') !== check.method || check.mode === 'off') {
      return original(resource, options)
    }
    check.calls += 1
    if (check.mode === 'network') throw new TypeError('Simulated network failure')
    if (check.mode === 'timeout') return new Promise((resolve, reject) => {
      const abort = () => reject(new DOMException('Aborted', 'AbortError'))
      if (options.signal?.aborted) abort()
      else options.signal?.addEventListener('abort', abort, { once: true })
    })
    // Real guarded PATCH may commit; deliberately lose only its browser response.
    if (check.mode === 'lost-response') { await original(resource, options); throw new TypeError('Simulated lost response') }
    if (check.mode === 'late') {
      const response = await original(resource, options)
      await new Promise((resolve) => setTimeout(resolve, 5000))
      return response
    }
    if (check.mode === 'legacy' && check.method === 'GET') {
      const response = await original(resource, options)
      if (!response.ok) return response
      const body = await response.json()
      return new Response(JSON.stringify({ ...body, year: 1800 }), { status: response.status, headers: response.headers })
    }
    if (check.mode === 'malformed') return new Response('invalid JSON', { status: 200 })
    const outcomes = {
      missing: [404, { detail: 'Vehicle not found.' }],
      rejected: [401, { detail: 'Not authenticated.' }],
      forbidden: [403, { detail: 'Request not allowed.' }],
      authentication: [503, { detail: 'Authentication unavailable. Please try again.' }],
      unavailable: [503, { detail: 'Vehicles unavailable. Please try again.' }],
      unexpected: [500, { detail: 'Internal server error' }],
      confirmation: [409, { detail: 'Reading changes require confirmation.', fields: ['mileage'], current_readings: { mileage: '1000.0' } }],
      stale: [409, { detail: 'Reading changes require confirmation.', fields: [], current_readings: {} }],
    }
    const [status, body] = outcomes[check.mode] ?? outcomes.unexpected
    return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } })
  }
})()
```

- For GET, simulate missing/rejected/authentication/unavailable/network/timeout/
  malformed/unexpected. Restore real fetch before deliberate Retry/reload.
  No private vehicle may appear before a current valid response. GET 403 is
  safe feedback, not a claim the normal GET requires mutation headers.
- For PATCH, simulate forbidden, authentication, unavailable, network, timeout,
  malformed and unexpected. Authentication rejection/unavailability gates private
  content. Correctable vehicle failures retain draft; uncertain changes show
  exactly: `The update may have completed. Reload this vehicle and check its
  current values before submitting again.` No replay occurs. Use lost-response
  once for an ordinary text edit, restore, then deliberately reload to inspect
  the actual committed result. This is response-loss simulation, not DB outage.
- For confirmation simulation, begin with fixture mileage `1000.0` and propose
  `900.0`; mode confirmation returns the restricted 409. Confirming again in
  that mode must require reload/review. For the empty-fields branch, first get
  the initial confirmation, switch mode to stale, then explicitly confirm.
  No matched simulated 409 writes reach PostgreSQL.
- For late mode, start a GET or ordinary text PATCH then navigate to another
  ID/logout/change account within five seconds. A forwarded PATCH may commit;
  its late response must not restore stale page state. Restore and deliberately
  inspect the exact fixture afterward. Do not infer rollback from cancellation.
- Legacy-year UI coverage: select method GET and mode legacy for the fixture.
  This forwards the guarded GET and changes only its returned year to `1800`,
  preserving the public shape and headers. Reload, open Edit, change only model,
  restore the shim before Save, and inspect that PATCH omits year. The genuine PATCH
  returns the actual stored year. Separately test changing year to an invalid
  new value. Label this synthetic response coverage; real persisted legacy-year
  behavior is covered by native/API tests, not this browser response simulation.
- Finish with `profileCheck.restore()`. A shim
  401 does not itself revoke the server session or clear an HttpOnly cookie.
  Reconcile with real logout/login afterward. Simulated statuses do not prove
  a genuine PostgreSQL outage, server cookie deletion or real expiration.

### Cleanup and report

Restore shims/blocking, sign out both users, and stop the guarded backend with
Ctrl+C. Wait for this exact message before claiming cleanup or Step 5 acceptance:

```text
Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.
```

The launcher deletes only exact tracked synthetic vehicles (ID plus fixture
owner) before fixture sessions/users and verifies absence through separate
guarded connections. Do not force-kill, truncate, broadly delete, reset sequences
or manually clean ordinary data. If cleanup is not confirmed, stop and report it.
Report execution date, exact browser version, development/preview cases, real
observations, simulated cases, actual full idle observation, limitations and
exact cleanup output. The November 14 report above supplies the user-observed
acceptance and exact cleanup; Step 5 was subsequently approved.


## Reused native cleanup evidence

Exact original evidence follows; its input bytes are preserved.

{
  "nativeSelected": 236,
  "verifiedCleanupReceipts": 234,
  "trackedUsersVerifiedAbsent": 376,
  "trackedSessionsVerifiedAbsent": 342,
  "trackedVehiclesVerifiedAbsent": 123,
  "readOnlyNoRecordsCases": [
    [
      "tests.test_health",
      "test_real_database_health"
    ],
    [
      "tests.test_user_queries_integration",
      "test_health_transaction_is_read_only_on_native_database"
    ]
  ],
  "countsMeaning": "Per-fixture exact identity absence, not affected DELETE row counts; includes records already removed by the test.",
  "aggregationNote": "Initial evidence parser assumed both read-only cases shared a module; exact two verified test identities used instead. No application change, native rerun or cleanup failure."
}


## Historical approved checkpoint inventory and evidence hashes

Exact original evidence follows; its input bytes are preserved.

{
  "schemaVersion": 1,
  "feature": {
    "id": 4,
    "title": "View and update a vehicle profile",
    "buildAttempt": 1
  },
  "frozenAtUtc": "2026-11-15T03:19:29.099368+00:00",
  "branch": "feature/view-and-update-a-vehicle-profile",
  "parentHead": "683e1933a77f7ba056811dbdc7bd97d16374ebc8",
  "baseRef": "main",
  "baseCommit": "683e1933a77f7ba056811dbdc7bd97d16374ebc8",
  "recordedOriginMain": "683e1933a77f7ba056811dbdc7bd97d16374ebc8",
  "fileCount": 28,
  "index": "empty",
  "commitMessage": "feat: view and update vehicle profiles",
  "specification": {
    "path": "blueprint/context/current-feature.md",
    "rawSha256": "ea12c29060490b2fbc0ddb61b723fe764768e8432b6481bffa8be66342175879",
    "byteLength": 66557,
    "status": "verified",
    "snapshot": "blueprint/.state/staging/feature-4-step-6/verified-specification.md"
  },
  "files": [
    {
      "path": "backend/app/routes/vehicles.py",
      "status": "modified",
      "purpose": "Authenticated GET/PATCH profile routes; pre-write mutation policy, sanitized validation/404/409/errors, prepared public response and committed session deadline.",
      "rawSha256": "a2f682679a51ff9ea8c89c0b542da594cbce1c3ac7c701f5513cf1f12fcc9036",
      "byteLength": 10348,
      "gitBlobSha1": "5d519976ecfcaa58da8f34ae1a2e695414e89825"
    },
    {
      "path": "backend/app/vehicle_queries.py",
      "status": "modified",
      "purpose": "Owner-scoped detail lookup and locked partial update; fresh confirmation, latest-row merge, reading timestamp and transaction ordering.",
      "rawSha256": "e34bf1e136fe26470d550043646558792c989ecbf133ec550e6161b3f54b5f0d",
      "byteLength": 6783,
      "gitBlobSha1": "787f6a94dc18f667ffbaaeaadf934d526988c8ff"
    },
    {
      "path": "backend/app/vehicle_schemas.py",
      "status": "modified",
      "purpose": "Canonical IDs, strict supplied-field PATCH/confirmation schemas and pure locked-snapshot comparison; shared Decimal/text/year/public behavior.",
      "rawSha256": "4fdde25a3ee1dac4cd3ad65f14f7537afd11fbc002d52c0c05b25dcc29668bdc",
      "byteLength": 9057,
      "gitBlobSha1": "4c16c35c22b02a48cb761c21067b2328cc2275a6"
    },
    {
      "path": "backend/tests/database_support.py",
      "status": "modified",
      "purpose": "Exact fixture-owned ID/owner authorization for profile operations independent of mutable values.",
      "rawSha256": "ba1cf3ae377db09448dd2cd28da7b13d26c6e62be346475f41e2af480990ae76",
      "byteLength": 12262,
      "gitBlobSha1": "3b3a88855eee40883882603473289788a74b5c2a"
    },
    {
      "path": "backend/tests/manual_registration_server.py",
      "status": "modified",
      "purpose": "Guarded manual detail/update wrappers that preserve callback and exact synthetic ownership tracking.",
      "rawSha256": "4c70af9c9b892626a03d8edcb1add48d837b813fdbd400d6c8ff623ab2eb827b",
      "byteLength": 7091,
      "gitBlobSha1": "a31dfbd1519f5b4c12018753354f3b143d9f5ad3"
    },
    {
      "path": "backend/tests/test_manual_registration_server.py",
      "status": "modified",
      "purpose": "Manual wrapper ordering, callback forwarding, safety rejection and cleanup regressions.",
      "rawSha256": "a408d80a54379739130f69aa70698b74ab7cae570888c469cf7be9a3053eb463",
      "byteLength": 12527,
      "gitBlobSha1": "7faaa349ab2c74aeec0ebf3e21e4996c08218540"
    },
    {
      "path": "backend/tests/test_vehicle_fixture_safety.py",
      "status": "modified",
      "purpose": "Reject untracked identities and verify edited vehicle cleanup remains exact and separately checked.",
      "rawSha256": "228ea6ff075b3750b84e79b4b15720970c2a94ccebba243aecbf3af8ee59f599",
      "byteLength": 7875,
      "gitBlobSha1": "b93780e133003d14bb19f98db2f784dea8beb695"
    },
    {
      "path": "backend/tests/test_vehicle_patch_schemas.py",
      "status": "untracked",
      "purpose": "Database-free ID/year/text/Decimal/null/omission/confirmation/public response contract tests.",
      "rawSha256": "b6ef293ff6835e61df2ed651e4548bbeb5b54391112fba16f6e39c19f2cf17e3",
      "byteLength": 17722,
      "gitBlobSha1": "f2675588c4ab2920cde64ef5deb1da16dfc8dff6"
    },
    {
      "path": "backend/tests/test_vehicle_profile_api.py",
      "status": "untracked",
      "purpose": "Database-free exact profile API, safe errors/policy/headers, transaction preparation and redaction tests.",
      "rawSha256": "967681021607802dd82a04dbbd8eecf1275ef718e92e41d2a46a58abd58e0412",
      "byteLength": 17941,
      "gitBlobSha1": "8c6656759a03e42e657a8f64617e370876a6082a"
    },
    {
      "path": "backend/tests/test_vehicle_profile_api_integration.py",
      "status": "untracked",
      "purpose": "Guarded native ownership/API/confirmation/persistence/legacy/error/commit and exact-cleanup tests.",
      "rawSha256": "e2a39ddaa6e2010c1f0076926f911da1a1b9319779613bc1b706067432629c95",
      "byteLength": 17555,
      "gitBlobSha1": "5257c9d43405c0836c9eb2483e0717653ed60207"
    },
    {
      "path": "backend/tests/test_vehicle_profile_queries.py",
      "status": "untracked",
      "purpose": "Database-free owner-scoped SQL, lock-before-compare, merge, timestamp, transaction and failure tests.",
      "rawSha256": "5983c7e2af06383d872a7cb9c2f7f3a3abe8fe4a2b89adda10f8f5fc5bf1e384",
      "byteLength": 11946,
      "gitBlobSha1": "601ab47f7fa7394d0b54ab1b1551eba0b79a384e"
    },
    {
      "path": "backend/tests/test_vehicle_profile_queries_integration.py",
      "status": "untracked",
      "purpose": "Guarded native detail/update, real locking/blocking evidence, stale confirmation, timestamps and exact cleanup.",
      "rawSha256": "2fb69e0c02bcdeb2acf1c1055bb83f03e6911a805954af40a132db57c3286e74",
      "byteLength": 17152,
      "gitBlobSha1": "0f3224fa28a092c5f3c0a3775a1b7b88e02f260c"
    },
    {
      "path": "backend/tests/test_vehicles.py",
      "status": "modified",
      "purpose": "Preserve collection/routing no-store regressions while allowing the approved new detail route.",
      "rawSha256": "713dcfe6471c601392fd204a5f77777124e52a9ec42f731874e56f646ba32f82",
      "byteLength": 15842,
      "gitBlobSha1": "9a8cc54cbb79dd00ae2b698a554cb61080c5c9c6"
    },
    {
      "path": "blueprint/context/current-feature.md",
      "status": "modified",
      "purpose": "Verified approved Feature 4 specification and implementation/evidence history; checkpoint/audit gate remains pending.",
      "rawSha256": "ea12c29060490b2fbc0ddb61b723fe764768e8432b6481bffa8be66342175879",
      "byteLength": 66557,
      "gitBlobSha1": "b5d54acb9b6e5739539207fada3873c339debd18"
    },
    {
      "path": "docs/verification/BROWSER_CHECKS.md",
      "status": "modified",
      "purpose": "Feature 4 guarded dev/preview procedure, safe simulation guide and attributed November 14 user browser observations.",
      "rawSha256": "76681aa07cf08d8892dcdd4a725dbed8bf45e7f4bd9b61296a8397efb81cd23a",
      "byteLength": 64875,
      "gitBlobSha1": "742179fdfeebd3eb527a6deca7aded5b68610735"
    },
    {
      "path": "docs/verification/VEHICLE_PROFILE_STATUS.md",
      "status": "untracked",
      "purpose": "Separate final automated/native/user-browser/simulation results, cleanup evidence, warnings and limitations.",
      "rawSha256": "b927bfb2ae2e96b52648ac9dbead04209ad4529eeffb61c06f988ea5d1e70298",
      "byteLength": 16960,
      "gitBlobSha1": "82ebd2c48cbd3ca3da9c9c9fe9c53de1959557f0"
    },
    {
      "path": "frontend/src/App.jsx",
      "status": "modified",
      "purpose": "Render the shared protected vehicle profile route alongside the existing static creation route.",
      "rawSha256": "d3f6286aa6c9efa5d529d5c3e600a9e41bd92787308fac4c9ac4d6152fd8a3da",
      "byteLength": 3346,
      "gitBlobSha1": "a08370801d26ecc8292fbcad00ee142462ec04bf"
    },
    {
      "path": "frontend/src/SessionContext.jsx",
      "status": "modified",
      "purpose": "Expose the existing stable session store for private detail state; no authentication algorithm changes.",
      "rawSha256": "b5e91f5708cae4da0e269be576057b9515b341b02eb959d4a24358a626651ee3",
      "byteLength": 1633,
      "gitBlobSha1": "2581bd94d9002c31a750e27c39c4da4eb72576d4"
    },
    {
      "path": "frontend/src/VehicleDetailPage.jsx",
      "status": "untracked",
      "purpose": "Protected profile view/edit, accessible confirmation and deliberate draft-discard reload; mounted-resource lifecycle.",
      "rawSha256": "344b3768e4b85f1854d7ed7274baa83c86a50df7b7ead94bd0966ccdb8d312c3",
      "byteLength": 8768,
      "gitBlobSha1": "79bc4aabfcf4edbf4df7f47e59dc3ef210a59e83"
    },
    {
      "path": "frontend/src/VehiclesPage.jsx",
      "status": "modified",
      "purpose": "Link each garage vehicle heading to its profile using React Router Link.",
      "rawSha256": "b5e0ee098435c89ef038c11d025864cc73f1116eb741115004b40c3743d3f6d7",
      "byteLength": 2998,
      "gitBlobSha1": "81d9f5e1ee2eca6bc666c959701807bbe8104d41"
    },
    {
      "path": "frontend/src/api.js",
      "status": "modified",
      "purpose": "Separate detail GET/PATCH helpers and closed response/error parsing; same-origin timeout/cancellation with no retry.",
      "rawSha256": "5bbf4cbbcc6eb9beec189cc61d49f2955b47299cc1d60746c7c98bd19e9c3b1a",
      "byteLength": 18482,
      "gitBlobSha1": "8223f350c3f20b07d68318a89c4613b786028b2f"
    },
    {
      "path": "frontend/src/styles.css",
      "status": "modified",
      "purpose": "Small responsive profile, action and confirmation layout additions.",
      "rawSha256": "d5049bee2463647f08bebd2eaf4aa8c9cc61a8323d18de4115cae3e745d92187",
      "byteLength": 3750,
      "gitBlobSha1": "d8486a4cf3cc80057a056e6e7110e506c461cb49"
    },
    {
      "path": "frontend/src/vehicleDetailState.js",
      "status": "untracked",
      "purpose": "Separate committed/draft/confirmation state; synchronous pending guard, generation/identity lifecycle and deadline acceptance.",
      "rawSha256": "73792a7322618b286f3a5e7e4c5b489f217ec370b059f0a13f325e7a8098aed8",
      "byteLength": 10433,
      "gitBlobSha1": "d2b639cbf9befcaba4d65106d80f20aa16143186"
    },
    {
      "path": "frontend/src/vehicleRoutes.js",
      "status": "modified",
      "purpose": "One public shared dynamic route descriptor used by actual rendering and protected-session matching.",
      "rawSha256": "0591c6d43f989661e5d2c6969c20e37845627968c1ca296b764c42b0e2f9438a",
      "byteLength": 386,
      "gitBlobSha1": "b503279c98db3ae84f471081cefa7f708e210926"
    },
    {
      "path": "frontend/src/vehicleValidation.js",
      "status": "modified",
      "purpose": "Canonical ASCII IDs, exact string readings, changed-only PATCH, legacy omission and restricted confirmation/error parsers.",
      "rawSha256": "11813fa07a47dac1e86376ceda51b408f82431c7eba4421dd9bff2acfc5913b2",
      "byteLength": 9934,
      "gitBlobSha1": "78dd7bdb4e60fb06c5c47c13c0158d425abc9142"
    },
    {
      "path": "frontend/tests/vehicleDetailApi.test.js",
      "status": "untracked",
      "purpose": "Node detail/PATCH request, ID, response/error, null/zero, confirmation, timeout and cancellation tests.",
      "rawSha256": "8e8a7e82206230d0898f2c23179d15a86b9627bb282dc9de10cbbca3d0612acd",
      "byteLength": 16453,
      "gitBlobSha1": "62a6973a69243a4af741c62f5a2ece87e09d8aba"
    },
    {
      "path": "frontend/tests/vehicleDetailState.test.js",
      "status": "untracked",
      "purpose": "Node draft/confirmation/reload/lifecycle/stale-work/expiry/deadline and mounted-resource replay tests.",
      "rawSha256": "82415c00b27d7a1ab1412cf738cafaa5d4a5bdcc386026dc850d0cf0d12e68cb",
      "byteLength": 21010,
      "gitBlobSha1": "e12d431f008dd241bee9616b9e36097808775242"
    },
    {
      "path": "frontend/tests/vehicleSession.test.js",
      "status": "modified",
      "purpose": "Shared dynamic/static route matching, encoded variants, rejected/unavailable gating, history and session/deadline regressions.",
      "rawSha256": "86146da46e55b93eb1eeacbdf557d573b8d65342b71cd09cee4f7c59f572ef26",
      "byteLength": 14113,
      "gitBlobSha1": "8a32e55a6bd311aac01ac48ef93615be967a88da"
    }
  ],
  "fullDiff": {
    "path": "blueprint/.state/staging/feature-4-review.diff",
    "rawSha256": "dad7118e6b3942559ead1771776b1a2cfe492635b4b986c211fa0d82b2fa0df9",
    "byteLength": 300690
  },
  "reviewPacket": {
    "path": "blueprint/.state/staging/feature-4-review-packet.md",
    "rawSha256": "9f1a0402e46825dc189040770810d03a3c1f5862aa83e0988edfae5970a5b698",
    "byteLength": 17563
  },
  "snapshots": [
    {
      "source": "blueprint/context/current-feature.md",
      "snapshot": "blueprint/.state/staging/feature-4-step-6/verified-specification.md",
      "rawSha256": "ea12c29060490b2fbc0ddb61b723fe764768e8432b6481bffa8be66342175879",
      "byteLength": 66557
    },
    {
      "source": "docs/verification/VEHICLE_PROFILE_STATUS.md",
      "snapshot": "blueprint/.state/staging/feature-4-step-6/verified-profile-status.md",
      "rawSha256": "b927bfb2ae2e96b52648ac9dbead04209ad4529eeffb61c06f988ea5d1e70298",
      "byteLength": 16960
    },
    {
      "source": "docs/verification/BROWSER_CHECKS.md",
      "snapshot": "blueprint/.state/staging/feature-4-step-6/verified-browser-record.md",
      "rawSha256": "76681aa07cf08d8892dcdd4a725dbed8bf45e7f4bd9b61296a8397efb81cd23a",
      "byteLength": 64875
    }
  ],
  "verification": {
    "commands": [
      "backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m \"not integration\" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-4-step-6/backend.xml --tb=short",
      "backend/.venv/Scripts/python.exe -m pip check",
      "node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js",
      "npm --prefix frontend run lint",
      "npm --prefix frontend run build",
      "RUN_DB_TESTS=1 (process-only; prior value restored); backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-4-step-6/native.xml -o junit_logging=all -o junit_log_passing_tests=true --tb=short",
      "git diff --check",
      "git diff --no-index --check /dev/null <each untracked candidate path>",
      "git status --short; git diff --cached --name-only; git rev-parse HEAD main origin/main; git check-ignore backend/.env backend/.env.test"
    ],
    "backendPassed": 1169,
    "backendDeselected": 236,
    "frontendPassed": 528,
    "frontendTestFiles": 8,
    "nativePassed": 236,
    "nativeDeselected": 1169,
    "pip": "passed",
    "lint": "passed",
    "build": "passed",
    "whitespace": "passed",
    "nodeMockTimersWarnings": 5,
    "pytestWarningsPerRun": 1,
    "nativeDatabase": "garageguide_app_test",
    "runDbTests": "1 for native only; prior process value restored",
    "firstStatementConnectionGuard": "SELECT current_database() before exposure on every physical native connection",
    "cleanup": {
      "nativeSelected": 236,
      "verifiedCleanupReceipts": 234,
      "trackedUsersVerifiedAbsent": 376,
      "trackedSessionsVerifiedAbsent": 342,
      "trackedVehiclesVerifiedAbsent": 123,
      "readOnlyNoRecordsCases": [
        [
          "tests.test_health",
          "test_real_database_health"
        ],
        [
          "tests.test_user_queries_integration",
          "test_health_transaction_is_read_only_on_native_database"
        ]
      ],
      "countsMeaning": "Per-fixture exact identity absence, not affected DELETE row counts; includes records already removed by the test.",
      "aggregationNote": "Initial evidence parser assumed both read-only cases shared a module; exact two verified test identities used instead. No application change, native rerun or cleanup failure."
    },
    "rawEvidenceFiles": [
      {
        "path": "blueprint/.state/staging/feature-4-step-6/backend.txt",
        "rawSha256": "1f0d9ef7ea61dbf449400b9ceeb2df2ff56b832a0bc8ee4b1c0f269a8291acf8",
        "byteLength": 7472
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/backend.xml",
        "rawSha256": "83100dc8c199f5de2710b2a64c90a4ae73cc23554ae93f50b08221157ef1275e",
        "byteLength": 167685
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/before.json",
        "rawSha256": "9b399c92fb21b7a092a831c81e651e6b1173d3c96b544c48fe3d2c8173e21ef1",
        "byteLength": 3115
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/build.txt",
        "rawSha256": "896d37f4e1f2d8a3c265d7682c2747720bc3479d48acd284182c71cc017c47f7",
        "byteLength": 764
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/cleanup-summary.json",
        "rawSha256": "1034dce05ba03ae8f57080d0810daffa7028f47f7b08697c10b38112b9c37125",
        "byteLength": 763
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/frontend.tap",
        "rawSha256": "68a210b1155ae1d49b0b374bf41c9b25409bf95bf11f30c8cb20d9a1d91fb292",
        "byteLength": 230432
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/lint.txt",
        "rawSha256": "3aee3900766951425bc0f22e040020d1a4ca51271636336c8230da3ab66fba66",
        "byteLength": 104
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/native.txt",
        "rawSha256": "d7bc761058afef271ae73284d866e76f6d600a8a2e0312720975bc0550d44126",
        "byteLength": 4230
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/native.xml",
        "rawSha256": "2c1b867c23fd14b7fa3fd6d2e9a3a2f7cd48f3911796ff2361f1ac2fdb4efe4b",
        "byteLength": 139423
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/pip.txt",
        "rawSha256": "6326999b2d47daff6338070efad9139a62dd802f33019eab621859ade33fc907",
        "byteLength": 64
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/verified-browser-record.md",
        "rawSha256": "76681aa07cf08d8892dcdd4a725dbed8bf45e7f4bd9b61296a8397efb81cd23a",
        "byteLength": 64875
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/verified-profile-status.md",
        "rawSha256": "b927bfb2ae2e96b52648ac9dbead04209ad4529eeffb61c06f988ea5d1e70298",
        "byteLength": 16960
      },
      {
        "path": "blueprint/.state/staging/feature-4-step-6/verified-specification.md",
        "rawSha256": "ea12c29060490b2fbc0ddb61b723fe764768e8432b6481bffa8be66342175879",
        "byteLength": 66557
      }
    ]
  },
  "browser": {
    "executor": "user",
    "observationDate": "2026-11-14",
    "browser": "Chrome 156.0.8078.73",
    "environments": [
      "Vite development",
      "production preview"
    ],
    "builderReused": true,
    "agentBrowserRun": false,
    "manualCleanupMessage": "Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.",
    "source": "docs/verification/VEHICLE_PROFILE_STATUS.md"
  },
  "builderReview": [
    "Canonical text IDs are validated before coercion on both boundaries. PATCH fields preserve omission/null and reuse strict Unicode/text/Decimal/year rules. Legacy stored years remain readable and omitted on unrelated edits.",
    "Both vehicle ID and actor.user.id bind each detail lookup/lock/update. No unscoped existence probe is used. Public return shapes omit ownership and confirmation metadata.",
    "SELECT FOR UPDATE precedes comparison; fresh locked values drive acknowledgment checks and latest omitted-field merging. Missing/stale acknowledgments reject the complete transaction, including empty-fields 409 outcomes.",
    "clock_timestamp() is used only when a reading changes; no-op/text-only/equal readings preserve the timestamp, while clearing the final known reading records a new time.",
    "Public validation/serialization and response preparation precede context commit/closure. Success returns after cleanup. Known failures translate afterward; uncertain commit acknowledgment does not trigger retries.",
    "The vehicle boundary sanitizes validation, 404/409, expected 401/403/503 and unexpected 500/logging. Mutation policy executes before body parsing/business writes; credential whitelists are unchanged.",
    "No-store applies to vehicle errors/routing and successes. Only successful prepared responses attach the authenticated actor committed deadline; errors do not fabricate a deadline or create a session/cookie.",
    "Actual rendered routing and session classification share route descriptors and React Router public matching. Static /vehicles/new wins; encoded/case/trailing variants are gated and deeper unrelated paths do not render profile data.",
    "Draft/committed/confirmation states remain separate. Pending submission is synchronously guarded. First confirmation is deliberate; stale/second 409 and uncertain mutations require explicit reload/review.",
    "Result acceptance includes route ID, request and authenticated generations. Account changes, same-user relogin, logout, visibility/departure/disposal and expiry cancel/gate private state. User ID equality alone cannot accept old work.",
    "Only current successful vehicle responses can advance deadlines. No automatic polling, expiry API request, deadline-only session request or mutation replay exists. Existing session algorithms and database transactions are unchanged.",
    "Accessibility and responsive conclusions rely on the attributed user browser report, separately from Node logic tests. Complete backend/native/frontend regressions preserve Features 1-3; existing archives and plan are unchanged."
  ],
  "independentReview": {
    "status": "not requested; deferred until approved immutable checkpoint",
    "receipt": null,
    "reviewer": null,
    "step6Checkbox": "unchecked pending fresh audit"
  },
  "exclusions": [
    "database/ and all schema/migration changes",
    "backend/requirements.txt, backend/requirements-dev.txt, backend/pyproject.toml",
    "frontend/package.json and frontend/package-lock.json",
    "backend/.env and backend/.env.test (ignored, untracked and unstaged)",
    "backend/prepapp.txt (unchanged)",
    "node_modules, virtual environments, dist, caches and generated output",
    "blueprint/.state/ including proposal, snapshots, full diff, raw logs/XML and recovery artifacts",
    "Feature 1-3 archives, build-plan progress, unrelated code/docs/configuration",
    "credentials, real passwords, session tokens/cookies and database dumps; deterministic synthetic test fixtures are test data, not real credentials"
  ],
  "limitations": [
    "No independent audit has run or receipt been requested. The builder review is not an independent review. Step 6 remains unchecked until the later fresh-review gate passes.",
    "The November 14, 2026 Chrome 156.0.8078.73 development/preview browser report and exact manual cleanup were supplied by the user and reused by the builder. No agent browser run is claimed.",
    "The eventual reviewer must identify its own executed checks and reused evidence. No reviewer execution, browser run or freshness is claimed in advance.",
    "Browser failure shims and native preparation/driver/lost-acknowledgment injections are simulations; they are not real PostgreSQL outages. A simulated lost response can follow a real commit.",
    "Legacy-year browser response simulation is distinct from persisted legacy-row native/API tests. Malformed HTTP paths rejected before React are Vite-boundary evidence; no extra observation is inferred.",
    "Overlapping supplied text fields use last-committed behavior. No optimistic version, idempotency, automatic mutation retry, deletion or later feature was introduced.",
    "An uncertain PATCH may have committed. Recovery requires deliberate reload and inspection; cancellation does not promise rollback.",
    "Local deadline gating depends on the device clock; PostgreSQL remains authoritative for idle and absolute session validity.",
    "Each pytest run emitted the existing Starlette/AnyIO BlockingPortal deprecation; Node emitted five experimental MockTimers warnings. Git emitted an LF-to-CRLF notice for current-feature.md.",
    "Cleanup aggregation first used an incorrect module-name assumption for the two read-only/no-record cases; the exact verified identities were used instead. No application change, native rerun or cleanup failure occurred."
  ],
  "approval": "not yet granted; no stage, commit, audit, completion or landing performed"
}


## Try it now

Run or do:

Optional, with the documented guarded test backend/Vite running and your reserved synthetic account/vehicle prepared: open `/vehicles`, follow a vehicle heading, select Edit, change Model, then Cancel edit.

Expected:

The saved model remains unchanged and no PATCH request is sent.

This proves:

Cancel discards a local profile draft. This demonstration is guidance only; it is not additional acceptance evidence.


## Preserved input integrity

The offsets below describe this prepared raw archive. The original specification
prefix is independently bound by the completion annotation. Git EOL conversion
uses the recovery contract to reconstruct that exact prefix; source-tree blobs
are compared using Git clean filters.

```json
[
  {
    "label": "findings",
    "source": "blueprint/context/findings.md",
    "offset": 73772,
    "byteLength": 501,
    "rawSha256": "af8c3711b0661426b25606b314c196acc61120470876eb4fab3a547a474dde6a"
  },
  {
    "label": "receipt",
    "source": "blueprint/context/review.md",
    "offset": 74363,
    "byteLength": 6482,
    "rawSha256": "5af67398fd8241b42a2d5cc7199526367af95f09ebf7fb62c5d665065aaca3d2"
  },
  {
    "label": "profileStatus",
    "source": "docs/verification/VEHICLE_PROFILE_STATUS.md",
    "offset": 80973,
    "byteLength": 16960,
    "rawSha256": "b927bfb2ae2e96b52648ac9dbead04209ad4529eeffb61c06f988ea5d1e70298"
  },
  {
    "label": "feature4BrowserRecord",
    "source": "docs/verification/BROWSER_CHECKS.md (exact Feature 4 prefix)",
    "offset": 98065,
    "byteLength": 15745,
    "rawSha256": "de92dec1b98e7cf216cae1717117a6a21e2bc857eb831c1d5eed34229240b368"
  },
  {
    "label": "nativeCleanup",
    "source": "blueprint/.state/staging/feature-4-step-6/cleanup-summary.json",
    "offset": 113912,
    "byteLength": 763,
    "rawSha256": "1034dce05ba03ae8f57080d0810daffa7028f47f7b08697c10b38112b9c37125"
  },
  {
    "label": "checkpointProposal",
    "source": "blueprint/.state/staging/feature-4-checkpoint-proposal.json",
    "offset": 114807,
    "byteLength": 24718,
    "rawSha256": "9e068d0fa67a10465e5c85a8672c2d1409278533c7181966b2e233998ab52493"
  }
]
```
