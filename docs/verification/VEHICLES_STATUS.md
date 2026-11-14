# Vehicle creation and listing verification status

Feature 3: Create and list vehicles in a digital garage.

Branch: `feature/create-and-list-vehicles-in-a-digital-garage`.
Steps 1 through 4 and the user's November 13, 2026 browser evidence are approved.
Step 5 final implementation verification and checkpoint preparation are complete.
The specification is verified for implementation, with every build step checked.
The revised exact checkpoint awaits explicit staging/commit approval and a
separate required independent audit. Feature 3 is not complete; no staging,
commit, independent audit, or landing has occurred.

## Recorded automated evidence

These are historical Step 1 through 4 checks. Fresh Step 5 executions are
recorded separately below. Focused results are subsets of their complete suites.

| Evidence | Recorded result |
| --- | --- |
| Step 1 focused vehicle schemas | 188 passed |
| Step 2 focused database-free query/fixture/support checks | 85 passed |
| Step 3 focused database-free API/query/support checks | 139 passed, including 89 vehicle API tests |
| Step 4 focused frontend checks | 128 passed |
| Step 4 complete six-file frontend Node suite | 298 passed; zero failures, cancellations, or skips |
| Latest complete database-free backend suite, Step 4 | 681 passed; 139 integration tests deselected |
| Step 4 frontend lint | Passed |
| Step 4 frontend production build | Passed after the scoped retry outside the sandbox directory-access restriction |
| Step 4 Python dependency check | No broken requirements found |
| Step 4 tracked/new-file whitespace checks | Passed |

Node reported its experimental MockTimers warning. Backend runs reported the
existing Starlette/AnyIO deprecation warning. The complete frontend command is
recorded in README.md, coding-standards.md, and current-feature.md. These logic
tests and build checks do not prove browser rendering or real browser activity.

## Recorded native PostgreSQL evidence

This evidence was executed during Step 3 and is not a new native test run.
With `RUN_DB_TESTS=1`, the complete guarded native suite passed 139 tests with
zero failures/errors/skips; 681 database-free tests were deselected. It included
43 new vehicle API cases plus registration, authentication, session/concurrency,
vehicle-query, and health regressions.

The ignored local report is
`blueprint/.state/staging/feature-3-step-3-native.xml`. Its 137 exact-cleanup
receipts verified absence of 182 tracked synthetic users, 148 sessions, and
21 vehicles across fixtures. The 43 new API cases had 43 cleanup receipts for
86 users, 86 sessions, and 11 vehicles. These are tracked-record absence totals,
not SQL affected-row counts.

Native connections required test-only settings and first-statement
`SELECT current_database()` verification for exactly `garageguide_app_test`.
Vehicle reservations preceded writes; deletion used exact vehicle IDs and
fixture owner IDs before user cleanup. Separate guarded connections verified
absence. Failure/availability and lost-acknowledgment cases used injected
simulations around native operations, not observed PostgreSQL outages.

The prior native cleanup evidence does not substitute for cleanup evidence from
the later user-performed browser run. No PostgreSQL connection or native suite
was run during Step 4 implementation or its original browser-observation
documentation update. Fresh Step 5 native execution is recorded separately below.

## User-performed browser observations: November 13, 2026

Reported by the user in Google Chrome **156.0.8078.73**, in both Vite development
and production preview. The version comes from the user's explicit version
statement; the template's version placeholder is not an additional version.
The agent did not execute these browser checks.

The user reported the following real observations:

- `/vehicles` and `/vehicles/new` required session validation before displaying
  private content. Direct loads, refresh, and Back/Forward protected the garage.
  Account navigation reached the garage.
- The empty garage displayed correctly. Cancel returned without creating a
  vehicle.
- Creation worked with mileage only, operating hours only, both readings,
  neither reading, and confirmed zero. Unknown readings displayed `Not recorded`;
  confirmed zero displayed `0.0`.
- Successful POSTs returned to the garage and reloaded the list through GET.
  Repeated submission attempts did not cause duplicate POSTs.
- Validation, field-error clearing, focus behavior, and announcements worked.
- Two independent browser sessions demonstrated that account A could not see
  B's vehicles and B could not see A's vehicles.
- Vehicle GET and POST responses included `Cache-Control: no-store`; successful
  responses included `X-GarageGuide-Session-Expires-At`.
- Vehicle responses updated the local deadline without an extra authentication
  request solely for synchronization. No periodic session or vehicle polling
  occurred while idle.
- At the full visible idle deadline, private identity and vehicle data cleared
  locally without an expiry-triggered API request or automatic retry. This is
  the user's reported full visible idle observation, separate from fake-clock
  automated tests.
- Keyboard operation, visible focus, layouts at 375/768/1440 pixels, and 200%
  zoom worked. Both environments passed the applicable reported checks.

The user separately reported unavailable/retry, rejected-session, uncertain-POST,
and stale-response simulations behaving according to the browser guide. These
are browser simulations, not evidence of a real PostgreSQL outage.

In a follow-up, the user confirmed all manual checks are complete, specifically
including idle timeout, GET/POST session behavior, adding vehicles, and comparison
between two accounts. This confirms manual-check completion as user-provided
evidence. It does not imply an agent browser run, new timings or screenshots,
or a real database outage behind simulated failures.

## User-reported browser cleanup evidence and Step 4 acceptance

The user subsequently supplied the exact guarded backend message:

```text
Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.
```

This confirms browser-run cleanup as user-provided evidence. It is not a new
agent-run database check and is separate from the earlier native-suite cleanup
totals. The original placeholder no longer blocks Step 4 acceptance.

The recorded automated checks, reported real browser behavior and simulations,
and user-confirmed cleanup satisfy the Step 4 acceptance criteria. The user
subsequently approved Step 4 and authorized Step 5 verification and proposal
preparation. Step 5's independent-review gate remains pending.
The subsequent all-checks confirmation supplements the original enumerated
observations; no detailed per-case trace is invented. Automated coverage remains
separate. The repeatable guide is in BROWSER_CHECKS.md.

Only documentation changed during Step 5. Application code and tests are
unchanged from the approved implementation/browser-evidence state. Staging,
commits, independent audit, completion, merging, pushing, deployment, and
Feature 4 remain outside this verification turn's authorization.

## Step 5: freshly executed final verification

These are new executions for Step 5, not the historical Step 3 native totals
relabelled as another run. Commands were run from the repository root using the
existing Python 3.13.17 environment and fnm-managed Node 22.23.4 installation.
No dependencies or runtimes were installed.

| Check | Actual result |
| --- | --- |
| Complete database-free backend suite | 681 passed, 139 integration tests deselected; zero failures/errors/skips; 10.10 seconds |
| Python dependency consistency | No broken requirements found |
| Complete six-file frontend Node suite | 298 passed; zero failures, cancellations, skips, or todos |
| Frontend lint | Passed, no lint diagnostics |
| Production build | Passed; Vite 6.4.5 transformed 57 modules; 1.82 seconds |
| Complete guarded native integration suite | 139 passed, 681 database-free tests deselected; zero failures/errors/skips; 114.49 seconds |
| Exact native cleanup | 137 receipts; 182 tracked users, 148 sessions, and 21 vehicles verified absent |
| Whitespace, index/status, full builder diff | Passed review/checks; index empty; working tree intentionally uncommitted |

Backend command:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-3-final-backend.xml
backend/.venv/Scripts/python.exe -m pip check
```

The complete frontend command, including all current test files:

```powershell
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js
npm --prefix frontend run lint
npm --prefix frontend run build
```

The test command's stdout/stderr was captured through PowerShell `Tee-Object`
to ignored `blueprint/.state/staging/feature-3-final-frontend.tap`, with its native
exit code preserved. Node reported the experimental MockTimers warning. Backend
runs each reported the existing Starlette/AnyIO deprecation warning. Build ran
outside the sandbox because of the already established esbuild parent-directory
access restriction; no application fix or configuration change was needed.
Git emitted its expected Windows LF-to-CRLF notices during diff/hash inspection.
None of these warnings was a failed test or waived gate.

Fresh native command:

```powershell
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider --junitxml=blueprint/.state/staging/feature-3-final-native.xml -o junit_logging=system-out
```

The suite loaded only test settings from `backend/.env.test`, rejected any
effective database other than `garageguide_app_test`, and verified that exact
database once as the first statement on every physical guarded connection.
Existing fixture finalizers were registered before writes. Vehicle reservations
were recorded before inserts; cleanup used exact vehicle IDs plus owner IDs,
then exact sessions and users. A separate guarded connection verified absence.
No truncation, prefix-wide deletion, sequence reset, schema initialization, or
schema alteration was performed.

The 43 vehicle API cases contributed 43 cleanup receipts for 86 tracked users,
86 sessions, and 11 vehicles; the nine query cases and existing regressions are
also included in the complete suite. Total counts describe tracked records
verified absent, not numbers of rows affected by DELETE. Two health tests
reserved no records and needed no synthetic cleanup receipt. No cleanup failed.
The fresh XML/TAP results and parsed totals are ignored local review artifacts;
they are not proposed source files.

## Builder review and scope checks

This is the implementation builder's review, not `$audit independent current`.
The findings and independent-review files remain canonical empty stubs, with no
current independent receipt. A fresh independent audit is required after the
user approves and creates the exact immutable checkpoint.

| Area reviewed | Evidence and conclusion |
| --- | --- |
| Ownership | Both routes use the existing validated session dependency; GET binds only `actor.user.id`; INSERT assigns that ID. Request extras/ownership fields are forbidden. Native two-account tests prove owned-list isolation. |
| SQL and transactions | Explicit columns and parameterized values only. Read-only list business transaction; owned write transaction for create. Decimal/null bindings and database timestamps. Public-model validation, JSON preparation, and deadline attachment occur before commit; success returns after commit/closure. Failure tests cover rollback, preparation, and lost acknowledgments. |
| Validation | Deterministic backend-year provider; strict create fields, Unicode/NUL checks, exact NUMERIC-compatible decimal strings, null versus zero. Read models retain the wider stored-year range. No new schema/type coercion is required. |
| Safe errors and cookies | Vehicle-specific approved-field/fixed-message boundary; no credential-whitelist changes. Policy failures precede business writes. Existing 401 deletion and authentication 503 preservation remain distinct from vehicle 503; unexpected errors are generic 500 with fixed logs. |
| Deadline response path | Reusable attachment copies the already committed actor deadline onto successful 200/201 responses only. Failed query/preparation/commit paths discard the prepared success response. All vehicle responses, including routing errors and redirects, are no-store. |
| Routes and stale responses | Actual shared React Router definitions feed `matchRoutes`, including decoded/case/slash variants. Authentication, navigation, and current-request generations reject stale data/deadlines, including same-user login, history-key reuse, visibility changes, logout, and expiry. |
| Local expiry and state | Expiry gates/clears identity without network renewal. Only current successful authenticated work updates the timer from server metadata. No private browser-storage caches, token exposure, automatic retries, or polling were added. |
| Proportional scope | Focused schemas, query module, route boundary, shared route/deadline helpers and testable page state serve current requirements. No ORM, generic repository, schema migration, pool, extra dependency, detail/edit/delete endpoint, or future product page was introduced. |

No confirmed in-scope blocker was found by this builder review. Independent
review may still identify findings; this statement is not a passing receipt.
No application behavior changed during Step 5, so no new browser-repeat claim
or agent browser execution is made. The approved user observations above remain
the browser evidence for the unchanged implementation.

Git inspection confirms no changes to SQL/schema files, dependency declarations,
lockfiles, pytest settings, environment examples, or Vite configuration. Private
`backend/.env` and `backend/.env.test` remain ignored and unstaged; internally
compared content fingerprints were unchanged before/after Step 5 verification.
Build output, caches, and local review artifacts are ignored and excluded.
Build/tests naturally generated ignored artifacts; no generated output is
proposed for Git. The unrelated user edit in `backend/prepapp.txt` was preserved
unchanged and is excluded from the checkpoint, with its own inventory entry.

## End-to-end request flow

React gates the garage/form through the existing session state and protected
routes. Vehicle helpers send relative `/api/vehicles` requests with same-origin
credentials through Vite's development/preview proxy to FastAPI. Database
credentials stay on the backend. POST uses JSON and the approved CSRF marker;
the existing exact trusted-Origin policy runs before parsing/business writes.
Pydantic validates/normalizes the create fields, preserving null versus zero.

The session dependency locks, validates, extends, and commits the server-side
session before yielding the trusted actor. Vehicle queries use only that actor's
ID in a separate short psycopg transaction. PostgreSQL either selects the owned
list or inserts the actor-owned vehicle with Decimal/null readings and database
timestamps. The public result and response, including the committed session's
public deadline, are prepared before the business transaction commits. Only
after commit and cleanup does FastAPI return 200 or 201 with no-store headers.

React validates the public shape/deadline and accepts it only for the still
current authenticated generation, navigation, and request. It updates the local
timer without a second authentication request. A confirmed create clears the
form and navigates to a fresh GET of the garage; a failed reload does not turn
the confirmed create into failure. Unknown/zero readings stay distinct. Lost
acknowledgments can conceal a commit, so uncertain POST feedback directs the
user to check the garage before any deliberate resubmission. There is no
automatic retry or timer-driven request.

## Frozen checkpoint and remaining limits

The exact proposal is
`blueprint/.state/staging/feature-3-verified-checkpoint-proposal.json`; its review packet,
complete inventory/purposes/raw hashes, feature builder diff, and separate full
working-tree diff are local ignored artifacts. They bind to parent HEAD
`46128d31c7e3d928636668804bad4a6ce74c1b9a` on the frozen feature branch. No index
changes have been made. Proposed message:

```text
feat: create and list vehicles in a digital garage
```

- Explicit staging/commit approval remains required. Only after that checkpoint
  exists may `$audit independent current` review its exact new HEAD and frozen
  specification. No independent audit was run against this uncommitted work.
- Browser evidence is user-performed on November 13, 2026, not an agent-run
  browser test or a new Step 5 browser execution. Unreported individual guide
  cases are not inferred. Node router/state tests do not prove DOM, layout, or
  assistive-technology behavior beyond the user's actual observations.
- Failure simulations are not real PostgreSQL outages. Lost-acknowledgment
  tests deliberately simulate uncertainty around real guarded native commits.
- Lists remain unpaginated, identical vehicles are allowed, and server-side
  idempotency is intentionally absent. Detail/edit/delete and Feature 4 are
  outside scope. Existing production-authentication hardening decisions remain
  outside this feature.
- The working tree remains dirty with the proposed feature files plus the
  excluded `backend/prepapp.txt` edit. No commit, completion, merge, push,
  deployment, branch deletion, or next feature is authorized.
