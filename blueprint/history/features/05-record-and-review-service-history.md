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


<!-- blueprint:completion {"schemaVersion":2,"specBytes":51735,"specSha256":"1610df4efb3140b9f0457ecbe6e0e4d1919688a6544dcf7a24a4075e7dc15086","branch":"refs/heads/feature/record-and-review-service-history","head":"a7f55e2f94c67ec3fb955fab3c9c9f4fa2782ebf","baseRef":"refs/heads/main","baseCommit":"4bffbb63d278bbe9b62e377d251c501622910e4b","sourceTree":"dba5bbd4675b7ad898a433f18a2d57e7be815704","landing":"local-merge","absentOptional":[]} -->


## Completion evidence and interpretation

Feature 5 is archived from the exact verified specification above. Its historical
builder status and earlier pending-audit notes are preserved as original evidence;
the passing independent receipt below records the final review outcome. Only
Feature 5 is newly completed. Feature 6 and later work remain unstarted.

The independent reviewer was `/root/feature5_f03_independent_review`, Codex
`gpt-6.2-sol`, in a fresh isolated subagent. Its receipt remains bound to
`a7f55e2f94c67ec3fb955fab3c9c9f4fa2782ebf`, not the later completion commit.
F-01 through F-03 are closed by the reviews recorded in their resolutions.
F-04 is open P2 and carried forward verbatim in the live ledger. It is neither
fixed, closed, accepted, nor silently waived by completion.

The original November 18, 2026 browser version 157.0.8103.79 development and
production-preview checklist, later focused repair observations, and exact
cleanup reports belong to the user. The latest focused report supplied no new
test date or browser version. No agent/reviewer browser execution is claimed.
Native PostgreSQL evidence (441 passes and 439 exact-cleanup receipts) is reused
by the final reviewer and this completion; it was not rerun. Browser simulations,
automated fault injection, real native tests, and real user-browser observations
remain separate. No real PostgreSQL outage is inferred from a simulation.

Known limitations remain: F-04's invalid direct-helper ID handling and weak spy
assertion; no pagination, optimistic versioning, automatic mutation retries, or
server idempotency; uncertain writes require deliberate inspection. Missing
history does not prove create failure, and another POST may duplicate it. A
later removal 404 proves current absence only. Network-backed npm audit was
unavailable in the offline review. Starlette/AnyIO deprecation, Node MockTimers
experimental notices, and Git line-ending notices remain recorded warnings.


## Findings

Only resolved findings are archived under stable Feature 5 IDs.


### Resolved F-01

### 5/F-01 [P1] closed - Correcting the second service entry leaves submission disabled

**File:** frontend/src/serviceState.js:65
**Found:** 2026-11-18 by /audit independent current (quality, tests)
**Why it matters:** A successful POST and history refresh leave `created` set. A validation error on the next entry changes the status from `ready` to `invalid`. Correcting its fields clears the field errors and leaves that status intact. The store then cancels the corrected submission. `frontend/src/ServiceHistoryPage.jsx:40` disables the submit button, and the page hides its reload control in the invalid state. An existing store fixture reproduced the complete sequence with one POST total.
**Suggested fix:** Track the required post-create refresh independently of later form validation. Clear that requirement when history refresh succeeds while preserving the success announcement. Cover a successful create, successful refresh, invalid second entry, correction, and successful second create. Preserve the existing block when the automatic refresh fails.
**Resolution:** The fresh independent review of `113b36db8be3a2bcc05a432559d383af069df0af` confirmed that the store and page gate creation on the outstanding refresh rather than form status. The focused Node regressions verified that correcting an invalid second entry sends a second POST after a successful refresh. Separate `unavailable` and `not-found` cases kept the POST count at one through repeated failed refreshes and permitted the next POST after a successful reload. The complete Node suite also passed.

Rechecked on `a7f55e2f94c67ec3fb955fab3c9c9f4fa2782ebf`. The second-entry, failed-refresh, and navigation-during-refresh regressions passed again. The page and store use the same pending refresh condition.



### Resolved F-02

### 5/F-02 [P1] closed - Valid Unicode in one service record can hide all service history

**File:** frontend/src/serviceValidation.js:49
**Found:** 2026-11-18 by /audit independent current (quality, tests)
**Why it matters:** The backend accepts and preserves U+FEFF at the edge of a service description or note because Python `strip()` leaves it intact. JavaScript `trim()` removes it, so the browser rejects the backend's otherwise valid record. `frontend/src/api.js:392` rejects the collection when any record fails validation. One valid stored record therefore blocks the entire history and its creation form, and the same validation makes that record unavailable on its detail route. A database-free check confirmed this using actual backend model serialization and the frontend validator.
**Suggested fix:** Align service form normalization and public-response validation with the backend's text contract so valid existing records render and unchanged fields stay omitted from PATCH. Cover the same Unicode edge values on both sides and verify that history remains usable.
**Resolution:** The fresh independent review of `113b36db8be3a2bcc05a432559d383af069df0af` verified the backend's shared response fixture, acceptance of both records by the frontend history store, and preservation of the affected record on the detail route. A separate reviewer-run request probe verified that changing only cost sends exactly `{"cost":"10.00"}`. Closure is pending because the same normalization repair introduced the performance regression in F-03.

On `a7f55e2f94c67ec3fb955fab3c9c9f4fa2782ebf`, a fresh independent reviewer compared frontend normalization with all 29 Python whitespace code points and verified U+FEFF, astral text, and internal formatting using actual backend model serialization with the real frontend request and store code. The affected and ordinary records both loaded, detail preserved description and notes, and the cost-only PATCH was exactly `{"cost":"10.00"}`. The replacement trim also passed the F-03 scaling probe. The focused frontend and backend tests passed.



### Resolved F-03

### 5/F-03 [P1] closed - Service text trimming stalls history on valid internal whitespace

**File:** frontend/src/serviceValidation.js:12
**Found:** 2026-11-18 by /audit independent current (performance, tests)
**Why it matters:** The trailing-whitespace alternative tries to match from each position in an internal whitespace run, scanning the remaining run before failing at the next non-whitespace character. That makes validation quadratic in the run length. History validates the same description in the API parser and store. The detail form also runs validation when rendering an edit. The feature accepts uncapped text and preserves internal formatting, so a single valid stored record can make the history and its creation form slow to open. In a reviewer-run Node probe using the real API parser and history store with a mocked two-record response, internal runs of 4,000, 8,000, 16,000, and 32,000 spaces took approximately 29, 121, 506, and 1,432 ms. All four responses were valid.
**Suggested fix:** Replace the suffix search with trimming that scans inward from the two edges once. Preserve Python's whitespace set, U+FEFF, and internal whitespace. Extend the existing shared normalization coverage with a long internal run and repeat the scaling probe.
**Resolution:** The fresh independent review of `a7f55e2f94c67ec3fb955fab3c9c9f4fa2782ebf` verified that the replacement tests whitespace from each edge and stops at the first non-whitespace character. The tested history path performs linear text validation and parsing. A two-record mocked-transport probe returned both exact records at every tested size. Median load durations over 10 measured loads for 4,000, 8,000, 16,000, 32,000, 131,072, and 524,288 interior spaces were 0.393, 0.308, 0.374, 0.599, 2.382, and 7.705 ms. The probe applied no timing threshold. The focused regression and Python whitespace/U+FEFF parity checks passed.



## Carried-forward open finding (not resolved)

### F-04 [P2] open - Null service IDs reach the collection in direct detail and removal requests

**File:** frontend/src/api.js:427
**Found:** 2026-11-19 by /audit independent current (quality, tests)
**Why it matters:** The shared request helper treats `null` as the collection sentinel even for individual operations. A reviewer-run mock transport recorded `getService('7', null)` sending GET and `removeService('7', null, true)` sending DELETE to `/api/vehicles/7/services`. The protected service store rejects the same invalid ID before dispatch, and the collection has no DELETE route. The test at `frontend/tests/serviceApi.test.js:93` expects no dispatch, but uses `assert.fail` inside `fetch`. The request catch converts the thrown assertion into a result the test accepts.
**Suggested fix:** Require a canonical service ID when the operation targets an individual record and assert the mock fetch call count outside the request. Verify the collection GET and POST still operate without a service ID.
**Resolution:**


## Independent review

# Independent Review

**Status:** passed
**Target commit:** a7f55e2f94c67ec3fb955fab3c9c9f4fa2782ebf
**Base commit:** 4bffbb63d278bbe9b62e377d251c501622910e4b
**Base ref:** main
**Spec hash:** 1610df4efb3140b9f0457ecbe6e0e4d1919688a6544dcf7a24a4075e7dc15086
**Prepared by:** codex
**Builder model:** unknown (runtime did not expose exact model)
**Requested reviewer:** codex
**Requested model:** gpt-6.2-sol
**Requested execution:** automatic
**Requested at:** 2026-11-19T23:36:34.823432+00:00
**Workflow:** regular
**Check required:** no

**Reviewer adapter:** codex
**Reviewer model:** gpt-6.2-sol
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-19T23:43:05Z
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** passed
**Check result:** not-required

## Commands

- `git rev-parse HEAD`, `git merge-base HEAD main`, `git ls-files --stage -- blueprint/context/current-feature.md`, `git ls-tree HEAD -- blueprint/context/current-feature.md`, `Get-FileHash blueprint/context/current-feature.md -Algorithm SHA256`, and `git status --porcelain=v1 --untracked-files=all`: pass. Verified target, base, index, tracked spec, raw bytes, and review-only changes.
- `git diff --check 4bffbb63d278bbe9b62e377d251c501622910e4b..HEAD`, `git diff --check`, and `git diff --cached --check`: pass. Git reported the configured LF-to-CRLF conversion notice for the review files.
- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider`: pass. 2,077 passed, 441 deselected, 46.17 seconds.
- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_schemas.py backend/tests/test_service_patch_schemas.py backend/tests/test_service_api.py backend/tests/test_service_record_api.py backend/tests/test_service_queries.py backend/tests/test_service_record_queries.py backend/tests/test_service_fixture_safety.py backend/tests/test_service_link_fixture_safety.py backend/tests/test_manual_registration_server.py -m "not integration" -p no:cacheprovider -q`: pass. 930 passed, 15.65 seconds. Both pytest runs reported one Starlette/AnyIO BlockingPortal deprecation.
- `$tests = Get-ChildItem frontend/tests -Filter '*.test.js' | Sort-Object Name; node --test $tests.FullName`: pass. 777 passed across all 11 files, zero failures, skips, or cancellations.
- `node --test frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js`: pass. 249 passed, zero failures, skips, or cancellations. The frontend test runs used the existing fnm Node v22.23.4 and emitted Node MockTimers experimental notices.
- `backend/.venv/Scripts/python.exe -m pip check`: pass. No broken requirements.
- `npm --prefix frontend run lint`: pass. No errors or warnings.
- `npm --prefix frontend run build`: pass. Vite built 65 modules in 2.15 seconds. The first sandboxed attempt failed resolving the Vite configuration. The same command passed with scoped elevation.
- `node --input-type=module` with in-memory Python schema serialization, mocked transport, actual service API parsers, and actual session and service stores: pass. Verified whitespace parity, mixed history, detail, exact cost-only PATCH, and bounded scaling without a timing threshold.
- `node --input-type=module` with a request-counting mock transport and the current route store: pass. Confirmed the two malformed direct helper calls in F-04 and the store's pre-dispatch rejection.
- `npm --prefix frontend audit`: unavailable within the authorized offline review. See Remaining risk.

## Evidence

- Codex runtime reviewer identity `/root/feature5_f03_independent_review`. The 39-path `4bffbb63d278bbe9b62e377d251c501622910e4b..a7f55e2f94c67ec3fb955fab3c9c9f4fa2782ebf` delta was reviewed against all eight verified build steps and the project standards. Generated artifacts and dependencies were excluded from source review.
- Reviewed strict schemas, sanitized request locations and messages, cache/deadline headers, trusted session ownership, bound nested predicates, and mutation policy before body processing. Reviewed the product query paths and nearby schema/connection code for latest-row merges, row-lock and foreign-key ordering, linked no-op/part/edit/delete rules, response preparation inside transactions, and commit/closure before success. Guarded fixture code reserves exact synthetic identities before writes and verifies child-first cleanup through independent guarded connections.
- Reviewed both protected routes, forms, exact response shape, request/route/authentication generations, lost acknowledgments, refresh and duplicate-submission gates, deliberate confirmation, and deadline handling. The F-01 regressions exercised an invalid then corrected second draft, unavailable and not-found refresh failures, successful deliberate reload, and navigation during refresh.
- Notes and descriptions matched Python for every valid non-NUL BMP code point, including all 29 Python whitespace points. The cross-layer probe also checked astral text, U+FEFF, preserved interior formatting, a mixed two-record history response, the affected record's detail, and a PATCH body of exactly `{"cost":"10.00"}`. Median mocked two-record loads at 4,000 / 8,000 / 16,000 / 32,000 / 131,072 / 524,288 interior spaces were 0.393 / 0.308 / 0.374 / 0.599 / 2.382 / 7.705 ms. The revised trim scans inward only at the edges.
- Reused prior native evidence from `docs/verification/SERVICE_HISTORY_STATUS.md` and inspected the original Step 8 native JUnit and cleanup summary. The JUnit records 441 passes, zero failures, errors, or skips, including 205 Feature 5 native cases. There were 439 exact cleanup receipts covering 786 users, 752 sessions, 346 vehicles, 174 services, 18 part snapshots, 19 maintenance completions, and 20 schedules. The other two cases were read-only health checks. Relevant backend product code, native integration tests, fixture code, and schema match that native checkpoint.
- Reused the user's November 18 browser v157.0.8103.79 report in Vite development and production preview. Also reused the user's focused F-01/F-02 results and later F-03 observations in both modes in `docs/verification/SERVICE_HISTORY_STATUS.md` and `docs/verification/BROWSER_CHECKS.md`. The latest report confirmed mixed history and detail, preserved U+FEFF and interior whitespace, and cost-only PATCH. The exact reported cleanup was `Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.`
- Preserved the original request outcomes and prior finding history in the existing ignored `blueprint/.state/staging/feature-5-original-audit-receipt.md`, `feature-5-pre-f03-audit-receipt.md`, and `feature-5-pre-f03-audit-findings.md` copies.

## Findings

- F-01 [P1] remains closed after independent re-verification.
- F-02 [P1] and F-03 [P1] closed on this checkpoint.
- F-04 [P2] open. Null service IDs reach the collection from two direct API helpers. The protected store prevents those requests, and the collection endpoint has no DELETE route. See `blueprint/context/findings.md`.

## Remaining risk

- The network-backed `npm --prefix frontend audit` was unavailable in this offline review. Pip check verified dependency consistency.
- Native PostgreSQL and browser evidence was reused. This review ran no PostgreSQL connections, native suite, browser, or server. The original browser report is a checklist-level pass, and the latest focused browser report supplies no new date or browser version. Browser failure simulations and automated fault injection are evidence for the simulated scenarios. The scaling measurements came from a mocked response in Node.
- The approved scope leaves service history unpaginated and uses last-committed-value behavior for overlapping corrections. After an uncertain mutation, deliberate inspection still matters because a lost response can follow a committed write.
- F-04 remains open and does not block the independent review gate.


## Implementation commit history

6779cdefa13de9d45f3b0cc968089900037334c6
Parents: 4bffbb63d278bbe9b62e377d251c501622910e4b
Subject: feat: record and review service history


113b36db8be3a2bcc05a432559d383af069df0af
Parents: 6779cdefa13de9d45f3b0cc968089900037334c6
Subject: fix: address service history review findings


a7f55e2f94c67ec3fb955fab3c9c9f4fa2782ebf
Parents: 113b36db8be3a2bcc05a432559d383af069df0af
Subject: fix: trim service text without repeated whitespace scans




## Historical original changes-requested receipt

# Independent Review

**Status:** changes-requested
**Target commit:** 6779cdefa13de9d45f3b0cc968089900037334c6
**Base commit:** 4bffbb63d278bbe9b62e377d251c501622910e4b
**Base ref:** main
**Spec hash:** 1610df4efb3140b9f0457ecbe6e0e4d1919688a6544dcf7a24a4075e7dc15086
**Prepared by:** codex
**Builder model:** gpt-6.2-sol
**Requested reviewer:** codex
**Requested model:** gpt-6.2-sol
**Requested execution:** automatic
**Requested at:** 2026-11-19T02:19:16+00:00
**Workflow:** regular
**Check required:** no

**Reviewer adapter:** codex
**Reviewer model:** gpt-6.2-sol
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-19T02:22:09Z
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** changes-requested
**Check result:** not-required

## Commands

- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider`: pass, 2,076 passed and 441 integration cases deselected; one existing Starlette/AnyIO deprecation.
- `node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js`: pass, 773 passed with zero failures or skips.
- `backend/.venv/Scripts/python.exe -m pip check`: pass, no broken requirements.
- `npm --prefix frontend run lint`: pass.
- `npm --prefix frontend run build`: pass, 65 modules. The sandboxed invocation failed at esbuild's ancestor directory access. The same command passed with scoped escalation.
- `git diff --check 4bffbb63d278bbe9b62e377d251c501622910e4b..6779cdefa13de9d45f3b0cc968089900037334c6` and `git diff --check`: pass.
- Database-free inline checks using the existing frontend state fixture and backend schema serialization: confirmed F-01 and F-02.
- `npm --prefix frontend audit`: unavailable within the authorized offline scope.

## Evidence

- Reviewer identity `/root/feature5_checkpoint_independent_review`. The isolated Codex child inherited the runtime's exact gpt-6.2-sol model without an override and received no builder transcript.
- Reviewed the complete 38-file checkpoint delta and relevant existing schema, authentication, routing, and session code. All five operations bind ownership to the authenticated actor. PATCH and DELETE lock the service row before looking for links. A fresh statement checks links against the locked record while foreign-key checks coordinate concurrent insertions. Public response preparation occurs within each business transaction and success returns after context exit.
- Reviewed the removal confirmation, mutation uncertainty, session expiry, cancellation, and request generation paths. Existing frontend tests cover late results after route departure, sign-out, and account changes. The two independently reproduced findings exercise sequences the existing tests miss.
- Reused Step 8 builder evidence from `docs/verification/SERVICE_HISTORY_STATUS.md` and `blueprint/.state/staging/feature-5-step-8/native.xml` and `cleanup.json`. The artifacts record 441 guarded PostgreSQL passes, zero failures or skips, and 439 exact fixture cleanup receipts. No PostgreSQL connection was opened during this review.
- Reused the November 18, 2026 user-performed Vite development and production preview browser observations and exact guarded cleanup message from `docs/verification/BROWSER_CHECKS.md`. The isolated reviewer did not rerun the browser checklist. The report gives no measured idle duration.

## Findings

- F-01 [P1] Correcting the second service entry leaves submission disabled.
- F-02 [P1] Valid Unicode in one service record can hide all service history.

## Remaining risk

- Both P1 findings block completion. Repeat the complete independent review against a newly approved checkpoint after repair.
- Network-backed `npm --prefix frontend audit` was unavailable within the authorized offline scope. `pip check` verifies installed compatibility.
- Native PostgreSQL and browser evidence was reused for this checkpoint. Automated fault injections and browser simulations establish behavior under those scenarios.


## Historical repair changes-requested receipt

# Independent Review

**Status:** changes-requested
**Target commit:** 113b36db8be3a2bcc05a432559d383af069df0af
**Base commit:** 4bffbb63d278bbe9b62e377d251c501622910e4b
**Base ref:** main
**Spec hash:** 1610df4efb3140b9f0457ecbe6e0e4d1919688a6544dcf7a24a4075e7dc15086
**Prepared by:** codex
**Builder model:** gpt-6.2-sol
**Requested reviewer:** codex
**Requested model:** gpt-6.2-sol
**Requested execution:** automatic
**Requested at:** 2026-11-19T03:14:06+00:00
**Workflow:** regular
**Check required:** no

**Reviewer adapter:** codex
**Reviewer model:** gpt-6.2-sol
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-19T03:16:56Z
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** changes-requested
**Check result:** not-required

## Commands

- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_schemas.py -k shared_frontend_history_response -p no:cacheprovider`: pass, one focused regression.
- `node --test --test-name-pattern='correcting an invalid second entry|failed history GET|shared backend whitespace' frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js`: pass, four focused regressions.
- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider`: pass, 2,077 passed and 441 integration cases deselected. The existing Starlette/AnyIO deprecation was reported.
- `node --test` with all eleven `*.test.js` files returned by `rg --files frontend/tests -g '*.test.js'`: pass, 776 passed with zero failures or skips on Node v22.23.4.
- `backend/.venv/Scripts/python.exe -m pip check`: pass.
- `npm --prefix frontend run lint`: pass.
- `npm --prefix frontend run build`: pass, 65 modules. The sandboxed invocation failed at esbuild's ancestor-directory access. The scoped build rerun passed.
- `git diff --check` for `main...HEAD`, `6779cdefa13de9d45f3b0cc968089900037334c6..HEAD`, the index, and the working tree: pass.
- Reviewer-only inline Node probes using `node --input-type=module`: pass for mixed list, Unicode detail, and exact cost-only PATCH assertions. Two independent timing probes confirmed F-03.
- `npm --prefix frontend audit`: unavailable within the authorized offline scope.

## Evidence

- Reviewer `/root/feature5_repair_independent_review` ran in a fresh Codex subagent with the runtime's exact inherited model `gpt-6.2-sol` and no builder transcript. Verified the target, local `main` merge base, and frozen tracked spec hash. Reviewed all 39 changed files in `4bffbb63d278bbe9b62e377d251c501622910e4b..113b36db8be3a2bcc05a432559d383af069df0af` and all eight changes from `6779cdefa13de9d45f3b0cc968089900037334c6` to the target, along with relevant schema, authentication, and session code. Generated and third-party material was outside the code scope.
- Reviewed actor-derived ownership, parameterized nested SQL, strict input schemas, safe errors and cache headers, row locking before link checks, response preparation inside transactions, and return after transaction exit. The indexed owner/date and link predicates avoid per-record database reads. Reviewed guarded fixture ordering, cancellation, expiration, and route generations against the tests. No new security finding was identified.
- Reviewer-run regressions proved that the second corrected submission proceeds after a successful refresh and that failed refreshes keep creation blocked until a successful reload. Cross-language normalization and request probes preserved U+FEFF in mixed history and detail and omitted it from the cost-only PATCH payload. The performance probe exercised the same list parser and store with synthetic records and found quadratic trimming of permitted internal whitespace.
- Preserved the original `changes-requested` receipt at `blueprint/.state/staging/feature-5-original-audit-receipt.md` and verified SHA-256 `ae2a09ef15d53ab0ef89ab48f7109da5a5f2d5e0093888dd7729dc3a520847e4`.
- Reused Step 8 guarded PostgreSQL evidence from `docs/verification/SERVICE_HISTORY_STATUS.md`, independently reading the local `native.xml` and `cleanup.json` artifacts. They report 441 passes, zero failures or skips, and 439 exact cleanup receipts verifying absence of 786 users, 752 sessions, 346 vehicles, 174 service records, 18 part snapshots, 19 maintenance completions, and 20 schedules. The two remaining cases were read-only health checks.
- Reused the user's focused F-01 and F-02 browser checks in Vite development and production preview from `docs/verification/SERVICE_HISTORY_STATUS.md`, including the simulated failed refresh and the exact report `Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.` This focused report is separate from the earlier full November 18, 2026 browser run.

## Findings

- F-03 [P1] open. Service text trimming stalls history on valid internal whitespace. The reviewer measured approximately 29, 121, 506, and 1,432 ms for internal runs of 4,000, 8,000, 16,000, and 32,000 spaces through the API parser and history store, respectively.
- F-02 [P1] fixed. Unicode correctness was reverified. Closure is pending because the same repair introduced F-03.
- F-01 [P1] closed. Independent focused and complete tests verified the corrected create and required refresh behavior.

## Remaining risk

- F-03 and the pending closure of F-02 block completion. Repair the trim and review the complete delta at a newly approved checkpoint.
- Network-backed `npm --prefix frontend audit` was unavailable within the authorized offline scope. The local `pip check` checked installed Python dependency compatibility.
- Native PostgreSQL and browser observations were reused from recorded evidence. This review ran no database connection or browser session. The timing measurements are from Node and a mocked response.


## Historical findings before the F-03 repair

# Findings

> **Generated file.** The findings ledger: review findings raised by `/audit`
> against the work in progress, each with a durable ID, severity (P0-P3), and
> status. `/implement` marks repaired findings `fixed`, a later `/audit` pass
> moves them to `closed`, and `/complete` refuses to land while any P0 or P1
> finding is `open` or `fixed`, then archives resolved findings with the work
> and resets this file.

### F-01 [P1] closed - Correcting the second service entry leaves submission disabled

**File:** frontend/src/serviceState.js:65
**Found:** 2026-11-18 by /audit independent current (quality, tests)
**Why it matters:** A successful POST and history refresh leave `created` set. A validation error on the next entry changes the status from `ready` to `invalid`. Correcting its fields clears the field errors and leaves that status intact. The store then cancels the corrected submission. `frontend/src/ServiceHistoryPage.jsx:40` disables the submit button, and the page hides its reload control in the invalid state. An existing store fixture reproduced the complete sequence with one POST total.
**Suggested fix:** Track the required post-create refresh independently of later form validation. Clear that requirement when history refresh succeeds while preserving the success announcement. Cover a successful create, successful refresh, invalid second entry, correction, and successful second create. Preserve the existing block when the automatic refresh fails.
**Resolution:** The fresh independent review of `113b36db8be3a2bcc05a432559d383af069df0af` confirmed that the store and page gate creation on the outstanding refresh rather than form status. The focused Node regressions verified that correcting an invalid second entry sends a second POST after a successful refresh. Separate `unavailable` and `not-found` cases kept the POST count at one through repeated failed refreshes and permitted the next POST after a successful reload. The complete Node suite also passed.

### F-02 [P1] fixed - Valid Unicode in one service record can hide all service history

**File:** frontend/src/serviceValidation.js:49
**Found:** 2026-11-18 by /audit independent current (quality, tests)
**Why it matters:** The backend accepts and preserves U+FEFF at the edge of a service description or note because Python `strip()` leaves it intact. JavaScript `trim()` removes it, so the browser rejects the backend's otherwise valid record. `frontend/src/api.js:392` rejects the collection when any record fails validation. One valid stored record therefore blocks the entire history and its creation form, and the same validation makes that record unavailable on its detail route. A database-free check confirmed this using actual backend model serialization and the frontend validator.
**Suggested fix:** Align service form normalization and public-response validation with the backend's text contract so valid existing records render and unchanged fields stay omitted from PATCH. Cover the same Unicode edge values on both sides and verify that history remains usable.
**Resolution:** The fresh independent review of `113b36db8be3a2bcc05a432559d383af069df0af` verified the backend's shared response fixture, acceptance of both records by the frontend history store, and preservation of the affected record on the detail route. A separate reviewer-run request probe verified that changing only cost sends exactly `{"cost":"10.00"}`. Closure is pending because the same normalization repair introduced the performance regression in F-03.

### F-03 [P1] open - Service text trimming stalls history on valid internal whitespace

**File:** frontend/src/serviceValidation.js:12
**Found:** 2026-11-18 by /audit independent current (performance, tests)
**Why it matters:** The trailing-whitespace alternative tries to match from each position in an internal whitespace run, scanning the remaining run before failing at the next non-whitespace character. That makes validation quadratic in the run length. History validates the same description in the API parser and store. The detail form also runs validation when rendering an edit. The feature accepts uncapped text and preserves internal formatting, so a single valid stored record can make the history and its creation form slow to open. In a reviewer-run Node probe using the real API parser and history store with a mocked two-record response, internal runs of 4,000, 8,000, 16,000, and 32,000 spaces took approximately 29, 121, 506, and 1,432 ms. All four responses were valid.
**Suggested fix:** Replace the suffix search with trimming that scans inward from the two edges once. Preserve Python's whitespace set, U+FEFF, and internal whitespace. Extend the existing shared normalization coverage with a long internal run and repeat the scaling probe.
**Resolution:**


## Preserved service-history verification record

# Service history verification status

Feature 5: Record and review service history. One build-plan item covering
create, list, edit, and remove. Branch:
`feature/record-and-review-service-history`; parent HEAD:
`4bffbb63d278bbe9b62e377d251c501622910e4b`.

Steps 1-7 were approved. Step 8 builder verification passed; the exact 38-file
checkpoint is prepared for review before staging/committing. The user's November
18 browser evidence is preserved. Independent audit remains pending an approved
immutable checkpoint. The build-plan item is unchanged and unchecked.

## Automated database-free evidence

Fresh Step 2 checks:

| Check | Result |
| --- | --- |
| Focused service queries and service/vehicle/session fixture tests | 86 passed in 0.71s |
| Complete backend database-free suite | 1640 passed, 253 integration tests deselected, in 26.95s |
| Backend pip check | No broken requirements found |
| Tracked and proposed untracked-file whitespace | Passed; final documentation read-back and scope checks also passed |

Exact test commands:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_queries.py backend/tests/test_service_fixture_safety.py backend/tests/test_vehicle_fixture_safety.py backend/tests/test_session_fixture_safety.py -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-5-step-2/backend.xml
backend/.venv/Scripts/python.exe -m pip check
git diff --check
```

The new query and fixture suites contain 53 and 13 database-free cases,
respectively. They cover bound owner/vehicle parameters, explicit columns,
ordering, Decimal/null bindings, no vehicle UPDATE, parent-not-found behavior,
preparation before commit, rollback/close/translation ordering, uncertain closure,
exact reservation/identity tracking, collision refusal, physical database guards,
cleanup recovery, and refusal to cascade through unexpected linked records.

One existing Starlette/AnyIO BlockingPortal deprecation warning appeared in each
pytest invocation. Git reports its ordinary Windows LF-to-CRLF notice for the
active specification. No failure was waived.

## Native PostgreSQL evidence: Step 2

The user explicitly authorized Step 2 tests only in garageguide_app_test.
The complete native suite was applicable because the shared native fixture was
extended. It passed 253 tests in 672.43s (11 minutes 12 seconds), with 1640
database-free tests deselected and zero failures, errors, or skipped selected
tests. This includes 17 new service query cases and all 236 existing native
registration, authentication, session, health, vehicle, locking, and concurrency
regressions. The new 17 cases are included in the 253, not additional passes.

```powershell
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-5-step-2/native.xml
```

Tests load only backend/.env.test and reject a different effective database.
Every physical test connection verifies SELECT current_database() as its first
statement, before callers receive it. No schema was initialized or changed.

Service reservations require an exact fixture-owned vehicle/user and collision
checks before writes. Successful creations track immutable service/vehicle/owner
IDs. Lost-acknowledgment recovery uses the exact pre-reserved values and owner
join. Cleanup locks exact services, refuses unexpected part/completion children,
and deletes services before vehicles, sessions, and users. A separate guarded
connection verifies absence. Recovery metadata is retained if cleanup fails.

All native fixture finalizers passed, including their separate-connection exact
absence checks. The dedicated lost-acknowledgment test explicitly asserted
cleanup_verified, cleanup_service_count=1, cleanup_vehicle_count=1, and
cleanup_counts=(2 users, 2 sessions), and then independently checked absence of
the exact service and vehicle IDs through another guarded connection.

The full-run JUnit artifact records all 253 passing outcomes with no teardown
errors. Its default logging did not retain passing-test stdout, including the
printed cleanup-count lines. Therefore no aggregate user/session/vehicle/service
record-count totals are inferred or claimed from that artifact. This is a
reporting limitation, not a failed cleanup check; no tests were rerun merely
to regenerate console receipts.

Native tests proved empty owned histories, identical missing/foreign outcomes
for both operations, two-account and same-owner two-vehicle isolation, all eight
null/zero combinations, maximum exact decimals, service-date/created-at/ID
ordering, identical distinct creations, PostgreSQL creation timestamps, and
unchanged vehicle current readings and readings_updated_at. Response preparation
ran while the INSERT was still invisible through another connection, and success
returned only after the write connection closed. Rollback and lost-acknowledgment
cases exercised real PostgreSQL transactions with the injected failures below.

## Simulated failures and limitations

The native failure tests inject a response-preparation exception, a failure before
commit, and an OperationalError after a real committed INSERT and closed connection.
The last case proves a saved record can remain after the caller receives an
availability failure and tests reservation-based recovery without retrying INSERT.
These are controlled simulations, not evidence of a real PostgreSQL outage.

Lists are unpaginated; identical records are allowed. A lost acknowledgment can
leave creation uncertain, so callers must not automatically retry. Vehicle current
readings and readings_updated_at are untouched. Step 3 adds the collection HTTP
boundaries described below. Step 4 adds individual queries and linked-record
concurrency verification. Step 5 adds the individual HTTP boundaries below.
Frontend behavior remains later work.

## Step 3 verification: collection APIs

Only GET and POST /api/vehicles/{vehicle_id}/services were added. The service
router uses require_authenticated_session and passes its actor and validated
vehicle ID to the unchanged Step 2 query functions. No ownership fields are
accepted in the body. An owned empty history is ordinary 200 success; missing
and foreign-owned parent vehicles both return the same fixed 404.

POST checks existing trusted Origin, JSON content type, and CSRF marker before
FastAPI reads/parses the body or invokes authentication/business dependencies.
GET needs no mutation headers. Error locations, messages, and types use a
service-specific allowlist without widening the credential whitelist. Raw
inputs/context, SQL/driver details, private values, and cookies are never logged
or echoed in errors. Unexpected errors take the fixed generic 500 path.

The query's preparation callback constructs the public JSON response and attaches
the already committed session deadline inside the business transaction. The route
returns it only after successful commit and connection closure. Prepared success
is discarded on failure. The existing vehicle-prefix middleware covers no-store
on nested errors/routing responses; the new route boundary also sets no-store.
Only successful 200/201 responses include the exact actor deadline. There is no
new deadline calculation, additional session query, or cookie issuance. A 401
clears an unusable cookie; an authentication/service 503 preserves it.

| Fresh Step 3 check | Result |
| --- | --- |
| Focused new API and existing service-query tests | 182 passed in 3.08s |
| Complete database-free backend suite | 1769 passed, 305 integration cases deselected, in 19.78s |
| Native API and selected regressions | 64 passed, 6 database-free health cases deselected, in 84.48s |
| Native service API subset | 52 new cases, included in the 64 |
| Existing native regression subset | 12 registration/user-query/health cases, included in the 64 |
| Pip check | No broken requirements found |
| Tracked/untracked whitespace and scope checks | Passed |

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_api.py backend/tests/test_service_queries.py -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-5-step-3/backend.xml
backend/.venv/Scripts/python.exe -m pip check
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_api_integration.py backend/tests/test_registration_integration.py backend/tests/test_user_queries_integration.py backend/tests/test_health.py -m integration -p no:cacheprovider -x -o junit_logging=all --junitxml=blueprint/.state/staging/feature-5-step-3/native.xml
git diff --check
```

The complete database-free run includes all existing authentication/session,
registration, health, and vehicle/profile regressions. The targeted native run
did not rerun the complete 305-case native suite. Step 2's 253 native passes,
including query ordering tie-breakers and maximum decimal values, remain prior
evidence for unchanged business/fixture code, not newly executed Step 3 results.
Existing Starlette/AnyIO and Git EOL warnings remain unchanged; no failure was waived.

### Step 3 native cleanup and transaction evidence

All 64 native tests passed with zero failures/errors/skips and no guard or cleanup
failure. Passing stdout was retained with a per-invocation pytest option, without
changing project-wide settings. Its 62 fixture-backed cleanup receipts verify
110 users, 104 sessions, 58 vehicles, and 15 services absent through separate
guarded connections. Counts refer to tracked identities verified absent across
fixtures, not SQL DELETE affected-row totals. Two cases reserved no records:

- tests.test_user_queries_integration::test_health_transaction_is_read_only_on_native_database
- tests.test_health::test_real_database_health

Ignored cleanup.json contains the per-test receipts and aggregation. Native
assertions also verified a separate connection could not see a service while its
success response was being prepared, then could see it after 201 and connection
closure. Response-preparation/pre-commit exceptions left no service committed.
An injected lost acknowledgment after a real commit returned safe 503 without
a deadline or cookie deletion, left one saved service, and recovered/deleted that
exact service before parent cleanup. These failures were simulations, not real
PostgreSQL outages. No mutation was automatically retried.

Native tests additionally proved null versus zero across all eight combinations,
identical distinct creations, owner/parent isolation, unchanged vehicle readings,
safe validation, policy denial without session extension/business writes,
unusable-session 401 deletion, exact success deadlines, logout, and public health
behavior. Individual service routes and frontend work were not introduced.

## Step 4 verification: individual queries and linked fixtures

Added get_service, update_service, and remove_service without exposing new HTTP
routes. All reads, row locks, link checks, UPDATEs, and DELETEs bind service ID,
vehicle ID, and the trusted actor's user ID through the parent vehicle. Missing,
foreign-owned, and wrong-parent requests share ServiceNotFoundError and its fixed
message. The existing collection queries and API behavior remain intact.

Update/removal select the owned row FOR UPDATE OF s before comparisons or link
queries. Updates merge raw omitted values from that latest locked row, preserving
legacy dates and stored formatting. No-op saves commit without UPDATE, including
completion-linked records. Actual edits with completion links fail atomically;
part snapshots alone permit edits. Removal requires strict explicit confirmation
and fails if either link type exists. Fixed domain errors contain no child IDs,
counts, service values, SQL, or driver details.

Public output is prepared/validated inside the transaction. Success returns
after commit and closure. Known failures roll back and close; lost acknowledgments
may leave an already committed edit/removal and are never retried. IDs, parent,
creation time, vehicle current readings/readings_updated_at, linked snapshots,
and maintenance baselines remain unchanged by service edits.

### Step 4 fixtures and cleanup

Part snapshots and schedules receive unique reserved synthetic names under exact
tracked owners/parents before INSERT. Completion reservations verify the exact
reserved schedule and service and record their immutable ID tuple before INSERT.
Recovery uses these exact reservations and tracks resulting IDs, independent of
mutable service values. Child creation in tests does not implement parts or
maintenance product functionality.

Cleanup deletes exact completion links, part snapshots, and then schedules before
services, vehicles, sessions, and users. Every DELETE retains exact identities
and owner/parent predicates. Schedule cleanup locks its row and refuses remaining
unexpected completion links; service cleanup retains its existing refusal of
unexpected children. No broad deletion or intentional cascade is used. Separate
guarded connections verify all tracked child/service/parent identities absent;
failed verification retains recovery metadata and stops native testing.

The native preflight also verifies the existing immediate cascade foreign keys
using SELECT-only catalog inspection before synthetic setup. A missing/deferred
required key stops writes rather than changing the schema. Every physical
connection still checks current_database() as its first statement, and settings
remain restricted to garageguide_app_test with RUN_DB_TESTS=1 and .env.test.

### Step 4 results and exact commands

| Check | Result |
| --- | --- |
| Focused new/existing query and fixture tests | 182 passed in 0.60s before the final FK-guard test was added |
| Final complete database-free suite | 1866 passed, 353 integration cases deselected, in 15.21s; includes all 97 new Step 4 cases |
| Isolated corrected native closure-observer test | 1 passed in 1.58s |
| Final targeted native suite | 118 passed, 6 database-free health cases deselected, in 176.90s |
| New individual-query native subset | 48 cases, included in the 118 |
| Native collection/API/health regression subset | 70 cases, included in the 118 |
| Pip check | No broken requirements found |
| Tracked/untracked whitespace and scope checks | Passed |

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_record_queries.py backend/tests/test_service_link_fixture_safety.py backend/tests/test_service_queries.py backend/tests/test_service_fixture_safety.py backend/tests/test_vehicle_fixture_safety.py backend/tests/test_session_fixture_safety.py -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-5-step-4/backend.xml
backend/.venv/Scripts/python.exe -m pip check
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_record_queries_integration.py::test_removal_returns_only_after_preparation_commit_and_close -p no:cacheprovider -x -o junit_logging=all --junitxml=blueprint/.state/staging/feature-5-step-4/native-closure-recheck.xml
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_record_queries_integration.py backend/tests/test_service_queries_integration.py backend/tests/test_service_api_integration.py backend/tests/test_health.py -m integration -p no:cacheprovider -x -o junit_logging=all --junitxml=blueprint/.state/staging/feature-5-step-4/native.xml
git diff --check
```

The first native attempt stopped after 26 passes and one failed assertion in
the new removal response/closure test. Its observer counted the intentional
read-only verification connection along with the writable removal connection,
then expected only one. The prepared response, commit, and exact cleanup checks
passed. The observer was restricted to writable connections; its isolated
recheck passed and the targeted suite and final database-free suite passed.
Application behavior was not changed to make the assertion pass. The failed
native-initial-closure-observer-failure.xml is preserved separately, not erased
or counted as a passing run. No database guard or cleanup failure occurred.

The final native run recorded 117 exact-cleanup receipts: 234 users, 234 sessions,
132 vehicles, 83 services, 10 part snapshots, 12 maintenance completions, and 13
schedules verified absent. These are tracked identities verified absent across
fixtures, not DELETE affected-row totals. The remaining native case,
tests.test_health::test_real_database_health, was read-only with no synthetic
fixtures. cleanup.json retains per-test receipts and aggregation. Initial and
isolated-recheck cleanup evidence is separate from these final-run totals.

### Step 4 concurrency and transaction evidence

Tests coordinated two guarded connections with Events and observed the exact
blocker using pg_blocking_pids. They did not infer ordering from sleep timing:

- For both link types, an uncommitted child insert held the foreign-key key-share
  lock while a service mutation waited for FOR UPDATE. After the child committed,
  removal was blocked; completion-linked edits were also blocked, while a
  part-only edit remained allowed.
- For both link types, removal held the service lock through its preparation
  callback while a child INSERT waited. Removal then committed, and PostgreSQL
  rejected the child with ForeignKeyViolation. No committed child was cascaded away.
- Waiting updates merged newly committed omitted values from the locked row;
  overlapping supplied fields used the approved last-committed-value behavior.
- Deliberately held locks plus a test-local lock_timeout produced actual
  PostgreSQL lock timeouts. Connections closed, safe availability errors were
  returned, no mutation occurred, and no retry was attempted.

Snapshot comparisons verified blocked edits/removals preserved the complete
service, part snapshots, completion rows, schedules/baselines, and current vehicle
readings/timestamps. No-op saves remained unchanged with either/both link types.
Other tests covered optional clears, confirmed zero, legacy dates, raw omitted
text, immutable fields, expense-view effects, preparation before commit, and
successful removal only after closure. Injected preparation/pre-commit/lost-ack
faults exercised real transactions but are simulations, not actual outages.

Each pytest invocation emitted the existing Starlette/AnyIO deprecation. Git
emitted its ordinary EOL notice. The 118-case native run was targeted; the full
353-case native suite was not rerun. Earlier evidence remains separately dated
and is not relabeled fresh. No browser, frontend, schema, dependency, individual
route, staging, commit, or independent-audit work occurred in Step 4.

## Step 5 verification: individual GET/PATCH/DELETE APIs

Added GET, PATCH, and DELETE at
/api/vehicles/{vehicle_id}/services/{service_id}, using the unchanged approved
query functions. Both decoded path IDs use canonical ASCII validation. Identity
comes only from require_authenticated_session; browser ownership fields remain
forbidden. Missing, foreign-owned, and wrong-parent records return exactly
404 {"detail":"Service record not found."}.

PATCH and DELETE enforce the existing trusted-Origin/JSON/CSRF policy before
FastAPI reads the body or runs authentication/business dependencies. DELETE
accepts only {"confirm_removal":true}; missing, false, null, coerced boolean
values, extra fields, and malformed/nonobject bodies receive sanitized 422.
PATCH preserves omission/null rules, fixed empty-body/required-field errors,
and ordinary no-op success. Part-only links permit edits; actual completion-linked
edits and either linked removal return only their approved fixed 409 detail.
No child IDs, names, counts, or other linked data appear in conflicts.

GET/PATCH return exactly one public ServiceRecord; successful DELETE returns
exactly id, vehicle_id, and deleted=true with HTTP 200. The query preparation
callback constructs the response inside the transaction; success is returned
only after commit and closure. Repeated removal returns the same fixed 404.
Cache-Control: no-store applies to successes, errors, and routing responses.
Only successful 200/201 responses carry the exact committed actor deadline;
no new session query or deadline calculation is added. A 401 deletes the unusable
cookie, while authentication/service availability errors preserve it.

### Step 5 commands and results

| Check | Actual result |
| --- | --- |
| Focused individual/collection API and individual-query tests | 398 passed in 6.19s |
| Complete database-free backend suite | 2054 passed, 441 integration cases deselected, in 20.79s |
| New Step 5 database-free subset | 188 cases, included in the complete suite |
| Targeted guarded native suite | 141 passed, 6 database-free health cases deselected, in 206.93s |
| New individual API native subset | 88 cases, included in the 141 |
| Existing collection API and health regressions | 53 cases, included in the 141 |
| Pip check | No broken requirements found |
| Tracked/untracked whitespace and final scope checks | Passed |

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_record_api.py backend/tests/test_service_api.py backend/tests/test_service_record_queries.py -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-5-step-5/backend.xml
backend/.venv/Scripts/python.exe -m pip check
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_record_api_integration.py backend/tests/test_service_api_integration.py backend/tests/test_health.py -m integration -p no:cacheprovider -x -o junit_logging=all --junitxml=blueprint/.state/staging/feature-5-step-5/native.xml
git diff --check
```

No Step 5 test failed. Each pytest invocation emitted one existing Starlette/AnyIO
deprecation warning; Git emitted its ordinary EOL notice. Source hashes confirm
the approved query, schema, linked-fixture, authentication, and prior test code
were preserved, except the old collection-only routing expectations necessarily
updated for the new methods. No application transaction algorithm changed.

### Step 5 native cleanup and behavioral evidence

All native connections remained under the existing test-settings and
first-statement current_database() guards, using only garageguide_app_test.
The final native.xml contains 140 exact-cleanup receipts verifying 280 users,
280 sessions, 149 vehicles, 106 services, 8 part snapshots, 7 maintenance
completions, and 7 schedules absent through separate guarded connections.
Counts refer to tracked identities verified absent across fixtures, including
records deliberately removed during a test, not SQL DELETE affected-row totals.
The remaining case, tests.test_health::test_real_database_health, was read-only
and reserved no synthetic records. cleanup.json retains per-test receipts and
their aggregation. No guard or cleanup failed.

Real native API tests proved the full GET/PATCH/confirmed-DELETE/repeated-404
flow, all null/zero combinations, identical missing/foreign/wrong-parent 404s,
canonical ID errors, no-op success with either/both link types, part-only edits,
atomic completion-linked rejection, and linked-removal rejection without changing
service/child/schedule/vehicle snapshots. Both mutations' policy tests verified
no body parsing, session extension, or business writes on rejection. Success
deadline headers matched the actual committed session row.

Preparation callbacks ran while their business connection was open and before
another guarded connection could observe the mutation. Successful responses
followed commit and closure. Injected preparation and pre-commit failures left
stored data unchanged and produced safe errors without deadlines. Injected
lost-acknowledgment failures after real commits returned safe 503, preserved the
cookie, and left the known committed edit/removal outcome for deliberate
inspection. No mutation was retried. These injections are simulations, not
evidence of a real outage. A later removal/read 404 established only current
absence, not which request removed the record.

The native run was targeted; it did not rerun the complete 441-case native suite
or Step 4's unchanged query-concurrency cases. Those remain separately recorded
earlier evidence. No browser verification, frontend changes, schema/dependency
changes, staging, commit, audit, or later-step work occurred in Step 5.

## Step 6 frontend logic and database-free regressions

Fresh verification on November 18, 2026:

| Check | Result |
| --- | --- |
| Focused service request/state/session tests | 219 passed, zero failures/skips; 357.00ms |
| Complete Node suite, all eleven test files | 747 passed, zero failures/skips; 909.50ms |
| Complete database-free backend suite | 2054 passed, 441 integration tests deselected; 20.77s |
| Backend pip check | No broken requirements found |
| Frontend lint | Passed, no lint warnings/errors |
| Frontend production build | Passed; 60 modules; 1.34s |
| Tracked and untracked-file whitespace | Passed |

Commands (using the existing fnm-managed Node v22.23.4 on PATH):

```powershell
node --test frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-5-step-6/backend.xml
backend/.venv/Scripts/python.exe -m pip check
npm --prefix frontend run lint
npm --prefix frontend run build
git diff --check
```

An additional read-only script checked trailing whitespace and final newlines
on every untracked candidate and compared backend raw hashes to Step 5's saved
results. All matched. Its first invocation had a PowerShell quoting error;
the corrected stdin-based script passed. This was not an application/test
failure. No test failure or guard was waived.

Step 6 changes only:

- frontend/src/api.js: five bounded, same-origin request helpers; separate
  collection/create/detail/update/removal contracts; fixed safe errors and
  uncertainty after possibly dispatched mutations. No automatic retry.
- frontend/src/serviceValidation.js: canonical IDs, exact public records,
  calendar dates, Unicode-safe fields, exact reading/USD strings, changed-only
  PATCH preparation, sanitized-error allowlists. The server decides today;
  browser dates do not reject a server-valid date at a time-zone boundary.
- frontend/src/serviceState.js: separate history/record stores sharing their
  private-request lifecycle, draft/saved separation, explicit removal and reload,
  uncertainty gates, request/authentication/navigation generations, and current
  success-only deadline handling. No pages or route changes.
- frontend/tests/serviceApi.test.js: endpoint shapes, IDs, exact decimals,
  date rules, safe errors, timeout/cancellation, and no automatic replay.
- frontend/tests/serviceState.test.js: drafts, no-ops, creation/reload outcomes,
  linked conflicts, removal confirmation, uncertainty and duplicate prevention.
- frontend/tests/serviceSession.test.js: stale successes/errors across route,
  logout/login, same-account relogin, identity, visibility, expiry, disposal,
  deadline freshness, and local expiration without network renewal.
- frontend/tests/serviceFixtures.js: synthetic in-memory session/API fixtures;
  no database or browser access.
- This record and current-feature.md: Step 6 progress and actual evidence.

An uncertain create retains its draft but blocks another POST until a deliberate
history reload and explicit duplicate-risk acknowledgment. An absent entry does
not prove that creation failed or that the original request cannot still finish.
An uncertain edit requires explained reload/discard and inspection before another
save. An uncertain removal requires reload; a later 404 establishes only current
absence. Confirmed creation followed by a failed history GET still reports
creation success and prevents accidental reposting. Navigation during that GET
cannot return stale current success; a dedicated regression covers this.

Private results are checked against route IDs and the current authenticated
generation before they can reach the shared deadline mechanism. Older, equal,
absent, malformed, or expired deadlines do not replace a newer local deadline.
Authentication rejection/unavailability gates private state; navigation, logout,
account changes, same-account relogin, hiding, departure, disposal, and expiry
cancel/ignore late results. No periodic or expiry-triggered request was added.
Errors never extend the deadline. Tests use controlled promises, fake clocks,
mock fetch, and synthetic in-memory data; none is browser/native evidence.

Warnings: Node reports the experimental MockTimers API in fake-clock tests;
pytest reports the existing Starlette/AnyIO BlockingPortal deprecation; Git
reports Windows LF-to-CRLF notices. The production build used the approved
scoped elevation needed by the installed esbuild process. Build output remains
ignored. No dependency, lockfile, schema, session algorithm, backend source,
private environment, or existing page/route was changed in Step 6.

No PostgreSQL connection, native rerun, cleanup SQL, browser execution, staging,
commit, or audit occurred in Step 6. Previous native results and cleanup receipts
remain earlier evidence, not rerun claims. Browser integration and route matching
for the new pages remain Step 7 work. Local logs, backend JUnit, final file hashes,
and results are under ignored blueprint/.state/staging/feature-5-step-6/.

## Step 7 automated evidence and browser preparation

Fresh checks on November 18, 2026:

| Check | Result |
| --- | --- |
| Focused service frontend suites | 245 passed, zero failures/skips; 341.26ms |
| Complete eleven-file Node suite | 773 passed, zero failures/skips; final run 800.79ms |
| Focused manual launcher and service-fixture database-free tests | 57 passed; 1.05s |
| Complete database-free backend | 2076 passed, 441 integration tests deselected; 21.60s |
| Pip check | No broken requirements found |
| Frontend lint | Passed, no lint warnings/errors |
| Final production build | Passed; 65 modules; 1.25s |
| Tracked/untracked whitespace | Passed |
| Agent-run browser, real manual setup, native tests, cleanup SQL | Not run by the agent in Step 7; user observations recorded below |

Exact commands (existing fnm-managed Node v22.23.4 on PATH):

```powershell
node --test frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_manual_registration_server.py backend/tests/test_service_fixture_safety.py -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-5-step-7/backend.xml
backend/.venv/Scripts/python.exe -m pip check
npm --prefix frontend run lint
npm --prefix frontend run build
git diff --check
```

An additional read-only script checked all untracked candidate final newlines/
trailing whitespace and prior-step hashes outside the approved Step 7 surface.
All passed. Full Node/lint/build were repeated after a final success-announcement
change; earlier passes are not additional unique tests. No test failed or was
waived. Warnings remain for Node's experimental MockTimers API, the existing
Starlette/AnyIO deprecation, and Git LF/CRLF notices. Build used scoped elevation
required by installed esbuild; no packages/runtimes were installed.

Changed Step 7 files and purposes:

- ServiceHistoryPage.jsx: history/create states, saved-record links, safe
  feedback, reload/inspection, and explicit uncertain-create duplicate warning.
- ServiceRecordPage.jsx: view/edit/save/cancel, permanent-removal confirmation,
  linked conflicts, explained reload/discard, and return/reload after removal.
- ServiceFields.jsx and ServiceValues.jsx: shared labeled controls, four service
  types, associated errors/hints, multiline text, and distinct Not recorded,
  0.0, and USD 0.00. Keyboard/focus/live-status behavior is wired but not yet
  observed in a browser.
- App.jsx, vehicleRoutes.js, and VehicleDetailPage.jsx: shared rendered/protected
  route definitions, profile link, private remounts, and static-route precedence.
- styles.css: select/textarea styling, wrapping, and service spacing.
- serviceState.js: explicit successful-parent loaded state and history focus
  updates; existing uncertainty/cancellation/session rules retained. Only a fixed
  serviceRemoved boolean crosses router navigation; no private draft/value does.
- serviceSession.test.js and serviceState.test.js: encoded/case/slash matching,
  invalid decoded IDs, unrelated paths, static precedence, session revalidation,
  and loaded-versus-empty history coverage.
- backend/tests/manual_registration_server.py: guarded wrappers for all five
  operations, reservation before create, immutable record guards, callback
  forwarding, exact cleanup, and opt-in third-account linked-fixture setup.
- backend/tests/database_support.py: tracked-parent presence and exact service
  identity checks, with missing/foreign/wrong-parent cases retaining safe 404s.
- backend/tests/test_manual_registration_server.py and test_service_fixture_safety.py:
  database-free guard, ordering, lost-ack cleanup, exact SQL parameters, callback,
  first-statement verification, opt-in setup, and cleanup-on-failure regressions.
- BROWSER_CHECKS.md, current-feature.md, and this record: manual procedure,
  actual automated evidence, and pending acceptance.

Each page owns/disposes its Step 6 store and uses RequireSession remounts for
navigation/authentication generations. Cancel discards the edit draft without
writing. Removal requires explicit confirmation and returns to fresh history
after success. Linked conflicts preserve saved data/drafts. Uncertain mutations
are never replayed: reload/inspection is deliberate, reload/discard is explained,
and an absent entry never proves create failure. No polling or deadline-only
authentication request was added. PostgreSQL remains authoritative for sessions.

The manual launcher still requires RUN_DB_TESTS=1, only .env.test, exactly
garageguide_app_test, and first-statement current_database() verification on
every physical connection. --service-links seeds part/completion-linked records
only for the third reserved account's new vehicles; A/B can test empty histories
and isolation. Exact child reservations precede writes; service tracking uses
immutable owner/vehicle/service IDs. Existing cleanup recovers exact reservations,
removes children before services/vehicles/users, and verifies absence separately.
These passed database-free mocks during implementation; actual setup/cleanup
had not run at that handoff. The subsequent user report is recorded below.

Expected cleanup output at implementation handoff (subsequently reported by the user):

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.
```

No browser tool is available. The complete Feature 5 section of BROWSER_CHECKS.md
covers development and production preview, real flows/linked restrictions,
two-account checks, uncertain-write and failure simulations, real visible idle
expiry, keyboard/focus, viewports/zoom, and exact cleanup. The subsequent user
observations below satisfy Step 7. Earlier native/browser results remain separate;
simulations do not prove a real PostgreSQL outage or server revocation.
No agent-run server, PostgreSQL connection, native rerun, browser, production backend change,
schema/dependency/lockfile/private environment change, staging, commit, or audit
occurred. Ignored Step 7 logs/JUnit/hashes are verification artifacts, not a
frozen checkpoint proposal. Step 8 remains unstarted and unauthorized.

## Step 8 final verification and checkpoint proposal

Fresh builder verification on November 18, 2026, after approval of Step 7:

| Check | Actual result |
| --- | --- |
| Complete database-free backend | 2076 passed, 441 native cases deselected; 40.63s |
| Complete frontend Node suite, all eleven files | 773 passed, zero failures/skips; 1846.22ms |
| Complete guarded native PostgreSQL suite | 441 passed, 2076 database-free cases deselected; 1043.15s |
| Pip check | No broken requirements found |
| Frontend lint | Passed, no lint errors/warnings |
| Frontend production build | Passed; 65 modules; 2.35s |
| Tracked/untracked candidate whitespace | Passed |
| Builder diff/scope review | 38 files; no confirmed blocking defect or unrelated change |
| Browser | November 18 user evidence retained; not rerun |
| Independent audit | Required; not run; pending approved immutable checkpoint |

Exact commands from repository-root PowerShell, using the existing Python
environment and fnm Node v22.23.4 on PATH:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-5-step-8/backend.xml
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js
backend/.venv/Scripts/python.exe -m pip check
npm --prefix frontend run lint
npm --prefix frontend run build
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -x -p no:cacheprovider -o junit_logging=all --junitxml=blueprint/.state/staging/feature-5-step-8/native.xml
git diff --check
```

Before native pytest, a settings-only preflight asserted RUN_DB_TESTS=1 and
load_settings(testing=True).database == garageguide_app_test without connecting
or printing credentials. That loader selects only backend/.env.test. Every
physical native connection then independently verified SELECT current_database()
as its first SQL through the existing fixture guard before exposure. The native
command's -x would stop on a first failure; all 441 selected cases ran and passed.
No guard or cleanup failed, no failure was waived, and no schema was initialized
or changed. All application/test inputs remained byte-for-byte unchanged during
the checks; only the three progress/evidence documents changed afterward.

The fresh native run includes all 205 Feature 5 service cases (52 collection API,
17 collection query, 88 individual API, 48 individual query) and all 236 existing
native regressions. It proves real two-account and wrong-parent isolation, exact
Decimal/null/zero values, sorting, unchanged vehicle readings/timestamps, locked
latest-row merging, linked/no-op restrictions, both foreign-key insertion/removal
orderings, lock timeouts, safe API contracts, and transaction ordering. Fault
injections before/after commit remain simulations, not evidence of an actual
PostgreSQL outage. Confirmed native lost-ack outcomes were inspected without
automatically replaying a mutation.

### Fresh native cleanup evidence

native.xml retains passing-test stdout. cleanup.json contains 439 per-test
cleanup receipts and their aggregation:

| Fixture identities verified absent | Aggregate across receipts |
| --- | ---: |
| Users | 786 |
| Sessions | 752 |
| Vehicles | 346 |
| Service records | 174 |
| Part snapshots | 18 |
| Maintenance completions | 19 |
| Schedules | 20 |

These are tracked fixture identities verified absent, not DELETE affected-row
counts, global table counts, or a reset. Each fixture registered cleanup before
writes, reserved exact synthetic data, tracked immutable parent/owner/record IDs,
recovered uncertain creations, removed exact linked children before services
and parents, and verified absence through separate guarded connections. No
truncation, broad/prefix deletion, cascade bypass, sequence reset, or write to
garageguide_app/postgres/another database occurred. The only two cases without
a synthetic-cleanup receipt were the read-only database health tests. Their
passing results do not claim synthetic writes or additional cleanup.

### Review, evidence boundaries, and remaining gates

Reviewed all 38 candidates, the complete tracked/untracked diff, production
paths and test/fixture coverage: owner-scoped SQL, transaction/lock ordering,
linked-data atomicity, omission/null/zero validation, safe errors/logs, mutation
policy, no-store/deadlines, shared protected routes, stale generations, drafts,
confirmation, uncertain writes, and exact cleanup. No application behavior was
changed during Step 8, so the preserved browser observations are applicable.
This is builder review, not an independent audit or finding closure.

The user's November 18 browser version 157.0.8103.79 report for BOTH development
and preview remains user-performed evidence below. No agent/reviewer browser
run or numeric idle duration is inferred. Native tests, automated mocks/fake
clocks, user browser observations, and browser failure simulations remain
separate categories. The user's exact cleanup message is preserved unchanged;
it is not substituted for the fresh native receipts above.

Warnings: one existing Starlette/AnyIO BlockingPortal deprecation per pytest
run, Node MockTimers experimental notices, and Git LF/CRLF notices. Production
build required the existing scoped esbuild elevation. No runtime/dependency was
installed, no lockfile changed, and generated build output stays ignored.

Approved limitations remain: historical snapshots do not update current vehicle
readings; only USD cost is supported; there is no pagination, version column,
server idempotency, or automatic mutation retry. Supplied overlapping edits use
last-committed-value behavior. Uncertain outcomes require deliberate inspection;
an absent entry after reload does not prove create failure or make resubmission
safe from duplication. A later removal 404 proves only current absence.

The exact frozen 38-path proposal, every purpose/raw SHA-256, full builder diff,
commands/results, exclusions, and Git state are in ignored local staging:
feature-5-checkpoint-proposal.json, feature-5-review-packet.md, feature-5-review.diff,
and feature-5-step-8/. Proposed message: feat: record and review service history.
Branch: feature/record-and-review-service-history. Parent HEAD remains
4bffbb63d278bbe9b62e377d251c501622910e4b. Index is empty; the working tree contains
only these 38 reviewed Feature 5 candidates. Schema/dependencies/lockfile,
private environments, generated/recovery files, backend/prepapp.txt, build plan,
workflow settings, overview, and prior archives are excluded. Features 1-4
remain checked; Feature 5 and later features remain unchecked. No stage, commit,
audit, completion, merge, push, or later feature was performed. Independent review
and $complete remain blocked on their separately approved workflow gates.

The existing manual guide remains available for optional demonstration; it is
not a new verification run or request to repeat the user's completed checklist.

## Browser and independent-review evidence

### User-performed Feature 5 observations — November 18, 2026

The user reported manually running the Feature 5 browser checklist with all
checks run passing. Reported browser version: 157.0.8103.79. Because the original
environment field contained a placeholder, the agent requested clarification;
the user explicitly confirmed completing the entire checklist in BOTH Vite
development and production preview.

This is the user's general checklist pass report, not agent/reviewer browser
execution or newly run automated/native tests. Real service flows remain
distinct from simulated failure cases. Simulations do not prove real PostgreSQL
outages or server revocation. No additional per-case result or numeric idle
duration is inferred. Earlier automated/native counts and evidence are preserved.

The user reported the exact guarded-backend message:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.
```

Both required modes and exact cleanup are confirmed. Step 7 is marked complete
and was awaiting review before Step 8 at that time. There is no remaining
mode/cleanup evidence blocker from this report. Subsequently approved Step 8
results are recorded above; no independent audit has run.
Recording these observations changed documentation only and ran no tests,
database connection, server, or browser. Nothing was staged or committed.

Ignored local JUnit artifacts are verification evidence only; they are not staged
or committed. The index remains empty. No dependency, schema, build-plan, workflow
configuration, or private environment changes are included. Frontend request and
state logic is included through Step 6; Step 7 pages have passing automated
checks and user-performed development/preview browser acceptance.

### User-performed F-01 and F-02 repair checks

In response to the focused browser checklist for Vite development and production
preview, the user reported "everything passed." This was a checklist-level pass
report for the repairs to the second-entry validation and history-refresh flows
(F-01) and the mixed Unicode service history flow (F-02). The failed-refresh
case in the checklist uses a simulated GET failure. The user supplied this
exact guarded backend cleanup message:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.
```

This report applies to the repairs based on checkpoint
`6779cdefa13de9d45f3b0cc968089900037334c6`. It is separate from the original
November 18, 2026 browser report and the recorded 441 native PostgreSQL passes.
No browser version, test date, or additional case-by-case observations were
supplied for this focused run. The agent did not rerun browser checks or connect
to PostgreSQL to record this report. Both findings remain open pending a fresh
independent review of the approved repair checkpoint.

### User-performed F-03 focused Unicode repair recheck

After the inward-scanning trim repair based on
`113b36db8be3a2bcc05a432559d383af069df0af`, the user confirmed all four focused
browser steps in BOTH Vite development and production preview. The report
confirmed that long interior whitespace and U+FEFF remained preserved, the
affected record and an ordinary record appeared and opened correctly, and a
cost-only edit sent only the changed cost in PATCH, omitting description and
notes. The fourth step, exact guarded cleanup, was also confirmed:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.
```

These are user-performed focused observations, separate from the earlier full
November 18 checklist, automated regressions, native PostgreSQL evidence, and
simulated failure cases. No new browser version or test date was supplied.
The agent did not rerun browser checks, tests, or PostgreSQL connections to
record this report. No full checklist or failure simulation rerun is claimed.

Focused browser acceptance for the F-03 repair is confirmed. F-01 remains closed;
F-02 and F-03 remain pending fresh independent verification of an approved repair
checkpoint. The prior audit receipt and findings are preserved unchanged; this
browser report does not close either finding or satisfy the independent gate.


## Original implementation checkpoint proposal

{
  "schemaVersion": 1,
  "feature": 5,
  "title": "Record and review service history",
  "date": "2026-11-18",
  "branch": "feature/record-and-review-service-history",
  "parent_head": "4bffbb63d278bbe9b62e377d251c501622910e4b",
  "commit_message": "feat: record and review service history",
  "expected_staged_file_count": 38,
  "index_initially_empty": true,
  "specification": {
    "path": "blueprint/context/current-feature.md",
    "sha256": "1610df4efb3140b9f0457ecbe6e0e4d1919688a6544dcf7a24a4075e7dc15086"
  },
  "files": [
    {
      "path": "backend/app/main.py",
      "status": "modified",
      "purpose": "Register the service-history router; preserve existing routes and middleware.",
      "bytes": 1555,
      "sha256": "46703d737bb736a2d1f07e6ddb4fe1fdf3bbafc195bb9cf2d6109f4a85d7bed7"
    },
    {
      "path": "backend/app/routes/services.py",
      "status": "untracked",
      "purpose": "Owner-authenticated collection and individual APIs, pre-body mutation policy, safe responses and headers.",
      "bytes": 10429,
      "sha256": "9d10323b6d3343077cd65421eb78a304d371c097b100a917e5926316cc17a864"
    },
    {
      "path": "backend/app/service_queries.py",
      "status": "untracked",
      "purpose": "Parameterized owner/parent-scoped service CRUD, locked link protection and explicit transaction boundaries.",
      "bytes": 10593,
      "sha256": "41f7fdd8b0f7de08165bcfe2bc5d06778b746c7c5a7004bf588709592c05180e"
    },
    {
      "path": "backend/app/service_schemas.py",
      "status": "untracked",
      "purpose": "Strict create/PATCH/removal/public models, injectable service date and exact Decimal/null serialization.",
      "bytes": 6365,
      "sha256": "598c806b6a3f084cb03871dd13fd67d2b86f2a9138e31da232d0dfcdd057b8f2"
    },
    {
      "path": "backend/tests/conftest.py",
      "status": "modified",
      "purpose": "Reuse guarded native fixture setup and report exact service/linked cleanup receipts.",
      "bytes": 2936,
      "sha256": "e824d8da1abe893ec4dc27fdf08958e12acb327199844142db835eb84872df1c"
    },
    {
      "path": "backend/tests/database_support.py",
      "status": "modified",
      "purpose": "Reserve/track immutable synthetic identities, guard each physical connection and clean exact child/service/parent fixtures.",
      "bytes": 30234,
      "sha256": "12a6dcf935ece1011e5afc4d790e9d06d48c7386c4ab7feef60cb98b0c667147"
    },
    {
      "path": "backend/tests/manual_registration_server.py",
      "status": "modified",
      "purpose": "Guarded synthetic browser backend, service wrappers and optional third-account linked fixtures.",
      "bytes": 13188,
      "sha256": "987daa9863548a48933449220f4654352cb28378516ec251f53c8927a93b91a3"
    },
    {
      "path": "backend/tests/test_manual_registration_server.py",
      "status": "modified",
      "purpose": "Database-free manual-server safety, callback, reservation, failure-finalizer and linked-setup tests.",
      "bytes": 20601,
      "sha256": "6e116f8d6794742cbdb594da86e81e693b5ac2fec492f58a0cd258b456b60ef4"
    },
    {
      "path": "backend/tests/test_service_api.py",
      "status": "untracked",
      "purpose": "Database-free list/create API contract, ownership, mutation policy, validation, error/header and transaction callback tests.",
      "bytes": 15695,
      "sha256": "15dac5874ff891f203e06e9402057b40259f28dadf4e615a232d8cc15b4ac11f"
    },
    {
      "path": "backend/tests/test_service_api_integration.py",
      "status": "untracked",
      "purpose": "Real guarded list/create API behavior, isolation, headers and simulated transaction fault regressions.",
      "bytes": 15607,
      "sha256": "584b8891b7bf416a29f8514eaa12a57d5a8c7428e1590323ab9e85cf3de22bcd"
    },
    {
      "path": "backend/tests/test_service_fixture_safety.py",
      "status": "untracked",
      "purpose": "Database-free exact service reservations, immutable tracking, physical guards and lost-ack cleanup safety.",
      "bytes": 8668,
      "sha256": "cef10297c14d7a8e67c982316f4c145b76be4e483b78f54f2fc65aff2dc321d5"
    },
    {
      "path": "backend/tests/test_service_link_fixture_safety.py",
      "status": "untracked",
      "purpose": "Database-free exact linked fixture reservations, safe cleanup ordering, collision and cascade refusal.",
      "bytes": 8486,
      "sha256": "d5421d31890c0ad9dea8d2e06ea34d491834ad231e0770f7375296d323009c5d"
    },
    {
      "path": "backend/tests/test_service_patch_schemas.py",
      "status": "untracked",
      "purpose": "Strict partial updates, omitted/null semantics, no-op fields and explicit removal-confirmation validation.",
      "bytes": 9275,
      "sha256": "a6a20a27c79d2ee0296c58bd3ba0b5894d0d7b36f58c5e31864da73757ea6a1e"
    },
    {
      "path": "backend/tests/test_service_queries.py",
      "status": "untracked",
      "purpose": "Database-free owner-scoped list/create SQL, parameters, exact values and commit/rollback/close behavior.",
      "bytes": 11103,
      "sha256": "50a17cf93200528e79deae02c9ac2f78048464b8b6efd24d20c8994cb342b0c8"
    },
    {
      "path": "backend/tests/test_service_queries_integration.py",
      "status": "untracked",
      "purpose": "Real guarded service list/create, ordering, Decimal/null values, unchanged vehicles and uncertain-insert recovery.",
      "bytes": 13742,
      "sha256": "fadf8557a3190ea4329c19042eebfd9125d278f2c1054ae95fff77d2d660b067"
    },
    {
      "path": "backend/tests/test_service_record_api.py",
      "status": "untracked",
      "purpose": "Database-free individual GET/PATCH/DELETE, safe 404/409/422, policy, headers, failures and redaction.",
      "bytes": 14755,
      "sha256": "dc0466c1a523ff7ed635bb53cd8a0d43f590166b7e0c50a026a9d704db905cef"
    },
    {
      "path": "backend/tests/test_service_record_api_integration.py",
      "status": "untracked",
      "purpose": "Real guarded individual API flow, nested isolation, linked conflicts, no-ops, removal and transaction faults.",
      "bytes": 18322,
      "sha256": "609429bd506a26286609685751ce9d2c0aab04e9140770f678fa1ee2b9a53fcf"
    },
    {
      "path": "backend/tests/test_service_record_queries.py",
      "status": "untracked",
      "purpose": "Database-free nested detail/update/removal SQL, row-lock/link ordering, merges and transaction faults.",
      "bytes": 10746,
      "sha256": "13ac21591c50144e5974756276a086b0dc7e4a806d19e249b9d1cdea7f067839"
    },
    {
      "path": "backend/tests/test_service_record_queries_integration.py",
      "status": "untracked",
      "purpose": "Real linked restrictions, two-connection locks, child-insert/removal orderings, no-op/legacy edits and expense-view effects.",
      "bytes": 24209,
      "sha256": "5fea3c86f8081c63715721c0f2fa4beae227e20a74d49c554e31d5fe119c8829"
    },
    {
      "path": "backend/tests/test_service_schemas.py",
      "status": "untracked",
      "purpose": "Create/public schema boundaries, dates, fixed types, Unicode, precise decimals and unknown/zero values.",
      "bytes": 15374,
      "sha256": "8080ac5e86d47a95b91e501d88f739ee297cc228fd1e6caaa8a22ace4c03a097"
    },
    {
      "path": "blueprint/context/current-feature.md",
      "status": "modified",
      "purpose": "Approved Feature 5 specification, step progress, verified builder results and user-attributed browser evidence.",
      "bytes": 51735,
      "sha256": "1610df4efb3140b9f0457ecbe6e0e4d1919688a6544dcf7a24a4075e7dc15086"
    },
    {
      "path": "docs/verification/BROWSER_CHECKS.md",
      "status": "modified",
      "purpose": "Repeatable guarded dev/preview checklist and the user's November 18 observations; preserve historical evidence.",
      "bytes": 81639,
      "sha256": "4e89e2efe5bfebe116bc9280e04f14bbf9bb5bdf24992717fb8fb6c21b09a2fa"
    },
    {
      "path": "docs/verification/SERVICE_HISTORY_STATUS.md",
      "status": "untracked",
      "purpose": "Separate automated/native/user-browser/simulated evidence, actual commands, cleanup results and limitations.",
      "bytes": 46917,
      "sha256": "e13ac2171e79c6ab7ca84b5e4ce07d0c515d880109b7e7e4efd6f0eb5b2a6379"
    },
    {
      "path": "frontend/src/App.jsx",
      "status": "modified",
      "purpose": "Render the two service pages behind the existing private session gate.",
      "bytes": 3755,
      "sha256": "1e1da7c86571412baa889a3fcba7aed28e58a696d2abbf8c60ec10a623078d22"
    },
    {
      "path": "frontend/src/ServiceFields.jsx",
      "status": "untracked",
      "purpose": "Shared labeled service controls, hints and associated safe field errors.",
      "bytes": 2447,
      "sha256": "3158a5df4815924cb092f5bd5a1ea03ee14417386b6bc848f1f5b7ea97ab4669"
    },
    {
      "path": "frontend/src/ServiceHistoryPage.jsx",
      "status": "untracked",
      "purpose": "Protected history/create page, links, exact values, deliberate reload and uncertain-create duplicate-risk flow.",
      "bytes": 5999,
      "sha256": "dfdb36d514206817c87b67cd31e5ed0f945be3673193eeeabc31c917b8b7952e"
    },
    {
      "path": "frontend/src/ServiceRecordPage.jsx",
      "status": "untracked",
      "purpose": "Protected detail/edit/remove page, draft cancellation, explicit removal, linked conflicts and uncertainty inspection.",
      "bytes": 6569,
      "sha256": "4268b1eb07dec03408d000fdd39fe54cc9c42f3dc0fa39e51cec4e9de7618aa0"
    },
    {
      "path": "frontend/src/ServiceValues.jsx",
      "status": "untracked",
      "purpose": "Render saved values with distinct unknown readings/cost and confirmed zero.",
      "bytes": 570,
      "sha256": "2fe1cd39873bdc2334464ba6d4460014682e2e50071c75e299de1cb087cbb7df"
    },
    {
      "path": "frontend/src/VehicleDetailPage.jsx",
      "status": "modified",
      "purpose": "Link the owned vehicle profile to service history.",
      "bytes": 9015,
      "sha256": "7d6033784a2e4eb43cec78ca51a2df204483956c8410a7d545be3d39f26f5a68"
    },
    {
      "path": "frontend/src/api.js",
      "status": "modified",
      "purpose": "Five bounded same-origin service request helpers, canonical IDs, strict responses and safe uncertainty handling.",
      "bytes": 26250,
      "sha256": "d966d4781400aad756e4c1f3c4edb87a47b03d05a6a3071fbddf708bd78d7c80"
    },
    {
      "path": "frontend/src/serviceState.js",
      "status": "untracked",
      "purpose": "Separate saved records/drafts, synchronous write guards, confirmation, lifecycle freshness and session deadlines.",
      "bytes": 13945,
      "sha256": "d30231d916b111a29292dfce8248f50311bdeb0213072aafeb3237a8e6afc7fb"
    },
    {
      "path": "frontend/src/serviceValidation.js",
      "status": "untracked",
      "purpose": "Canonical IDs/dates, exact public shapes, string decimal normalization, changed-only PATCH and fixed error parsing.",
      "bytes": 6725,
      "sha256": "72306fe47cf4840e363fba88f173d559c8d3eaf6539c93a72645c5208ceb0872"
    },
    {
      "path": "frontend/src/styles.css",
      "status": "modified",
      "purpose": "Extend native select/textarea and service layouts using existing responsive plain CSS.",
      "bytes": 4180,
      "sha256": "ba8b27daf258e136266bca05518f08d36acc847779590419cd411d910303acfb"
    },
    {
      "path": "frontend/src/vehicleRoutes.js",
      "status": "modified",
      "purpose": "Share actual service route descriptors with rendering/session matching; preserve static-route precedence.",
      "bytes": 638,
      "sha256": "1bf97cb10c078c13595b5f633e3d256ba855caff5e45d0429ca5478ebb8924f7"
    },
    {
      "path": "frontend/tests/serviceApi.test.js",
      "status": "untracked",
      "purpose": "Request/body/response contracts, strict IDs/decimals, timeout/cancellation, fixed errors and no write replay.",
      "bytes": 9841,
      "sha256": "d496aa85e0cddc8cbac0cda9da9c1f93dd28774354a6157953902bcb1c8b0e25"
    },
    {
      "path": "frontend/tests/serviceFixtures.js",
      "status": "untracked",
      "purpose": "Synthetic in-memory API/session fixtures for Node tests; no database or browser access.",
      "bytes": 2828,
      "sha256": "1e33675a2914e2a5d70dd6014cd6583db509d87eb60bfd994f0a6f1becb51530"
    },
    {
      "path": "frontend/tests/serviceSession.test.js",
      "status": "untracked",
      "purpose": "Shared decoded route matching, session/auth/navigation generations, deadline freshness and stale-result rejection.",
      "bytes": 7653,
      "sha256": "233f01ebd942229062d4c1b22d1c33a84fc2c2e4f29fb9bb848ca9bcb76cf74a"
    },
    {
      "path": "frontend/tests/serviceState.test.js",
      "status": "untracked",
      "purpose": "Draft/saved separation, confirmation/cancel, uncertainty/reload, duplicate guards and post-create GET behavior.",
      "bytes": 10677,
      "sha256": "d1af1e3c6706b85351d60dfea9da7ed4dbe2ffe0971599d52f0d0e3c51bb0e18"
    }
  ],
  "full_diff": {
    "path": "blueprint/.state/staging/feature-5-review.diff",
    "sha256": "1ed2f0ac49a31b23e80b79d3e8aaed9ad6f5a5cfac8f7730bc5529ca7481797d"
  },
  "verification_results": {
    "path": "blueprint/.state/staging/feature-5-step-8/results.json",
    "sha256": "5fc7e33e0f3564cfd4c021f3b734e3e12381460bef99592cf09e0dbee2508739"
  },
  "evidence_artifacts": [
    {
      "path": "blueprint/.state/staging/feature-5-step-8/backend.xml",
      "sha256": "3fe1f32e0b10039f8f5e01f180a19b28b919a4fd882ada46d084e4938ee7cda3"
    },
    {
      "path": "blueprint/.state/staging/feature-5-step-8/native.xml",
      "sha256": "9b9cfa058639d33035e5ba66fe8d0744e982e4da42c1540c111f7e831a7aa9f2"
    },
    {
      "path": "blueprint/.state/staging/feature-5-step-8/frontend.log",
      "sha256": "fc37f663b85503ef74b81affee3ad29f3191f76a54a976d6709e83c842a13a94"
    },
    {
      "path": "blueprint/.state/staging/feature-5-step-8/cleanup.json",
      "sha256": "aa067ecf873c24ab2702ccbf7e3c8d4a546cf99eea884832d6e27cd5d8f59914"
    },
    {
      "path": "blueprint/.state/staging/feature-5-step-8/commands.json",
      "sha256": "1abbf655d0f7e33586d92618eff14905e371a72df4589cc6c91543dffb11cdf4"
    },
    {
      "path": "blueprint/.state/staging/feature-5-step-8/builder-review.json",
      "sha256": "93fdcc3efe0b30ba1a25035bcaad4b3337dab2fbd2dde800016414f464180029"
    }
  ],
  "excluded": [
    "private .env/.env.test files and credentials",
    "schema SQL and migrations",
    "dependencies and lockfiles",
    "node_modules, virtual environments, caches and build output",
    "ignored activity/staging/recovery artifacts",
    "backend/prepapp.txt",
    "build plan, workflow settings, overview and prior archives",
    "review/findings canonical stubs"
  ],
  "approval_boundary": "Proposal only. Do not stage or commit until explicit approval; do not run independent audit, completion, merge or push without authorization.",
  "independent_audit": {
    "required": true,
    "status": "not run; pending approved immutable checkpoint"
  },
  "feature_complete": false
}


## F-01 and F-02 repair checkpoint proposal

{
  "schemaVersion": 1,
  "feature": 5,
  "branch": "feature/record-and-review-service-history",
  "parent_head": "6779cdefa13de9d45f3b0cc968089900037334c6",
  "commit_message": "fix: address service history review findings",
  "expected_staged_file_count": 8,
  "index_initially_empty": true,
  "specification": {
    "path": "blueprint/context/current-feature.md",
    "sha256": "1610df4efb3140b9f0457ecbe6e0e4d1919688a6544dcf7a24a4075e7dc15086"
  },
  "diff": {
    "path": "blueprint/.state/staging/feature-5-f01-f02-verified-repair.diff",
    "sha256": "4c23f856e8710082e00015bd2ffd9f95d6d7d31d13200582ba4ffae312cea4bd"
  },
  "browser_report": {
    "feature": 5,
    "findings": [
      "F-01",
      "F-02"
    ],
    "parent_head": "6779cdefa13de9d45f3b0cc968089900037334c6",
    "repair_diff_sha256": "0d4c0b769ce834052333e883afdf668b594a4b02f5500a17aeb3a1eba4555ed3",
    "performer": "user",
    "report_verbatim": "everything passed",
    "context": "Reply to the request for focused repair browser results from Vite development and production preview.",
    "exact_guarded_cleanup_message": "Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.",
    "status": "user reported passing focused browser checks and supplied exact guarded cleanup output",
    "verification_record": "docs/verification/SERVICE_HISTORY_STATUS.md"
  },
  "files": [
    {
      "path": "backend/tests/test_service_schemas.py",
      "sha256": "f853cbf629de37296b1de8ae424c11323f2be664959f448f3ad2c9629ac3a729"
    },
    {
      "path": "docs/verification/SERVICE_HISTORY_STATUS.md",
      "sha256": "c0535017a113952e8456556965fafd3b84dde07fa0d137f5981b6b8ecb5915b7"
    },
    {
      "path": "frontend/src/ServiceHistoryPage.jsx",
      "sha256": "618479ac2e6e48d706f99234541bea6e63e2520bf6fa4b962cb60f969d27d6a2"
    },
    {
      "path": "frontend/src/serviceState.js",
      "sha256": "45d74e2d00a55d6fd11126a316409873ed727cdf0fe3d9a1068684b291ab5b23"
    },
    {
      "path": "frontend/src/serviceValidation.js",
      "sha256": "ebffda033efc5a202ca483bf169d23f170fa73554f08d9c5dbba77cdf11b3307"
    },
    {
      "path": "frontend/tests/fixtures/serviceWhitespace.json",
      "sha256": "a69ff5be404b3bc41e279735cf280f3dfc5f3227ce92b252bec873f166f68474"
    },
    {
      "path": "frontend/tests/serviceApi.test.js",
      "sha256": "92bcbd8c54b0ea94eff1bc1d6e4bca3e91bc163d27e2ceb439e1722d66b18c27"
    },
    {
      "path": "frontend/tests/serviceState.test.js",
      "sha256": "320e00c2d3220c1d5a7054057609ff9e6adbbdccff1bd1cd196791505d3f412b"
    }
  ],
  "excluded_audit_records": [
    "blueprint/context/findings.md",
    "blueprint/context/review.md"
  ]
}


## Final F-03 repair checkpoint proposal

{
  "schemaVersion": 1,
  "feature": 5,
  "repair": "F-03",
  "branch": "feature/record-and-review-service-history",
  "parentHead": "113b36db8be3a2bcc05a432559d383af069df0af",
  "indexEmpty": true,
  "fileCount": 4,
  "commitMessage": "fix: trim service text without repeated whitespace scans",
  "files": [
    {
      "path": "frontend/src/serviceValidation.js",
      "purpose": "Replace repeated suffix scanning with inward edge trimming while preserving Python whitespace, U+FEFF, and interior text.",
      "rawSha256": "cf7efceb94bdc429a22da4bd74337ef148b25dab72abfa1585b54209b582cd22",
      "bytes": 7249
    },
    {
      "path": "frontend/tests/serviceApi.test.js",
      "purpose": "Cover long interior whitespace in mixed history and preserve cost-only PATCH behavior.",
      "rawSha256": "474536af9d050d3fccf1f79a3cf0025ea3ff4db3b9b9e81d05f0214090fc7fc0",
      "bytes": 12021
    },
    {
      "path": "docs/verification/SERVICE_HISTORY_STATUS.md",
      "purpose": "Record user-performed focused Unicode, mixed-history, cost-only PATCH, and cleanup observations in development and production preview.",
      "rawSha256": "80521de335effa4849fe80551d642a585cd6affba8527bc2aa200b2785f22412",
      "bytes": 49484
    },
    {
      "path": "docs/verification/BROWSER_CHECKS.md",
      "purpose": "Record focused user-browser acceptance separately from automated/native evidence and independent finding closure.",
      "rawSha256": "51d38682926f6d19cf784769e1fb1b150654994304aed9ff49d29b8ee873db21",
      "bytes": 82712
    }
  ],
  "diff": {
    "path": "blueprint/.state/staging/feature-5-f03-checkpoint.diff",
    "sha256": "6c53fdf818ef83f247e02927863608adeda52d65da05d2dd3278f4700bf446e1"
  },
  "excludedProtectedFiles": [
    {
      "path": "blueprint/context/current-feature.md",
      "rawSha256": "1610df4efb3140b9f0457ecbe6e0e4d1919688a6544dcf7a24a4075e7dc15086"
    },
    {
      "path": "blueprint/context/review.md",
      "rawSha256": "be93fc57865216ae82f252e5e9ad7c9f5120f40f727fa8d534361a4a813f71a9"
    },
    {
      "path": "blueprint/context/findings.md",
      "rawSha256": "df592d6a2730e692c87a1808ae62b3c5eaacfb445f2ae96a4d0788cd692c5991"
    }
  ],
  "findingState": {
    "F-01": "closed",
    "F-02": "fixed; pending independent closure",
    "F-03": "open; repair and focused browser checks passed; pending independent verification"
  },
  "evidence": {
    "frontendPasses": 777,
    "databaseFreeBackendPasses": 2077,
    "integrationDeselected": 441,
    "focusedFrontendPasses": 5,
    "focusedSharedBackendPasses": 1,
    "pipCheck": "passed",
    "lint": "passed",
    "build": "passed",
    "browser": "User confirmed all four focused steps in Vite development and production preview; no new test date or browser version supplied.",
    "native": "Not rerun for this frontend repair.",
    "checksRerunForProposal": "HEAD, branch, empty index, exact paths, protected-file integrity, and scoped whitespace only."
  }
}


## Historical focused F-01 and F-02 user report

{
  "feature": 5,
  "findings": [
    "F-01",
    "F-02"
  ],
  "parent_head": "6779cdefa13de9d45f3b0cc968089900037334c6",
  "repair_diff_sha256": "0d4c0b769ce834052333e883afdf668b594a4b02f5500a17aeb3a1eba4555ed3",
  "performer": "user",
  "report_verbatim": "everything passed",
  "context": "Reply to the request for focused repair browser results from Vite development and production preview.",
  "exact_guarded_cleanup_message": "Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.",
  "status": "user reported passing focused browser checks and supplied exact guarded cleanup output",
  "verification_record": "docs/verification/SERVICE_HISTORY_STATUS.md"
}


## Original Step 8 results (historical totals)

{
  "date": "2026-11-18",
  "feature": 5,
  "step": 8,
  "branch": "feature/record-and-review-service-history",
  "head": "4bffbb63d278bbe9b62e377d251c501622910e4b",
  "backend_database_free": {
    "passed": 2076,
    "integration_deselected": 441,
    "seconds": 40.63
  },
  "frontend": {
    "files": 11,
    "passed": 773,
    "failed": 0,
    "skipped": 0,
    "milliseconds": 1846.221
  },
  "native": {
    "passed": 441,
    "database_free_deselected": 2076,
    "seconds": 1043.15,
    "database": "garageguide_app_test",
    "run_db_tests": "1",
    "settings_file": "backend/.env.test",
    "first_statement_guard": true,
    "cleanup_receipts": 439,
    "cleanup_verified": true,
    "verified_absence_totals": {
      "users": 786,
      "sessions": 752,
      "vehicles": 346,
      "services": 174,
      "part_snapshots": 18,
      "maintenance_completions": 19,
      "schedules": 20
    },
    "read_only_no_receipt_cases": [
      "tests.test_health::test_real_database_health",
      "tests.test_user_queries_integration::test_health_transaction_is_read_only_on_native_database"
    ]
  },
  "pip_check": "No broken requirements found.",
  "lint": "passed",
  "production_build": {
    "passed": true,
    "modules": 65,
    "seconds": 2.35,
    "scoped_esbuild_elevation": true
  },
  "whitespace": {
    "tracked": "passed",
    "all_38_candidates": "passed",
    "untracked_candidates": 26
  },
  "browser": {
    "performer": "user",
    "date": "2026-11-18",
    "reported_version": "157.0.8103.79",
    "modes": [
      "Vite development",
      "production preview"
    ],
    "full_checklist_confirmed": true,
    "rerun_by_agent": false,
    "reported_cleanup_message": "Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.",
    "simulations_separate_from_real_behavior": true,
    "numeric_idle_duration_not_inferred": true
  },
  "review": {
    "type": "builder self-review of full Feature 5 delta",
    "files": 38,
    "confirmed_blockers": [],
    "unrelated_changes": [],
    "independent_audit": "required, not requested or run; pending approved checkpoint"
  },
  "constraints": {
    "no_stage_commit_audit_complete_merge_push": true,
    "application_files_unchanged_during_step_8": true,
    "feature_5_build_plan_unchecked": true,
    "no_schema_dependency_lockfile_or_private_environment_changes_in_proposal": true
  },
  "warnings": [
    "Existing Starlette/AnyIO BlockingPortal deprecation (one per pytest run)",
    "Node MockTimers experimental notices",
    "Git LF/CRLF notices"
  ],
  "packaging_note": "Initial read-only TAP summary assertion did not account for Windows CRLF. Parser normalized log line endings and passed; no application/test failure or source change.",
  "commands": {
    "backend_database_free": "backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m \"not integration\" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-5-step-8/backend.xml",
    "frontend": "node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js",
    "pip": "backend/.venv/Scripts/python.exe -m pip check",
    "lint": "npm --prefix frontend run lint",
    "build": "npm --prefix frontend run build",
    "native": "backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -x -p no:cacheprovider -o junit_logging=all --junitxml=blueprint/.state/staging/feature-5-step-8/native.xml",
    "whitespace": "git diff --check plus explicit UTF-8/final-newline/trailing-whitespace inspection of every candidate",
    "environment": {
      "node": "existing fnm v22.23.4 installation placed on PATH; no install",
      "native": "RUN_DB_TESTS=1; load_settings(testing=True) checked garageguide_app_test before pytest; no .env contents printed"
    }
  },
  "file_sha256": {
    "backend/app/main.py": "46703d737bb736a2d1f07e6ddb4fe1fdf3bbafc195bb9cf2d6109f4a85d7bed7",
    "backend/app/routes/services.py": "9d10323b6d3343077cd65421eb78a304d371c097b100a917e5926316cc17a864",
    "backend/app/service_queries.py": "41f7fdd8b0f7de08165bcfe2bc5d06778b746c7c5a7004bf588709592c05180e",
    "backend/app/service_schemas.py": "598c806b6a3f084cb03871dd13fd67d2b86f2a9138e31da232d0dfcdd057b8f2",
    "backend/tests/conftest.py": "e824d8da1abe893ec4dc27fdf08958e12acb327199844142db835eb84872df1c",
    "backend/tests/database_support.py": "12a6dcf935ece1011e5afc4d790e9d06d48c7386c4ab7feef60cb98b0c667147",
    "backend/tests/manual_registration_server.py": "987daa9863548a48933449220f4654352cb28378516ec251f53c8927a93b91a3",
    "backend/tests/test_manual_registration_server.py": "6e116f8d6794742cbdb594da86e81e693b5ac2fec492f58a0cd258b456b60ef4",
    "backend/tests/test_service_api.py": "15dac5874ff891f203e06e9402057b40259f28dadf4e615a232d8cc15b4ac11f",
    "backend/tests/test_service_api_integration.py": "584b8891b7bf416a29f8514eaa12a57d5a8c7428e1590323ab9e85cf3de22bcd",
    "backend/tests/test_service_fixture_safety.py": "cef10297c14d7a8e67c982316f4c145b76be4e483b78f54f2fc65aff2dc321d5",
    "backend/tests/test_service_link_fixture_safety.py": "d5421d31890c0ad9dea8d2e06ea34d491834ad231e0770f7375296d323009c5d",
    "backend/tests/test_service_patch_schemas.py": "a6a20a27c79d2ee0296c58bd3ba0b5894d0d7b36f58c5e31864da73757ea6a1e",
    "backend/tests/test_service_queries.py": "50a17cf93200528e79deae02c9ac2f78048464b8b6efd24d20c8994cb342b0c8",
    "backend/tests/test_service_queries_integration.py": "fadf8557a3190ea4329c19042eebfd9125d278f2c1054ae95fff77d2d660b067",
    "backend/tests/test_service_record_api.py": "dc0466c1a523ff7ed635bb53cd8a0d43f590166b7e0c50a026a9d704db905cef",
    "backend/tests/test_service_record_api_integration.py": "609429bd506a26286609685751ce9d2c0aab04e9140770f678fa1ee2b9a53fcf",
    "backend/tests/test_service_record_queries.py": "13ac21591c50144e5974756276a086b0dc7e4a806d19e249b9d1cdea7f067839",
    "backend/tests/test_service_record_queries_integration.py": "5fea3c86f8081c63715721c0f2fa4beae227e20a74d49c554e31d5fe119c8829",
    "backend/tests/test_service_schemas.py": "8080ac5e86d47a95b91e501d88f739ee297cc228fd1e6caaa8a22ace4c03a097",
    "blueprint/context/current-feature.md": "1610df4efb3140b9f0457ecbe6e0e4d1919688a6544dcf7a24a4075e7dc15086",
    "docs/verification/BROWSER_CHECKS.md": "4e89e2efe5bfebe116bc9280e04f14bbf9bb5bdf24992717fb8fb6c21b09a2fa",
    "docs/verification/SERVICE_HISTORY_STATUS.md": "e13ac2171e79c6ab7ca84b5e4ce07d0c515d880109b7e7e4efd6f0eb5b2a6379",
    "frontend/src/App.jsx": "1e1da7c86571412baa889a3fcba7aed28e58a696d2abbf8c60ec10a623078d22",
    "frontend/src/ServiceFields.jsx": "3158a5df4815924cb092f5bd5a1ea03ee14417386b6bc848f1f5b7ea97ab4669",
    "frontend/src/ServiceHistoryPage.jsx": "dfdb36d514206817c87b67cd31e5ed0f945be3673193eeeabc31c917b8b7952e",
    "frontend/src/ServiceRecordPage.jsx": "4268b1eb07dec03408d000fdd39fe54cc9c42f3dc0fa39e51cec4e9de7618aa0",
    "frontend/src/ServiceValues.jsx": "2fe1cd39873bdc2334464ba6d4460014682e2e50071c75e299de1cb087cbb7df",
    "frontend/src/VehicleDetailPage.jsx": "7d6033784a2e4eb43cec78ca51a2df204483956c8410a7d545be3d39f26f5a68",
    "frontend/src/api.js": "d966d4781400aad756e4c1f3c4edb87a47b03d05a6a3071fbddf708bd78d7c80",
    "frontend/src/serviceState.js": "d30231d916b111a29292dfce8248f50311bdeb0213072aafeb3237a8e6afc7fb",
    "frontend/src/serviceValidation.js": "72306fe47cf4840e363fba88f173d559c8d3eaf6539c93a72645c5208ceb0872",
    "frontend/src/styles.css": "ba8b27daf258e136266bca05518f08d36acc847779590419cd411d910303acfb",
    "frontend/src/vehicleRoutes.js": "1bf97cb10c078c13595b5f633e3d256ba855caff5e45d0429ca5478ebb8924f7",
    "frontend/tests/serviceApi.test.js": "d496aa85e0cddc8cbac0cda9da9c1f93dd28774354a6157953902bcb1c8b0e25",
    "frontend/tests/serviceFixtures.js": "1e33675a2914e2a5d70dd6014cd6583db509d87eb60bfd994f0a6f1becb51530",
    "frontend/tests/serviceSession.test.js": "233f01ebd942229062d4c1b22d1c33a84fc2c2e4f29fb9bb848ca9bcb76cf74a",
    "frontend/tests/serviceState.test.js": "d1af1e3c6706b85351d60dfea9da7ed4dbe2ffe0971599d52f0d0e3c51bb0e18"
  }
}


## Original Step 8 verification commands

{
  "backend_database_free": "backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m \"not integration\" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-5-step-8/backend.xml",
  "frontend": "node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js",
  "pip": "backend/.venv/Scripts/python.exe -m pip check",
  "lint": "npm --prefix frontend run lint",
  "build": "npm --prefix frontend run build",
  "native": "backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -x -p no:cacheprovider -o junit_logging=all --junitxml=blueprint/.state/staging/feature-5-step-8/native.xml",
  "whitespace": "git diff --check plus explicit UTF-8/final-newline/trailing-whitespace inspection of every candidate",
  "environment": {
    "node": "existing fnm v22.23.4 installation placed on PATH; no install",
    "native": "RUN_DB_TESTS=1; load_settings(testing=True) checked garageguide_app_test before pytest; no .env contents printed"
  }
}


## Preserved Feature 5 browser guide and user observations

# Manual browser verification

## Feature 5 Step 7: user-performed browser verification complete

The user reported manually running the Feature 5 browser checklist on November
18, 2026, with all checks run passing, using browser version 157.0.8103.79.
In a follow-up clarification, the user explicitly confirmed completing the
entire checklist in BOTH Vite development and production preview.

These are user-performed observations, not agent/reviewer browser execution.
Real service behavior and the checklist's simulated failure cases remain
separate; simulations do not prove a PostgreSQL outage or server revocation.
No additional per-case outcome or numeric idle duration is inferred from the
general pass report. Automated/native PostgreSQL evidence remains separately
recorded in SERVICE_HISTORY_STATUS.md; no tests or PostgreSQL connections were
rerun to record these observations.

The user reported this exact guarded-backend cleanup confirmation:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.
```

Both required browser modes and exact cleanup are confirmed. Step 7 was approved;
Step 8 final automated/native results are recorded separately in
SERVICE_HISTORY_STATUS.md and add no browser observations. The procedure below is retained for
repeatability and is not additional execution evidence. Historical Feature 1-4
records remain unchanged.

### Feature 5 F-03 focused repair: user-performed observations

The user confirmed completing all four focused Unicode repair steps in BOTH
Vite development and production preview after the inward-scanning trim change:

1. Long interior whitespace and U+FEFF were preserved in a synthetic record.
2. The affected record and an ordinary record appeared in history and opened
   correctly.
3. A cost-only edit sent only the changed cost in PATCH; description and notes
   were omitted.
4. Exact guarded cleanup was confirmed with the message recorded above.

This is focused user-browser evidence for the repair based on
`113b36db8be3a2bcc05a432559d383af069df0af`, not agent/reviewer execution, a full
checklist rerun, native-test execution, or a new simulated-failure run. No new
browser version or test date was supplied. Automated evidence remains separate.
F-01 stays closed; F-02/F-03 await fresh independent review. The original audit
receipt and findings remain unchanged. See SERVICE_HISTORY_STATUS.md for the
attributed report and cleanup text.

### Feature 5 guarded setup

Stop ordinary backend servers on port 8000. Use only the existing initialized
garageguide_app_test. Do not run SQL schema scripts, fixture SQL by hand,
ordinary production/development backends, or database reset commands. The
launcher loads only backend/.env.test, requires explicit RUN_DB_TESTS=1 and the
effective test database, and checks SELECT current_database() as the first
statement on every physical connection before exposing it. Remove conflicting
database environment overrides privately; never print credentials.

In terminal 1, from repository root:

```powershell
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe backend/tests/manual_registration_server.py --service-links
```

The launcher prints three reserved synthetic **email addresses**, not precreated
accounts or passwords. At /register, create A and B with the first two addresses
and C with the third. Choose your own temporary 15-128-character passwords and
use those same passwords at /login. Use two independent browser profiles or
normal/incognito for A and B (two incognito windows may share cookies). Do not
use ordinary accounts/data, copy cookie values, log passwords, or export request
bodies/screenshots containing secrets. Access logging is disabled in this
test-only backend. Keep the backend running through dev and preview.

Create distinct synthetic vehicles under A and B. Their histories start empty.
With --service-links, only C's newly created vehicles receive two synthetic
records: "Synthetic part-linked service" and "Synthetic completion-linked
service". These are test fixtures, not parts/schedule product functionality.
All service creations are reserved before writes. Edits/removal use immutable
tracked service/vehicle/owner IDs; missing/foreign/wrong-parent records still
reach the normal safe 404. No fixture may adopt an ordinary existing record.

Terminal 2:

```powershell
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
npm --prefix frontend run dev
```

Use http://127.0.0.1:5173. In another terminal with the same Node PATH, build
and start preview when ready; keep the same guarded backend:

```powershell
npm --prefix frontend run build
npm --prefix frontend run preview
```

Use http://127.0.0.1:4173. Sign in separately for preview; use new synthetic
vehicle/description suffixes so dev and preview evidence can be distinguished.
Do not start an ordinary uvicorn backend. If setup/guard/cleanup fails, stop;
do not switch to another database or broadly delete records to continue.

### Feature 5 real browser checklist — repeat in dev and preview

1. **Routes and gates:** From Account, open the garage, an owned profile, then
   Service history. Direct-load/refresh /vehicles/V/services and
   /vehicles/V/services/S (substitute your exact synthetic IDs). Repeat with
   trailing slashes, uppercase static segments, and percent-encoded static
   segments/ASCII ID digits. Leave via a Link and use Back/Forward as well as
   refresh. Authentication and business-loading gates must precede private
   history/identity. /vehicles/new must still open vehicle creation.
   Invalid IDs (01, 0, +1, 1.0, overflow, non-ASCII digits) and unrelated suffixes
   must show no cached service records. If Vite rejects a malformed direct HTTP
   path before React loads, record it as a server-boundary result only.
2. **Empty/list/create:** A's new vehicle has no services. Open its history and
   create maintenance, repair, inspection, and diagnostic records with dates and
   descriptions. Check newest service date first, then creation/id for ties.
   Create with neither reading/cost, mileage only, hours only, both readings,
   and confirmed zero readings/cost. Unknown values show Not recorded; zero
   readings show 0.0 and confirmed-free cost shows USD 0.00. Use exact decimal
   controls (for example 12345.6, 45.7, USD 42.50). Successful creation clears
   the form, then GET reloads history. Repeated clicks/Enter while pending must
   produce one POST. Identical deliberate records remain allowed.
3. **Fields/validation:** Required date/type/description must be labeled. Only
   four types are offered. Invalid/blank required text, impossible date, a
   future date (9999-12-31), negative/exponent/comma/excess-precision decimals,
   and overflow must give safe field errors, first-error focus, and corrected
   field-error clearing. The backend decides today; do not infer its day from
   the browser time zone. Optional blank notes become null. No raw error/input
   or driver information appears. There is no file upload or parts editor.
4. **Detail/edit/cancel:** Open a saved entry from history. Enter Edit, change
   values, then Cancel edit. It must send no PATCH and show the saved values.
   Save text/date/type changes and reload to confirm persistence. Save reading
   decreases and clear known mileage/hours/cost/notes to blank; no odometer
   confirmation is required for these historical snapshots. Inspect PATCH
   field names only: unchanged business fields are omitted; cleared optional
   values are null; zero stays an exact decimal string. No empty PATCH is sent.
   Save stays on detail and shows the committed response. Returning to the
   vehicle profile proves current mileage/hours/readings_updated_at unchanged.
5. **Removal:** Remove opens an inline confirmation explaining permanence and
   possible newer concurrent edits. Cancel removal sends no DELETE and retains
   the record/draft. Confirm once: one DELETE with literal confirm_removal true,
   then return to history and GET reload; the entry is absent. The old detail
   URL/repeated removal request returns the same safe 404. No automatic replay,
   force option, child-data disclosure, or undo promise is offered.
6. **Linked records, real backend:** Sign in as C and create a synthetic vehicle.
   Its two seeded service descriptions identify the test cases. Part-linked
   service edits succeed but removal returns the fixed linked-data conflict.
   Completion-linked actual edits return the fixed completion conflict;
   removal is also blocked. Cancel/unchanged saves perform no mutation in the
   UI; no-op API success is separately covered by native tests. Reload after
   each blocked operation: the saved service and vehicle readings are unchanged.
   Do not inspect child data or delete links to bypass protection. Native tests
   separately prove child-row integrity and real locking; browser UI alone
   cannot establish those database assertions.
7. **Ownership:** In independent A/B browsers, create records under each one's
   vehicles. Neither history includes the other's data. Try B's parent/history
   and service URLs while signed in as A and vice versa. Also put A's service
   ID under another vehicle A owns. Missing/foreign/wrong-parent individual
   cases show the same fixed Service record not found; collection parent cases
   show Vehicle not found. Neither can create under the other's vehicle, edit,
   or remove the other's service. Use only these synthetic IDs. Preserve safe
   status/body observations; no unscoped existence information should appear.
8. **Sessions/headers:** Inspect safe Network response metadata: no-store on
   service success/errors and Session-Expires-At only on successful 200/201.
   Current successful service responses update the local deadline without an
   extra /api/auth/session request solely for synchronization. Errors do not
   extend it. Protected navigation, refresh, visibility return, and deliberate
   retry may revalidate. Leave the page visible and inactive until the actual
   last returned local deadline: identity, records, drafts, and confirmation
   clear without an expiry-triggered request, polling, or automatic retry.
   Report the real waiting duration; fake-clock tests are not this observation.
9. **Stale work/isolation:** Throttle/delay a service GET or write, then navigate
   between vehicles/records, Back/Forward, log out, switch accounts, relogin as
   the same account, hide/return, or reach expiry. Old successes/errors must
   never restore old records/drafts, claim current success, or extend a newer
   deadline. A rejected session hides all private content. An unavailable
   session gates it and offers deliberate retry. Logout one independent browser;
   the other remains independent. Restore all network controls before real retry.
10. **Accessibility/layout:** Keyboard-only navigation, labels, field-error
    associations, first-error focus, status announcements, confirmation focus,
    Cancel returning focus, and explained disabled/pending controls work. Check
    long descriptions/notes and Not recorded/zero at 375, 768, and 1440 pixels
    and 200% zoom without horizontal scrolling or clipped controls.

### Feature 5 simulated failures and uncertain writes

These simulations are not evidence of a PostgreSQL outage, actual session
revocation, or the backend's transaction/failure ordering. Run them only against
the guarded backend. The following optional DevTools shim keeps no request
bodies, passwords, cookies, or record values and logs nothing. Install once;
do not layer it with other fetch shims. Select a method and mode, exercise one
case, then restore real fetch before real inspection.

```javascript
(() => {
  const original = window.fetch.bind(window)
  const check = { method: 'GET', mode: 'off', calls: 0 }
  check.restore = () => { window.fetch = original; delete window.serviceCheck }
  window.serviceCheck = check
  window.fetch = async (url, options = {}) => {
    const method = options.method || 'GET'
    if (typeof url !== 'string' || !/^\/api\/vehicles\/[1-9][0-9]*\/services(?:\/[1-9][0-9]*)?$/.test(url) ||
        method !== check.method || check.mode === 'off') return original(url, options)
    check.calls += 1
    if (check.mode === 'network') throw new TypeError('Simulated network failure')
    if (check.mode === 'timeout') return new Promise((resolve, reject) => {
      const abort = () => reject(new DOMException('Aborted', 'AbortError'))
      if (options.signal?.aborted) abort()
      else options.signal?.addEventListener('abort', abort, { once: true })
    })
    if (check.mode === 'commit-lost') {
      // Only use with POST/PATCH/DELETE: the real guarded mutation runs once.
      if (method === 'GET') throw new TypeError('Select a mutation method first')
      const response = await original(url, options)
      if (!response.ok) return response
      await response.body?.cancel()
      return new Response('invalid JSON', { status: method === 'POST' ? 201 : 200 })
    }
    if (check.mode === 'malformed') return new Response('invalid JSON', { status: method === 'POST' ? 201 : 200 })
    const cases = {
      unavailable: [503, 'Service history unavailable. Please try again.'],
      authentication: [503, 'Authentication unavailable. Please try again.'],
      rejected: [401, 'Not authenticated.'], forbidden: [403, 'Request not allowed.'],
      unexpected: [500, 'Internal server error'],
      conflict: [409, method === 'PATCH' ?
        'Service record is linked to maintenance completion and cannot be changed.' :
        'Service record has linked data and cannot be removed.'],
    }
    const [status, detail] = cases[check.mode] || cases.unexpected
    return new Response(JSON.stringify({ detail }), { status, headers: { 'Content-Type': 'application/json' } })
  }
})()
```

- For GET, try unavailable/network/timeout/malformed/unexpected. Private history
  must not be confused with an empty successful history. Restore fetch and use
  Try again or Reload history. Also simulate rejected/authentication on a
  service request: rejection clears private state, authentication availability
  gates it. The existing auth-session shim below can test the navigation gate.
- For POST/PATCH/DELETE, test unavailable/network/timeout/malformed/unexpected
  and forbidden. There must be one request per deliberate submit/confirmation,
  a ten-second timeout, no automatic retry, and no idle polling. Known validation
  and linked conflicts keep correctable drafts; service-only availability keeps
  drafts but applies mutation uncertainty. Clear all failure modes afterward.
- For a valid POST with mode commit-lost, the real create runs but its success
  body is deliberately lost. The form retains its draft, blocks submission, and
  explains how to inspect date/type/description/readings/cost. Set mode off,
  deliberately reload history, inspect, and verify the duplicate-risk warning.
  Even an absent entry must not be described as proof of failure. Acknowledging
  that risk only unlocks the form; it must not send another POST automatically.
- For PATCH commit-lost, use a known unlinked record. The edit may have committed.
  Resubmission is blocked. Reload explains draft discard and requires agreement;
  restore real fetch and inspect saved values before editing again.
- For DELETE commit-lost, use a disposable unlinked record and explicit removal
  confirmation. No automatic replay occurs. Restore real fetch; deliberately
  reload the record/history. A later 404 states only current absence, not which
  request removed it. Real backend commit/rollback behavior is native evidence,
  not inferred from the shim.
- To test confirmed creation followed by failed history reload, first load a
  normal history, then set method GET and mode unavailable, and submit a real
  valid creation. POST must succeed but its follow-up GET fails. Feedback must
  still say the record was created and block accidental reposting. Restore
  mode off and reload history. Record this as a simulated GET failure.
- Finish with serviceCheck.restore(); restore auth shims/throttling/blocking too.

### Feature 5 exact cleanup and report

Sign out all synthetic browsers, then Ctrl+C the guarded backend and wait for:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.
```

Cleanup recovers exact reserved creations if an acknowledgment was lost, removes
only tracked/reserved child fixtures before services, then vehicles/sessions/users,
and verifies absence through separate guarded connections. Unexpected children
or any failed guard/cleanup stop verification; never truncate, broadly delete,
reset sequences, run schema initialization, or declare a browser pass without
the verified marker. The marker above is expected output, not an observation.

Report date, exact browser/version, dev/preview results, real create/list/edit/
remove/linked checks, two-account observations, actual idle duration, focus and
viewport results, simulated failure modes and restoration, exact cleanup output,
and anything unverified. Do not claim native test reruns or reviewer/browser
execution from these instructions. The November 18 user report above satisfies
Step 7's mode/cleanup acceptance. Separately authorized Step 8 verification is
recorded in SERVICE_HISTORY_STATUS.md; this guide is not new execution evidence.



## Native PostgreSQL and exact cleanup evidence (reused)

{
  "database": "garageguide_app_test",
  "native_passed": 441,
  "receipt_count": 439,
  "verified_absence_totals": {
    "users": 786,
    "sessions": 752,
    "vehicles": 346,
    "services": 174,
    "part_snapshots": 18,
    "maintenance_completions": 19,
    "schedules": 20
  },
  "counts_meaning": "Aggregated tracked fixture identities verified absent, not SQL DELETE affected-row totals or a global database reset.",
  "cases_without_fixture_cleanup_receipt": [
    "tests.test_health::test_real_database_health",
    "tests.test_user_queries_integration::test_health_transaction_is_read_only_on_native_database"
  ],
  "tests_by_file": {
    "tests.test_authentication_api_integration": 57,
    "tests.test_health": 1,
    "tests.test_registration_integration": 7,
    "tests.test_service_api_integration": 52,
    "tests.test_service_queries_integration": 17,
    "tests.test_service_record_api_integration": 88,
    "tests.test_service_record_queries_integration": 48,
    "tests.test_session_queries_integration": 18,
    "tests.test_user_queries_integration": 4,
    "tests.test_vehicle_profile_api_integration": 62,
    "tests.test_vehicle_profile_queries_integration": 35,
    "tests.test_vehicle_queries_integration": 9,
    "tests.test_vehicles_integration": 43
  },
  "evidenceUse": "Recorded native evidence reused by the final reviewer and completion; no new connection or native rerun.",
  "rawArtifactIntegrity": [
    {
      "path": "blueprint/.state/staging/feature-5-step-8/native.xml",
      "bytes": 281819,
      "sha256": "9b9cfa058639d33035e5ba66fe8d0744e982e4da42c1540c111f7e831a7aa9f2"
    },
    {
      "path": "blueprint/.state/staging/feature-5-step-8/cleanup.json",
      "bytes": 144458,
      "sha256": "aa067ecf873c24ab2702ccbf7e3c8d4a546cf99eea884832d6e27cd5d8f59914"
    }
  ]
}


## Completion verification (fresh automated checks)

{
  "performedAt": "2026-11-19T23:54:32.028174+00:00",
  "targetHead": "a7f55e2f94c67ec3fb955fab3c9c9f4fa2782ebf",
  "specSha256": "1610df4efb3140b9f0457ecbe6e0e4d1919688a6544dcf7a24a4075e7dc15086",
  "commands": {
    "backend": "backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m \"not integration\" -p no:cacheprovider",
    "frontend": "node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js",
    "pip": "backend/.venv/Scripts/python.exe -m pip check",
    "lint": "npm --prefix frontend run lint",
    "build": "npm --prefix frontend run build",
    "whitespace": "git diff --check; git diff --cached --check; untracked archive UTF-8/final-newline/trailing-whitespace checks",
    "integrity": "Exact archive prefix/chunk hashes, resolved-only findings transform, F-04 preservation, canonical stubs, checkbox-only plan change, unchanged fingerprint/prior archives, source-tree recovery validation; details in completion validation artifact."
  },
  "backend": {
    "passed": 2077,
    "integrationDeselected": 441,
    "warnings": [
      "Existing Starlette/AnyIO BlockingPortal deprecation"
    ]
  },
  "frontend": {
    "files": 11,
    "passed": 777,
    "failed": 0,
    "skipped": 0,
    "warnings": [
      "Existing Node MockTimers experimental notices"
    ]
  },
  "pip": "No broken requirements found.",
  "lint": "passed; exit 0",
  "build": {
    "passed": true,
    "modules": 65,
    "seconds": 1.32,
    "scopedElevation": true
  },
  "native": "Reused 441 passes, 439 cleanup receipts; no PostgreSQL connection or rerun.",
  "browser": "Reused user November 18 development/preview evidence and focused repair reports; no agent browser run.",
  "findings": {
    "closed": [
      "F-01",
      "F-02",
      "F-03"
    ],
    "openNonblocking": [
      "F-04"
    ]
  },
  "tryGuide": "Reused exact Step 8 optional guide; not additional execution evidence.",
  "limitations": [
    "Network-backed npm audit unavailable within offline scope.",
    "No schema, dependency, private environment, generated product artifact, or unrelated change.",
    "F-04 remains open P2; no acceptance or repair.",
    "Normal index stays empty; source-tree evidence uses a separate temporary index only."
  ]
}


## Optional preserved manual demonstration

## Try it now

Run or do:
With the documented guarded test setup running and an owned synthetic vehicle, open its profile and select Service history. This is optional; the November 18 browser checklist does not need to be repeated for this handoff.

Expected:
An empty history or only that vehicle's records, with the labeled creation form. Unknown values read Not recorded; confirmed zeros retain 0.0 or USD 0.00.

This proves:
Protected profile-to-history navigation and saved-value presentation.

Failure signs:
Another account's records, private content before validation, or unknown values displayed as zero.


## Preserved input integrity

Offsets describe the raw archive prepared here. Original specification recovery
uses the completion annotation and exact-byte/EOL-candidate contract. Embedded
chunks are retained verbatim; only the three resolved finding heading IDs are
prefixed as documented. Original raw native logs remain at the hashed paths.

```json
[
  {
    "label": "F-01",
    "source": "blueprint/context/findings.md (only heading ID prefixed)",
    "offset": 54257,
    "byteLength": 1787,
    "rawSha256": "1121266cb511bbc8f48353d005c6edbdcc34d9773f944bbd97cd1b373f626902"
  },
  {
    "label": "F-02",
    "source": "blueprint/context/findings.md (only heading ID prefixed)",
    "offset": 56065,
    "byteLength": 2092,
    "rawSha256": "af8299a612d4d2f954fad0196161ff88eb152590fdab1f753cc290d3415b6c4e"
  },
  {
    "label": "F-03",
    "source": "blueprint/context/findings.md (only heading ID prefixed)",
    "offset": 58178,
    "byteLength": 1909,
    "rawSha256": "4bbc705fb9223bae2559b16d61230493a264d592c35cf3f45e7075aa51c1be84"
  },
  {
    "label": "carriedForwardF04",
    "source": "blueprint/context/findings.md (verbatim unresolved block)",
    "offset": 60137,
    "byteLength": 1025,
    "rawSha256": "5e30e5c2ad53fceec84c83106f7b8e81da1d5cdf17f5b32a36bde80cf357d714"
  },
  {
    "label": "passingReceipt",
    "source": "blueprint/context/review.md",
    "offset": 61187,
    "byteLength": 8120,
    "rawSha256": "4183b3b861c69447df08ebdf95cc2dc169651553e2b10053ed3527478f29ebb3"
  },
  {
    "label": "implementationHistory",
    "source": "git log --reverse 4bffbb63d278bbe9b62e377d251c501622910e4b..a7f55e2f94c67ec3fb955fab3c9c9f4fa2782ebf",
    "offset": 69343,
    "byteLength": 448,
    "rawSha256": "8064c5c3c4c47fdd16d93da79750bbf6f60b94a898da8b003474e2c278edf20a"
  },
  {
    "label": "originalAuditReceipt",
    "source": "blueprint/.state/staging/feature-5-original-audit-receipt.md",
    "offset": 69843,
    "byteLength": 4454,
    "rawSha256": "ae2a09ef15d53ab0ef89ab48f7109da5a5f2d5e0093888dd7729dc3a520847e4"
  },
  {
    "label": "preF03AuditReceipt",
    "source": "blueprint/.state/staging/feature-5-pre-f03-audit-receipt.md",
    "offset": 74347,
    "byteLength": 6016,
    "rawSha256": "be93fc57865216ae82f252e5e9ad7c9f5120f40f727fa8d534361a4a813f71a9"
  },
  {
    "label": "preF03Findings",
    "source": "blueprint/.state/staging/feature-5-pre-f03-audit-findings.md",
    "offset": 80412,
    "byteLength": 4829,
    "rawSha256": "df592d6a2730e692c87a1808ae62b3c5eaacfb445f2ae96a4d0788cd692c5991"
  },
  {
    "label": "serviceStatus",
    "source": "docs/verification/SERVICE_HISTORY_STATUS.md",
    "offset": 85293,
    "byteLength": 49484,
    "rawSha256": "80521de335effa4849fe80551d642a585cd6affba8527bc2aa200b2785f22412"
  },
  {
    "label": "originalCheckpoint",
    "source": "blueprint/.state/staging/feature-5-checkpoint-proposal.json",
    "offset": 134827,
    "byteLength": 15224,
    "rawSha256": "212b22bd59d389533d5188805086d67a7f5146bab777455c6e81748cb3ad0ad9"
  },
  {
    "label": "firstRepairCheckpoint",
    "source": "blueprint/.state/staging/feature-5-f01-f02-repair-checkpoint-proposal.json",
    "offset": 150098,
    "byteLength": 2764,
    "rawSha256": "b672853f403dc443e01d64c7dc0d79bdb4a760cc70d00ac3c3b823313bf2727e"
  },
  {
    "label": "finalRepairCheckpoint",
    "source": "blueprint/.state/staging/feature-5-f03-checkpoint-proposal.json",
    "offset": 152906,
    "byteLength": 2974,
    "rawSha256": "7363ec2c302afc7402ddcb50c3f61eae6e714a2e6f0a079c07af836b6fa96d0c"
  },
  {
    "label": "focusedBrowserReport",
    "source": "blueprint/.state/staging/feature-5-f01-f02-browser-report.json",
    "offset": 155931,
    "byteLength": 759,
    "rawSha256": "61f4f3a10d4e3903bba0a8b9f75c7a3be13c9e455e494263f4f556938d494845"
  },
  {
    "label": "originalStep8Results",
    "source": "blueprint/.state/staging/feature-5-step-8/results.json",
    "offset": 156740,
    "byteLength": 8645,
    "rawSha256": "5fc7e33e0f3564cfd4c021f3b734e3e12381460bef99592cf09e0dbee2508739"
  },
  {
    "label": "originalStep8Commands",
    "source": "blueprint/.state/staging/feature-5-step-8/commands.json",
    "offset": 165429,
    "byteLength": 1390,
    "rawSha256": "1abbf655d0f7e33586d92618eff14905e371a72df4589cc6c91543dffb11cdf4"
  },
  {
    "label": "feature5BrowserRecord",
    "source": "docs/verification/BROWSER_CHECKS.md (exact Feature 5 prefix)",
    "offset": 166881,
    "byteLength": 17870,
    "rawSha256": "99fcdb31da61813f822f30f5894556070203b2fd61a0e3e2bd69ad643d90872d"
  },
  {
    "label": "nativeCleanupSummary",
    "source": "original native JUnit and cleanup.json, read-only summary",
    "offset": 184811,
    "byteLength": 1824,
    "rawSha256": "3cc141594b53254fec94084e59b29c379d55a697c09c66b6bdfbb8b53c0168da"
  },
  {
    "label": "completionChecks",
    "source": "this completion final automated checks",
    "offset": 186690,
    "byteLength": 2617,
    "rawSha256": "470af304355e748344c670a83b3ba48c1739bcaf2d6e48d2aa55b73c704e0574"
  },
  {
    "label": "tryGuide",
    "source": "blueprint/.state/staging/feature-5-step-8/try-it-now.md",
    "offset": 189353,
    "byteLength": 627,
    "rawSha256": "e30110b148ff6b944ed0beccd27d32d213cc07bdaf77cc43ddc2e20b8814fdde"
  }
]
```
