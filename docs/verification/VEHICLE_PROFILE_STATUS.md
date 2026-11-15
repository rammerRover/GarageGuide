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
