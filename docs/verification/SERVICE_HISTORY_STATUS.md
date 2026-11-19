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
