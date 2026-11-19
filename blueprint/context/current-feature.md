# Feature: Record and review service history

**From build-plan:** feature 5
**Build attempt:** 1
**Branch:** feature/record-and-review-service-history
**Archive:** blueprint/history/features/05-record-and-review-service-history.md
**Status:** Verified by builder; Steps 1-8 complete; awaiting exact checkpoint approval and independent audit; Feature 5 remains unchecked in the build plan

## Goal

Let an authenticated owner create, list, review, edit, and deliberately remove
dated service records for an owned vehicle. Preserve unknown versus confirmed
zero values, historical readings, ownership, and linked records.

Keep Feature 5 as the existing single build-plan item. Do not split, rename,
renumber, or edit the build plan while implementing this specification.

Planning baseline: main and the recorded origin/main both point to
`4bffbb63d278bbe9b62e377d251c501622910e4b`. Before this specification was written,
the tree and index were clean, Features 1-4 were archived and checked complete,
Feature 5 was next unchecked, and the live context files were canonical stubs.
No prior Feature 5 build was found. The archive leaf was absent, its parents
were ordinary directories, its available Git history was empty, and the valid
branch name had no local namespace collision. Build attempt 1 is frozen.
Recheck prerequisites before implementation; do not create the branch yet.

## In scope

- Owner-scoped nested service collection GET/POST and individual GET/PATCH/DELETE.
- Date, type, description, optional mileage/hours, optional USD cost, and notes.
- Strict create, partial-update, removal-confirmation, and public schemas.
- Locked updates/removal, protection for linked records, and safe errors.
- Two protected pages for history/creation and individual review/edit/removal.
- Existing session, CSRF, deadline, cancellation, and private-state integration.
- Database-free, guarded native, frontend, browser, and independent-review evidence.

## Out of scope

- Parts management, schedules, schedule completion, expense screens/summaries,
  uploads, reports, AI, diagnosis, and every later feature.
- Changing vehicle current readings or readings_updated_at from service operations.
- Moving services between vehicles, ownership transfers, force deletion, soft
  deletion, bulk operations, and historical change logs.
- Schema changes, migrations, automatic schema creation, ORMs, Django, new
  dependencies, connection pooling, version columns, and server-side idempotency.
- Pagination, search, automatic mutation retries, polling, and background renewal.
- Changes to the build plan, project-wide workflow configuration, completed
  archives, or unrelated documentation and application behavior.

## Build loop

- The user approved this specification and restored approval between steps in
  the implementation request. Follow workflow.stepReview=every: implement one
  step, run its checks, explain the changes, and stop for approval before the
  next step. Do not change blueprint/config.json or the eight-step structure.
- After implementation approval, create only the frozen branch from the verified
  completed Feature 4 main baseline. Preserve approved planning changes.
- Run relevant checks during implementation. Stop for a blocking test failure,
  failed database guard/cleanup, unexplained unrelated change, or a decision that
  would change approved behavior or scope. Never waive a failing check.
- Database-free steps must not connect to PostgreSQL. The implementation request
  explicitly authorizes guarded native tests and guarded browser setup only in
  garageguide_app_test, under all safeguards below, when their approved step is
  reached. This does not authorize schema initialization or changes.
- Present completed implementation, all file purposes, tests, browser evidence
  or outstanding manual checks, warnings, and limitations together before staging
  or committing. No automatic checkpoint commits are authorized.
- Use $implement, $check, $audit, and $complete in user-facing instructions.
- Ownership and destructive persisted-data operations require a fresh isolated
  $audit independent current against a separately approved immutable checkpoint.
  Prepare the exact checkpoint proposal first; obtain commit approval before
  creating that checkpoint and running the audit. Never self-certify independence.
- $complete, completion commits, landing, push, deployment, branch deletion, and
  later features need separate authorization. Do not mark Feature 5 complete here.

## Build steps

Stop for the user's approval after each implementation step.

- [x] 1. Define service validation and public schemas.
  Add strict create/PATCH/removal models, canonical IDs, an injectable calendar
  date provider, exact Decimal serialization, and focused database-free tests.
  Preserve omitted fields separately from null and allow wider stored dates on
  reads. Reuse existing safe text/reading/ID behavior without changing vehicle
  contracts or adding an unrelated generic validation layer.
  **Done when:** focused tests prove every field boundary, dates, strict extras,
  null/zero, PATCH/no-op preparation, removal confirmation, and public shape;
  the complete database-free backend suite, pip check, and whitespace pass.

  **Step 1 evidence (November 18, 2026):** Created the frozen branch at completed
  Feature 4 HEAD 4bffbb63d278bbe9b62e377d251c501622910e4b after verifying main,
  recorded origin/main, an empty index, and only the approved specification change.
  Added service_schemas.py and two focused database-free schema test files.
  Focused command:
  `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_schemas.py backend/tests/test_service_patch_schemas.py -p no:cacheprovider`
  passed 405 tests in 1.49s. The complete configured database-free backend command
  passed 1574 tests with 236 integration tests deselected in 31.78s. Each pytest
  run emitted one existing Starlette/AnyIO BlockingPortal deprecation warning.
  `backend/.venv/Scripts/python.exe -m pip check` reported no broken requirements.
  `git diff --check` and explicit whitespace checks of all three untracked files
  passed; Git emitted its ordinary LF-to-CRLF notice for the active specification.
  Tests use the existing forbid_database fixture; no PostgreSQL connection,
  native test, route, query, frontend change, schema/dependency change, staging,
  or commit occurred. Review cadence was reconciled with the user's latest
  instruction without changing project-wide settings. Step 2 remains unstarted.

- [x] 2. Add owner-scoped list/create queries and guarded fixtures.
  Add focused service_queries.py with explicit columns and parameterized values.
  Verify the parent owner, prepare responses inside transactions, and extend exact
  fixture reservations, uncertain-insert recovery, and service-first cleanup.
  **Done when:** database-free query/fixture tests and explicitly authorized native
  list/create/isolation tests pass; transaction ordering and exact cleanup are
  verified; vehicle current readings/timestamps remain unchanged.

  **Step 2 evidence (November 18, 2026):** Added service_queries.py for list/create
  only, exact service reservations/tracking/recovery in NativeTestDatabase, and
  conditional service cleanup reporting. No service routes or frontend work.
  Focused database-free service query and service/vehicle/session fixture tests:
  86 passed in 0.71s. Complete database-free backend suite: 1640 passed, 253
  integration tests deselected, in 26.95s. Pip check passed. Complete explicitly
  authorized guarded native suite: 253 passed, 1640 database-free tests deselected,
  in 672.43s, including 17 new service cases and 236 existing regressions.
  Each pytest run emitted the existing Starlette/AnyIO deprecation warning.
  Native guards loaded only test settings and verified every physical connection
  before exposure. All native fixture finalizers passed. The lost-acknowledgment
  native case proved a real INSERT committed without a returned success, then
  recovered the exact service through its reservation; it explicitly verified
  cleanup of 1 service, 1 vehicle, 2 users, and 2 sessions. Failed preparation
  and simulated pre-commit failure left no service committed. These injected
  faults are simulations, not evidence of a real PostgreSQL outage.
  Ignored JUnit artifacts are in blueprint/.state/staging/feature-5-step-2/.
  Default JUnit logging did not retain passing-test stdout, so no aggregate
  per-fixture record-count totals are claimed. Exact cleanup checks ran inside
  the passing finalizers and the dedicated recovery test, using separate guarded
  verification connections. Full details and commands are in
  docs/verification/SERVICE_HISTORY_STATUS.md. Step 3 remains unstarted; no
  schema/dependency changes, staging, commit, audit, or browser run occurred.

- [x] 3. Expose list/create APIs with safe boundaries.
  Add the service router, register it in main.py, apply existing authentication
  and mutation policy, sanitize service errors, and attach approved headers.
  **Done when:** API tests prove empty/populated lists, committed creation, all
  reading/cost combinations, ownership rejection, safe failures, policy ordering,
  response preparation, deadlines, and applicable native/API regressions.

  **Step 3 evidence (November 18, 2026):** Added only collection GET/POST in
  routes/services.py and registered the router in main.py. Reused authenticated
  sessions, mutation policy, the deadline helper, existing nested-vehicle
  no-store middleware, and unchanged Step 2 queries. Added service API unit and
  native suites. Focused API/query command passed 182 tests in 3.08s. Complete
  database-free suite passed 1769 tests with 305 integration tests deselected
  in 19.78s; pip check passed. Targeted guarded native API/registration/user-query/
  health verification passed 64 tests (6 database-free health cases deselected)
  in 84.48s, including 52 new service API cases and 12 existing regressions.
  Each pytest invocation emitted one existing Starlette/AnyIO deprecation.
  Passing stdout retained in ignored step-3 native.xml yielded 62 exact-cleanup
  receipts: 110 tracked users, 104 sessions, 58 vehicles, and 15 services verified
  absent. Two read-only health cases reserved no records. These are tracked
  absence totals, not SQL affected-row counts. Every physical native connection
  remained guarded for garageguide_app_test; no guard or cleanup failed.
  Tests proved policy rejection before body reading/auth/business calls, safe
  errors, cookie preservation/deletion, no-store and success-only exact committed
  deadlines, owned empty histories, identical missing/foreign 404s, isolation,
  null/zero, unchanged vehicle readings, and 201 only after commit and closure.
  Injected preparation/pre-commit/lost-acknowledgment failures are simulations,
  not real database outages. Step 2's full 253 native passes remain earlier
  evidence, not a fresh full 305-case native run. Full commands and limitations
  are recorded in SERVICE_HISTORY_STATUS.md. Step 4 remains unstarted; no
  individual service routes, frontend, schema/dependency changes, staging,
  commit, audit, or browser run occurred.

- [x] 4. Add detail/update/removal queries and linked-record protection.
  Lock the owned service before merging or checking links. Allow no-op saves,
  block actual completion-linked edits, and block either kind of linked removal.
  Add coordinated real PostgreSQL concurrency tests and exact child fixtures.
  **Done when:** tests prove ownership, latest-row merging, atomic rejection,
  preserved linked data, no vehicle-reading changes, commit/rollback/closure,
  uncertain outcomes, and concurrent inserts cannot be silently cascaded away.

  **Step 4 evidence (November 18, 2026):** Added only query-layer detail/update/
  removal and fixed domain errors. Both mutations lock the owner-scoped service
  row first; updates merge raw omitted values from the latest locked row, allow
  no-ops, and block actual completion-linked changes. Removal requires explicit
  confirmation and blocks either kind of link. Guarded fixtures reserve exact
  synthetic part/schedule/completion identities before writes, recover them,
  delete only those children, refuse unexpected links/cascades, and verify exact
  absence before clearing recovery state. Read-only prepared-FK checks enforce
  the existing immediate cascade constraints without modifying the schema.
  Focused query/fixture checks passed 182 cases in 0.60s before the additional
  FK-guard case was added; the final complete database-free suite includes all
  97 new Step 4 cases and passed 1866 tests (353 native cases deselected) in
  15.21s. Pip check passed. The initial native run stopped at one test-observer
  assertion after 26 passes: it counted an intentional verification read as a
  second writable transaction. Cleanup passed. The observer was restricted to
  writable connections; the isolated recheck passed, then the final targeted
  native suite passed 118 tests (6 database-free health cases deselected) in
  176.90s, including all 48 new native cases and 70 service/health regressions.
  This was a test correction; application behavior and approved scope did not
  change. Initial failure, isolated recheck, final results, and cleanup artifacts
  are preserved separately under blueprint/.state/staging/feature-5-step-4/.
  The final native run yielded 117 exact-cleanup receipts: 234 users, 234 sessions,
  132 vehicles, 83 services, 10 part snapshots, 12 completion links, and 13
  schedules verified absent. One read-only health case reserved no fixtures.
  Counts describe tracked absence, not SQL DELETE row totals. No guard or cleanup
  failed. Events and pg_blocking_pids proved both child-insert/removal orderings
  for both link types, fresh link rechecks, latest-row merging, and real lock
  timeouts. Blocked mutations preserved service/child/schedule/vehicle snapshots.
  Preparation/pre-commit/lost-acknowledgment faults were injected simulations;
  lost acknowledgments did not trigger retry. Existing Starlette/AnyIO and Git
  EOL warnings remain. No full 353-case native run or browser run is claimed.
  Step 5 remains unstarted; no routes/frontend/schema/dependency changes,
  staging, commit, or audit occurred in this step.

- [x] 5. Expose individual GET/PATCH/DELETE APIs.
  Require explicit removal confirmation and existing mutation policy; preserve
  fixed 404/409/422 responses and success-only deadline headers.
  **Done when:** database-free and authorized native tests prove exact contracts,
  missing/foreign/wrong-parent indistinguishability, no-op and blocked edits,
  removal and repeated-removal behavior, safe errors, policy, and exact cleanup.

  **Step 5 evidence (November 18, 2026):** Exposed only the three approved
  individual methods through the existing service router and unchanged Step 4
  queries. Added service-ID and removal-confirmation error sanitization, exact
  individual 404 and linked-data 409 mappings, and pre-body PATCH/DELETE policy
  enforcement. DELETE requires the existing strict confirmation model. Response
  preparation and deadline attachment remain inside the query-owned transaction;
  success returns only after commit and closure. Collection routing tests were
  updated for the newly supported individual paths; no PUT was added.
  Focused API/query checks passed 398 tests in 6.19s. The complete database-free
  suite passed 2054 tests with 441 integration cases deselected in 20.79s,
  including all 188 new Step 5 database-free cases. Pip and whitespace checks
  passed. Targeted guarded native verification passed 141 tests (6 database-free
  health cases deselected) in 206.93s: 88 new individual API cases, 52 collection
  API regressions, and one read-only health check. Its 140 cleanup receipts
  verified absence of 280 users, 280 sessions, 149 vehicles, 106 services,
  8 part snapshots, 7 completion links, and 7 schedules. These are tracked
  absence totals across fixtures, not SQL DELETE row counts. No test, guard,
  or cleanup failed in Step 5. Existing Starlette/AnyIO and Git EOL warnings
  remain. Tests covered identical missing/foreign/wrong-parent 404s, no-op saves,
  exact linked conflicts with unchanged snapshots, confirmed and repeated
  removal, canonical IDs, null/zero, redaction, policy before body reads and
  session/business work, 401 cookie deletion, 503 cookie preservation, exact
  success-only deadlines, and commit/closure ordering. Injected failures are
  simulations; lost acknowledgments were never retried. Saved evidence is in
  blueprint/.state/staging/feature-5-step-5/. The full 441-case native suite and
  a browser run were not performed. Step 6 remains unstarted. No frontend,
  schema, dependency, settings, query/fixture changes, staging, commit, or audit
  occurred in this step.

- [x] 6. Add frontend request and state logic.
  Keep collection/create/detail/PATCH/DELETE parsing separate. Validate canonical
  IDs, exact public responses, changed-field PATCHes, null/zero, and fixed errors.
  Model committed records, drafts, confirmation, uncertainty, and request/session
  generations explicitly; reuse existing deadline and authenticated-request logic.
  **Done when:** focused and complete Node tests prove valid/invalid inputs,
  decimal strings, responses, guards, uncertainty, stale work, and expiration;
  lint/build and database-free backend regressions pass.

  **Step 6 evidence (November 18, 2026):** Added all five service request helpers
  to api.js, strict serviceValidation.js, and serviceState.js with separate
  history and record stores sharing the private-request lifecycle. Kept saved
  records separate from drafts, exact decimal strings and null/zero, changed-only
  PATCHes, canonical IDs, safe response/error parsing, explicit removal, and
  synchronous repeat-write prevention. Uncertain writes require deliberate
  reload/inspection; uncertain creation additionally requires acknowledgment
  that an absent entry does not prove failure and resubmission may duplicate.
  Successful creation clears the draft and reloads history, preserving its
  success notice if that GET fails. Cancellation/context checks run before a
  response can affect the shared deadline. Navigation, hidden/departed pages,
  logout, account changes, same-account relogin, disposal, and expiration clear
  private state and reject late work. No polling, expiry request, or automatic
  mutation retry was added. Self-review added a regression for navigation during
  the post-create GET so it cannot later report stale current success.

  Final focused Node run: 219 passed, zero failures/skips, in 357.00ms. Complete
  explicit eleven-file Node command: 747 passed, zero failures/skips, in 909.50ms.
  Complete database-free backend suite: 2054 passed, 441 integration tests
  deselected, in 20.77s. Pip check, lint, production build (60 modules, 1.34s),
  and tracked/untracked whitespace checks passed. Node MockTimers experimental,
  existing Starlette/AnyIO deprecation, and Git LF/CRLF notices remain visible.
  A shell-quoting error in the first auxiliary whitespace/hash script was
  corrected; its read-only rerun passed. No test failure was waived.

  Step 5 backend raw hashes are unchanged. Private environment files remain
  ignored and unstaged. No PostgreSQL connection, native test, browser run,
  React page/route, schema/dependency/configuration change, staging, commit,
  audit, or later-step work occurred. Step 7 remains unstarted. Logs, backend
  JUnit, file hashes, and results are retained in ignored local staging evidence.

- [x] 7. Build both protected pages and verify browser behavior.
  Add the profile link, history/create page, individual view/edit/remove page,
  shared route definitions, accessible forms and confirmation, and responsive CSS.
  Prepare the browser guide and guarded manual server support.
  **Done when:** applicable development and production-preview browser checks are
  recorded with exact cleanup; flows, ownership, null/zero, linked conflicts,
  uncertainty, routing, sessions, stale work, accessibility, and responsive layouts
  pass. If browser execution is unavailable, supply exact manual instructions and
  report this acceptance criterion pending; do not claim source inspection passed it.

  **Step 7 implementation evidence (November 18, 2026):** Added both pages,
  shared labeled fields/read-only values, profile/history links, shared route
  descriptors, responsive CSS, and accessible status/focus/confirmation/reload
  controls. Reused the Step 6 stores/API for drafts, changed-only PATCH, exact
  decimals/nulls, explicit removal, uncertainty, and session generations. History
  distinguishes successful parent loading from an empty list. Confirmed removal
  returns to freshly loaded history with only a fixed nonprivate success flag;
  no private values/drafts enter router state. No polling/auth-sync request.

  Extended test support for guarded manual service access, exact reservations
  before writes, immutable tracking, and callback forwarding. Opt-in
  --service-links seeds exact linked service fixtures only for new vehicles of
  the third reserved account; the first two accounts retain empty histories.
  Existing test-only database/physical-connection guards and exact child-first
  cleanup remain mandatory. No product test endpoint, schema, or dependency.

  Focused Node: 245 passed in 341.26ms. Final complete eleven-file Node run:
  773 passed, zero failures/skips, in 800.79ms. Focused launcher/fixture checks:
  57 passed in 1.05s. Complete database-free backend: 2076 passed, 441 native
  cases deselected, in 21.60s. Pip, lint, build (65 modules, 1.25s), and
  tracked/untracked whitespace passed. Node MockTimers, existing Starlette/AnyIO,
  and Git EOL notices remain. Build used scoped esbuild elevation. A final
  frontend success-announcement change was followed by full Node/lint/build
  reruns. No test failed or was waived.

  No browser tool is available. BROWSER_CHECKS.md contains exact dev/preview
  commands, all real flows, two-account/linked fixtures, failure simulations,
  full visible idle checks, accessibility/layout checks, and the expected exact
  cleanup marker. No server, PostgreSQL connection, native test, or browser run
  occurred during agent implementation. At that handoff, real setup/cleanup and
  browser acceptance were pending; the user report below supersedes that pending
  state. Step 8 is unstarted. No staging, commit, audit, production
  backend, schema/dependency/configuration, or build-plan change occurred.

  **User-performed browser evidence (November 18, 2026):** The user reported
  manually running the Feature 5 checklist with all checks run passing, then
  explicitly confirmed completing the entire checklist in BOTH Vite development
  and production preview. Reported browser version: 157.0.8103.79. This is a
  user-performed report, not agent/reviewer execution. Real service behavior and
  simulated failure cases remain separate; simulations do not prove real
  PostgreSQL outages or server revocation. No additional per-case result or
  numeric idle duration is inferred. The user observed this exact cleanup:
  `Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.`
  Both modes and exact cleanup are confirmed, satisfying Step 7's browser
  acceptance criterion. Step 7 is complete; awaiting review before Step 8.
  This documentation update ran no tests, server, database, or browser. Earlier
  automated/native results remain separate. No staging, commit, or audit.

- [x] 8. Verify the complete feature and prepare the immutable review checkpoint.
  Run complete database-free backend/frontend suites, pip check, lint/build,
  authorized complete native suite, cleanup verification, and tracked/untracked
  whitespace checks. Review the full diff and file inventory; freeze specification,
  evidence, hashes, proposed commit message, and machine-readable checkpoint.
  **Done when:** builder checks and required browser evidence pass and the complete
  review packet is ready before staging/committing. Record independent audit as
  pending until a separately approved checkpoint exists; completion additionally
  requires its fresh passing receipt and no blocking findings.

  **Step 8 final evidence (November 18, 2026):** User approved Step 7 and
  authorized this complete verification pass. No application behavior changed.
  Complete database-free backend: 2076 passed, 441 integration tests deselected,
  in 40.63s. Complete explicit eleven-file Node suite: 773 passed, zero failures/
  skips, in 1846.22ms. Pip check and lint passed. Production build passed with
  65 modules in 2.35s, using the existing scoped esbuild elevation. Tracked and
  untracked candidate whitespace checks passed. Existing Starlette/AnyIO, Node
  MockTimers, and Git LF/CRLF notices remain; no failure was waived.

  The complete authorized native suite passed 441 tests, 2076 database-free
  cases deselected, in 1043.15s. RUN_DB_TESTS=1, only .env.test settings, effective
  garageguide_app_test, first-statement verification on every physical connection,
  and registered exact cleanup remained enforced. Its 439 captured cleanup
  receipts verified absence of 786 users, 752 sessions, 346 vehicles, 174 service
  records, 18 part snapshots, 19 maintenance completions, and 20 schedules.
  These are aggregate tracked fixture identities verified absent, not DELETE
  affected-row counts. The two remaining cases were read-only health checks.
  No guard, cleanup, or test failed. Separate guarded connections verified absence;
  there was no schema initialization/change, truncation, broad delete, or reset.

  All 205 new service native cases and 236 existing native regressions passed,
  including real lock/concurrent-child orderings, isolation, atomic linked blocks,
  no-op/legacy updates, unchanged vehicle readings, exact decimals/nulls, safe
  API errors/headers, transaction ordering, and deliberate fault injections.
  Injected faults/fake clocks remain simulations, not genuine outage evidence.
  The user's November 18 browser/version 157.0.8103.79 report for both dev and
  preview is preserved as user-performed evidence, not rerun or agent/reviewer
  browser execution. No repeat browser check was needed for this documentation-
  only finalization. General reported passes do not add an inferred idle duration.

  Reviewed the full 38-file tracked/untracked delta, all application paths and
  test/fixture coverage. No confirmed blocking defect or unrelated file was
  found. Schema, dependencies/lockfile, private environments, generated output,
  recovery artifacts, build plan, configuration, overview, prior archives, and
  backend/prepapp.txt are excluded. The branch and parent HEAD are unchanged;
  the index is empty. Freeze paths, purposes, raw SHA-256 hashes, commands,
  evidence, and the complete diff in blueprint/.state/staging/
  feature-5-checkpoint-proposal.json, feature-5-review-packet.md, and
  feature-5-review.diff. Proposed message: feat: record and review service history.
  Independent audit is required but pending a separately approved immutable
  checkpoint; review/findings remain canonical stubs. No staging, commit, audit,
  completion, merge, push, or later feature was performed.

## Files / areas

- New backend/app/service_schemas.py, service_queries.py, and routes/services.py.
- backend/app/main.py for router registration; reuse authentication.py and its
  deadline helper without changing the session database algorithm.
- New focused schema/query/API tests and integration counterparts in backend/tests/.
- backend/tests/database_support.py, conftest.py, manual_registration_server.py,
  and fixture/manual-server safety tests for exact synthetic service/child records.
- frontend/src/api.js plus focused serviceValidation.js and serviceHistoryState.js
  and serviceRecordState.js where the distinct state lifecycles warrant them.
- New ServiceHistoryPage.jsx and ServiceRecordPage.jsx; existing VehicleDetailPage.jsx,
  vehicleRoutes.js, App.jsx, and styles.css for links, shared routes, and rendering.
- New frontend/tests/serviceApi.test.js, serviceState.test.js, and
  serviceSession.test.js for request, state, and protected-route/deadline logic.
- docs/verification/SERVICE_HISTORY_STATUS.md, BROWSER_CHECKS.md, and this active
  specification for accurate feature progress and separate evidence categories.
- No database SQL, dependency, lockfile, build-plan, or configuration edits.

## Data / contracts

### Fields and dates

Create accepts only service_date, service_type, description, mileage,
operating_hours, cost, and notes. The first three are required; omitted optional
fields become null. PATCH accepts only these business fields, all optional by
presence. Reject unknown fields, including ownership, IDs, timestamps, parts,
completion metadata, and vehicle reassignment. Do not accept total_cost as an alias.

| Field | Supplied request value |
| --- | --- |
| service_date | Exact ASCII YYYY-MM-DD, a valid calendar date from 0001-01-01 through backend today inclusive; reject numbers, timestamps, whitespace, and impossible/future dates. |
| service_type | Exactly maintenance, repair, inspection, or diagnostic; match the schema without silent case conversion. |
| description | Unicode-safe text, trimmed, nonblank, case/internal formatting preserved. |
| mileage | Decimal string or null, nonnegative, at most one fractional digit, maximum 99999999999.9. |
| operating_hours | Same as mileage. |
| cost | USD decimal string or null, nonnegative, at most two fractional digits, maximum 9999999999.99. |
| notes | Unicode-safe text or null; trim surrounding whitespace, blank becomes null, preserve internal line breaks. |

The existing app calendar convention is backend date.today(), used by the
vehicle-year provider. Define injectable get_current_date() using date.today()
per validation, not an import-time constant. Do not switch to UTC or browser
time. Test date boundaries with fixed providers. The browser must not reject a
valid backend date solely because its local date differs; server date validation
is authoritative and its sanitized error remains usable across midnight.

Public reads accept existing representable PostgreSQL dates in Python's
0001-01-01 through 9999-12-31 range, including future stored dates. An omitted
legacy date remains unchanged during unrelated PATCHes. Do not coerce database
infinity/BC/out-of-range dates into false values; treat unrepresentable rows as
safe unexpected failures, with no partial writes or leaked data.

All supplied text must be valid UTF-8 Unicode without NUL or unpaired surrogates.
Do not introduce new text-length caps. Render user content as React text, never
HTML injection. Strict schemas reject booleans/coercions and hide raw inputs;
sanitized API errors remain necessary in addition to model configuration.

Decimal requests are strings: trim surrounding whitespace, allow ASCII digits
with an optional decimal point followed by one digit for readings or one/two
digits for cost. Normalize leading zeroes. Reject signs, exponents, commas,
empty strings, binary JSON numbers, booleans, NaN/infinity, overflow, and excess
precision. Do not round or clamp invalid inputs. Use Decimal for SQL bindings;
serialize readings with one fractional digit and cost with two. Never use
JavaScript floating-point arithmetic for these values.

Null means not recorded. Reading "0.0" and cost "0.00" mean confirmed zero/free.
Either, both, or neither reading may be known. Historical readings need not
match current vehicle readings or be monotonic between services. Ordinary
historical edits require no Feature 4 odometer-confirmation mapping. Never
update vehicle mileage, operating_hours, or readings_updated_at in this feature.

### PATCH and public shape

- Omission preserves the current locked value; explicit null clears an optional
  field. Blank notes clear notes. Changed blank numeric form controls become null.
- Required date/type/description cannot be null or blank. An unchanged legacy
  date must not be resubmitted by the frontend during an unrelated edit.
- Reject empty PATCH; the frontend sends only genuinely changed business values.
- Valid supplied values equal to stored values return ordinary 200 success,
  including when a maintenance-completion link exists.
- Preserve id, vehicle_id, created_at, vehicle readings, parts, schedules, and
  completion rows. No partial update occurs if any supplied value is invalid
  or the actual edit is blocked by a completion link.

The exact public ServiceRecord fields are id, vehicle_id, service_date,
service_type, description, mileage, operating_hours, cost, notes, and created_at.
IDs are positive PostgreSQL INTEGER identities, created_at is a timezone-aware
PostgreSQL timestamp, service_date is YYYY-MM-DD, and decimals use canonical
strings/null. Return no user ID, child data, credentials, or session information.

Example:

```json
{"id":456,"vehicle_id":123,"service_date":"2026-11-14","service_type":"maintenance","description":"Changed engine oil","mileage":"12500.0","operating_hours":null,"cost":"42.50","notes":null,"created_at":"2026-11-18T16:00:00Z"}
```

### API and ownership

| Endpoint | Success |
| --- | --- |
| GET /api/vehicles/{vehicle_id}/services | 200 with exactly {"vehicle_id":123,"services":[...]} |
| POST /api/vehicles/{vehicle_id}/services | 201 with one complete ServiceRecord |
| GET /api/vehicles/{vehicle_id}/services/{service_id} | 200 with one complete ServiceRecord |
| PATCH /api/vehicles/{vehicle_id}/services/{service_id} | 200 with the committed complete ServiceRecord |
| DELETE /api/vehicles/{vehicle_id}/services/{service_id} | 200 with exactly {"id":456,"vehicle_id":123,"deleted":true} |

Validate framework-decoded vehicle_id and service_id as canonical ASCII decimal
text from 1 through 2147483647 before integer coercion. Reject leading zeroes,
signs, whitespace, non-ASCII digits, fractions, zero, negatives, and overflow.

Only require_authenticated_session supplies the trusted owner. Every parent and
service query must enforce that owner. Individual operations bind service ID,
vehicle ID, and actor user ID through the owned parent. No unscoped existence
probe or browser-supplied owner. Never treat a service belonging to another
vehicle, even one owned by the same user, as matching the nested URL.

Collection operations first establish the owned vehicle in the same business
transaction; listing no services is ordinary success. Select explicit public
columns through owner-scoped joins and order by service_date DESC, created_at
DESC, id DESC. Create via an owner-scoped INSERT SELECT with route vehicle ID
and actor ID, explicit columns, and RETURNING public fields. Identical entries
are allowed and get different IDs; there is no uniqueness/idempotency guarantee.

### Locks, transactions, and linked data

Use short explicitly owned psycopg transactions. Read-only business operations
use read-only connections. Authentication may separately commit a session idle
extension; a business failure does not undo that extension.

For PATCH/DELETE, acquire the owner-scoped service row with SELECT ... FOR UPDATE
before comparing values or checking linked data. Merge PATCH omissions from
the latest locked row. Recheck links in statements after the lock is acquired,
using the normal READ COMMITTED behavior. Do not rely on a pre-lock snapshot.
UPDATE and DELETE predicates must retain nested ownership restrictions, not just
a previously checked bare service ID. Parameterize every variable value.

Concurrent overlapping edits use last-committed-value behavior. No version
column, ETag, or stale-edit guarantee is added. Removal confirmation authorizes
removal of the currently locked record, which another device may have edited;
the interface must not promise it freezes the previously displayed version.

Current schema behavior: deleting service_records cascades to service_parts
and maintenance_completions. It does not delete vehicles, schedules, or catalog
parts. The expense view recalculates from remaining costs. Completion links
derive their date/readings/cost from the service, so editing those values would
change effective completion information without updating a separate snapshot.

Application policy, without changing those foreign keys:

- Removal is blocked if ANY linked service_parts or maintenance_completions row
  exists. Do not expose child rows/counts, delete children to bypass the rule,
  accept a force option, or invoke the cascade intentionally.
- An actual PATCH change is blocked if ANY maintenance_completions link exists.
  No-op saves succeed. Part snapshots alone do not block an edit and remain
  unchanged. Do not recalculate schedules or rewrite linked data.
- Check existence, not child contents, inside the locked transaction. FOR UPDATE
  must coordinate with the foreign-key key-share checks for child insertion.
  Prove both relevant orderings: a committed child blocks later mutation;
  if deletion wins before an insert, that insert cannot commit a dangling child.
  A successfully committed concurrent child must never be silently cascaded away.
- Reject the whole operation before business writes on a blocked outcome.

Prepare/validate public results and response bodies inside the transaction.
Return success only after commit AND connection closure, including DELETE.
Response-preparation failure rolls back; failures attempt rollback where possible
and close before safe translation. A lost commit acknowledgment may mean a write
committed. Do not promise rollback or automatically retry in that case.

DELETE accepts exactly {"confirm_removal":true}; require strict true, reject
missing/false/null/nonboolean confirmation, extras, and malformed bodies with 422.
The UI must obtain deliberate confirmation; Cancel sends no request. A later
DELETE for an absent record returns the same safe individual 404, not invented
success. No automatic retry, undo promise, soft delete, or force-delete behavior.

### Safe errors and headers

| Case | Response |
| --- | --- |
| Missing/foreign parent on collection GET/POST | 404 {"detail":"Vehicle not found."} |
| Missing/foreign/wrong-parent individual record | 404 {"detail":"Service record not found."} |
| Linked removal | 409 {"detail":"Service record has linked data and cannot be removed."} |
| Actual completion-linked edit | 409 {"detail":"Service record is linked to maintenance completion and cannot be changed."} |
| Authentication rejection | Existing 401 {"detail":"Not authenticated."} with unusable-cookie deletion |
| Mutation-policy rejection | Existing 403 {"detail":"Request not allowed."} |
| Authentication DB unavailable | 503 {"detail":"Authentication unavailable. Please try again."}; preserve potentially valid cookie |
| Service business operation unavailable | 503 {"detail":"Service history unavailable. Please try again."} |
| Unexpected failure | 500 {"detail":"Internal server error"} |

Invalid paths/bodies/JSON, extra fields, invalid dates/decimals, empty PATCHes,
and missing removal confirmation return sanitized 422 {"detail":[...]}.
Each entry contains only loc, msg, type. Allow path locations vehicle_id/service_id;
body locations only the seven business fields, confirm_removal, or body root.
Unknown keys map to root, never echo their names/values. Use fixed messages and
allowlisted types for missing, string_type, extra_forbidden, json_invalid,
model_type/model_attributes_type, and value_error. Map other errors to fixed
value_error. Field messages describe the approved rule, never raw input/context.
Do not reuse or broaden the credential email/password validation whitelist.

Require existing exact trusted Origin, application/json with ordinary charset
parameters, and X-GarageGuide-CSRF: 1 for POST/PATCH/DELETE, before body parsing
and business writes. GET requires authentication without mutation headers.
Do not add CORS or change authentication/session/cookie algorithms.

All service responses, including errors and routing responses, have
Cache-Control: no-store. Attach X-GarageGuide-Session-Expires-At only to successful
authenticated 200/201 responses using the existing helper and committed actor
deadline. Never calculate a deadline or perform another session query in a
service handler. Errors do not extend the client deadline.

Keep logs and error responses free of service/vehicle values, bodies, child data,
SQL, driver details, credentials, hashes, session tokens, and cookies. Log only
fixed safe outcomes; no raw exception formatting or traceback containing inputs.

### Frontend and uncertain outcomes

Protected routes:

- /vehicles/:vehicleId/services: history and creation form, reached from profile.
- /vehicles/:vehicleId/services/:serviceId: view/edit/removal page, reached from history.

Share actual route definitions with session classification using React Router's
public matching API. Preserve canonical parameter validation, decoded/case/slash
variants, direct loads, refresh, Back/Forward, and /vehicles/new precedence.
Unrelated/invalid routes never display cached service/vehicle/account information.

History supports loading, empty, populated, unavailable, 404, and deliberate
retry. The record page supports view, Edit, Save, Cancel, Back to history,
validation, linked conflict, unavailable, 404, uncertain outcome, and reload.
Show null as Not recorded; show confirmed reading zero as 0.0 and cost zero as
USD 0.00. Label cost Total service cost (USD) and offer only the four service types.

Keep committed records separate from temporary drafts. PATCH sends changed
business fields only, with explicit null for cleared optional values. Successful
Save stays on detail and displays the committed response. Cancel discards edits.
Successful create clears its form and reloads history through GET; a failed
reload must still report creation success and must not invite a duplicate POST.
Successful remove clears record state, returns to history, and reloads it.

Removal uses an inline accessible confirmation panel stating permanence and
possible newer concurrent edits. Confirm sends one DELETE; Cancel sends none.
Linked-data 409 leaves the record and draft intact and explains the restriction.
Never offer a force option or silently remove child data.

Use relative URLs, credentials: 'same-origin', existing JSON/CSRF headers,
ten-second timeouts, and cancellation. A synchronous in-flight guard and pending
controls prevent repeated mutation submission. Never retry mutations automatically.

For lost acknowledgments, timeouts, transport failures, unexpected/malformed
success responses, or cancelled mutations after dispatch, treat the outcome as
possibly committed. Preserve a safe draft only while the session remains valid,
but gate resubmission until deliberate reload/inspection. Explain specifically:

- Uncertain create: inspect the chosen vehicle's history for the date, type,
  description, readings, and cost. An absent entry after reload does NOT prove
  failure: the original request may still finish. Resubmission can create a
  duplicate, and any later retry must be a deliberate user choice after warning.
- Uncertain edit: reload the record and inspect saved values before editing again.
  Explain that reload discards the draft; obtain deliberate agreement first.
- Uncertain removal: reload history/record. A later 404 proves only that the record
  is currently absent, not which request removed it. Do not replay DELETE.

Known validation/linked-conflict errors preserve correctable drafts. Service-only
availability failures preserve drafts while the session remains valid, with the
mutation uncertainty rules still applied. Authentication failure/uncertainty
gates private UI; rejection, logout, expiry, or account change clears private state.

Track route vehicle/service IDs, authentication generation, navigation/request
generation, pending work, and visibility/disposal. User ID equality alone cannot
accept work after same-account relogin. Cancel or ignore late responses from
old IDs, superseded loads, previous sessions, logout/login, hidden/departed pages,
navigation, expiration, or disposed stores. Stale successes/conflicts cannot
restore data, overwrite a draft, extend a deadline, or report current success.

Accept deadlines only for successful current-generation responses through the
existing reusable session mechanism. Preserve newer deadlines; absent, malformed,
older, or expired headers cannot extend time or authorize private content.
At local deadline equality, clear identity and service state without a request.
No polling, automatic retry, expiry renewal, or deadline-only /api/auth/session
request. PostgreSQL remains authoritative for idle and absolute expiration.

Use semantic forms, labels, associated field errors, first-error focus, clearing
corrected errors, live status announcements, visible focus, keyboard controls,
and explained disabled states. Check 375/768/1440-pixel layouts and 200% zoom.
Never store private drafts or authentication material in browser storage, URLs,
router state, telemetry, or logs. Route URLs carry only record identifiers.

## Testing

No tests or database connections were run while writing this specification.
There is no combined Verify or configured browser-automation command. Reuse
installed pytest, Node tests, ESLint, and Vite; do not add runners or dependencies.

Database-free checks, from repository root using the installed runtimes:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pip check
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js
npm --prefix frontend run lint
npm --prefix frontend run build
git diff --check
```

Run focused new tests during their steps. The complete Node command must include
all eight existing files plus every new test file actually added; adjust the
listed new names if their focused organization changes, never omit a suite.
Also check untracked proposed source/documentation for whitespace before review.

Native verification requires explicit authorization and:

```powershell
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider
```

- Load only backend/.env.test; require RUN_DB_TESTS=1 and effective database
  garageguide_app_test before connecting. Never connect to garageguide_app,
  postgres, or another database during native tests.
- SELECT current_database() is the first SQL statement on EVERY new physical
  connection, including handler, fixture, concurrency, cleanup, and verification
  connections; require exactly garageguide_app_test before exposing it.
- Register finalizers and exact synthetic reservations before writes. Track
  immutable service ID, fixture vehicle ID, and fixture owner independently of
  mutable descriptions/dates. Recover lost insert acknowledgments only through
  exact pre-reserved unique synthetic data under the exact fixture owner/vehicle.
- Test linked records using exact fixture-owned parts snapshots and completion
  links/schedules as test setup only. This does not implement later product features.
  Remove exact child fixtures before service fixtures, then vehicles, sessions,
  users, and remaining owned test parents in foreign-key-safe order. Never invoke
  a service cascade that could remove untracked child data. Fail on unexpected
  children instead of adopting or broadly deleting them.
- Verify exact service/child/vehicle/session/user absence through separate guarded
  connections. No truncation, broad/prefix deletion, sequence reset, schema setup,
  or ordinary-data cleanup. Stop all native verification if guard/cleanup fails.
- Coordinate real two-connection locking tests with events/barriers and PostgreSQL
  blocking evidence, not sleep-only timing. Prove committed child insertion wins
  safely or deletion wins with insertion unable to commit; never silent cascade.
  Verify blocked edits/removals leave service and exact linked rows unchanged.

Cover strict schema boundaries; two-account isolation across all five endpoints;
wrong-parent IDs; null/zero and clearing; latest-row merging; no-op/link rules;
transaction preparation/commit/rollback/closure faults and uncertain acknowledgments;
safe errors/logs; mutation-policy failures before writes; headers; and unchanged
vehicle current readings/timestamps. Preserve Features 1-4 and health/auth/session
regressions. Test live expense-view effects without adding an expense interface.

Frontend tests cover request shapes, exact response matching, fixed errors,
uncertain create/edit/remove, duplicate-submission guards, draft/reload behavior,
protected route variants, stale work across IDs and authentication generations,
and deadline/expiry behavior without polling. Test removal-confirmation cancellation.

Browser checks in development AND production preview use only the guarded test
backend, unique synthetic accounts/vehicles/services, and exact final cleanup.
Check create/list/reload/edit/clear/cancel/remove; two-account privacy; actual
linked-data restrictions where guarded fixtures support them; routing/history;
headers/deadlines; full visible idle expiry; pending controls; uncertainty;
keyboard/focus/errors/announcements; responsive layouts and zoom.

Record automated, native PostgreSQL, user-performed browser, and simulated-failure
evidence separately in SERVICE_HISTORY_STATUS.md and BROWSER_CHECKS.md. Attribute
browser observations to their performer and date; no agent/reviewer browser claim
without execution. Existing November 14 vehicle checks do not prove service flows.
Record exact commands, totals, warnings, cleanup messages, limitations, and any
reused evidence. Synthetic failures are not proof of a real database outage.

## Notes for the AI

- This is one Feature 5 with eight implementation steps. The latest user request
  restores approval between steps. Present each step before beginning the next,
  and provide the complete checkpoint proposal after final verification.
- Implementation and the frozen branch are authorized. Keep database-free steps
  database-free; native tests remain limited to the authorized guarded test
  database. No installation, staging, commit, audit, or later action is authorized.
- Preserve linked-data restrictions exactly. Do not reinterpret confirmation as
  permission to cascade, introduce force deletion, or silently alter historical
  completion information.
- No schema or build-plan edits and no changes to completed Feature 1-4 evidence.
- Before staging/committing, report every changed/untracked file and purpose,
  raw SHA-256 hashes, full diff, exact checks, cleanup, limitations, branch/HEAD,
  index/tree status, and a frozen checkpoint proposal for explicit approval.
- Independent review, completion, landing, push, and deployment retain their
  separate authorization boundaries. Do not begin Feature 6.
