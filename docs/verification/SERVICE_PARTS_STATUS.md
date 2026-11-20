# Parts used verification

Feature 6: Record parts used during a service.

## Current status

Step 3 was approved. Step 4's Parts used interface and guarded manual setup are
implemented. Automated and native final verification passed as recorded below.
The user confirmed the complete browser checklist passed in development and
production preview on November 20, 2026, including the full visible idle check
and exact cleanup. Step 4 is complete and awaiting final review/checkpoint
approval. No staging, commit, audit or feature completion is authorized by this
record. F-04 remains open and nonblocking, unchanged.

Branch: `feature/record-parts-used-during-a-service`.
Parent HEAD: `a55857122368529eba9481ff4613abdc94285716`.
Verification date: November 19, 2026. No agent-controlled browser run occurred.
User-browser evidence recorded: November 20, 2026. Application/test hashes match
the passing November 19 candidate; automated/native checks were not rerun for
this documentation update.

## Contract and implementation review

- The active specification and API both use POST
  `/api/vehicles/{vehicle_id}/services/{service_id}/parts/lookup`.
  The specification does not say `/catalog-match`; no route discrepancy or
  contract edit was needed before wiring the section.
- The existing protected service-detail page renders the new section after its
  service request completes. It uses the Step 3 request/state helpers without
  adding a page, route, catalog browser, dependency or compatibility claim.
- Saved snapshots, manual draft, exact pair and reviewed preview are separate.
  Manual entry works independently of the catalog. Lookup spelling/case is
  preserved. Saving rechecks all preview identity fields and copies only the
  locked catalog row. A stale preview inserts nothing and needs deliberate
  lookup or explicit manual entry. Catalog change/deletion preserves copied
  historical text; a null reference is not labeled as proof of manual origin.
- Removal requires explicit confirmation and affects only the chosen snapshot.
  The service and catalog entry remain. Parent service locks serialize attachment
  with service removal. No vehicle/service readings, cost or maintenance links
  are updated by snapshot operations. Values are bound SQL parameters.
- Public JSON is prepared inside the business transaction. Success leaves the
  connection context only after commit/closure. Known failures roll back and
  close before safe translation; uncertain acknowledgments cannot promise
  rollback. The frontend never automatically retries a write, requires reload
  and inspection, and warns that a missing entry does not prove an Add failed.
- Service edits/removal and parts requests disable each other's active controls
  with synchronous state checks. This avoids overlapping the existing session
  store's single private-request slot. Canceling service/part confirmation sends
  no mutation. Reload warnings explain draft/preview effects.
- Existing authenticated actor, CSRF/Origin/JSON rules, safe errors, no-store
  and committed deadline helper are reused. Only successful current-generation
  results can advance the deadline. No polling or expiry-triggered request is
  added. Old service request helpers/F-04 are not repaired incidentally.
- Inputs have labels, hints/error associations, first-error/preview focus,
  inline removal/reload panels, cancel focus restoration, status announcements,
  disabled pending controls and wrapping CSS. Accessibility/responsive evidence
  comes from the user's checklist below; source/build alone is not proof.

## Automated checks run in Step 4

Commands run from the repository root using the existing Python virtual
environment and fnm Node 22.23.4. No installation or unrelated upgrade occurred.

| Check | Actual result |
| --- | --- |
| Focused manual-server and fixture safety checks | 77 passed; Starlette/AnyIO deprecation warning |
| Complete database-free backend suite | 2660 passed, 537 integration tests deselected; 1 deprecation warning; 33.23 s |
| Complete Node command, all 13 test files | 978 passed, 0 failed/cancelled/skipped; 1.07 s; existing experimental MockTimers warnings |
| Backend pip check | No broken requirements found |
| Frontend lint | Passed |
| Frontend production build | Passed on final UI; Vite 6.4.5, 68 modules; 1.38 s |
| Tracked and untracked whitespace checks | Passed; candidate diff/manifest include all 28 feature files |

Focused command:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_manual_service_parts.py backend/tests/test_manual_registration_server.py backend/tests/test_service_part_fixture_safety.py -p no:cacheprovider --tb=short
```

An initial focused run had 76 passes/1 failure because a Mock constructor's
`name` argument names the mock rather than creating a string `.name` attribute.
The fixture-result stub now uses SimpleNamespace. The rerun passed all 77;
this was a test-double correction, not a product or guard-policy change.

Complete commands:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pip check
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js frontend/tests/servicePartApi.test.js frontend/tests/servicePartState.test.js
npm --prefix frontend run lint
npm --prefix frontend run build
git diff --check
```

The Node suites cover request shapes, ID validation, preview invalidation,
uncertainty, required refresh, duplicate guards, stale responses, authentication
generations and deadlines, including the existing F-01/F-02/F-03 regressions.
There is no installed DOM/browser runner; these are logic tests, not UI evidence.

## Native PostgreSQL verification (separate from browser)

The final complete run PASSED: **537 passed, 2660 deselected, 0 failures or
skips**, 821.69 seconds. One existing Starlette/AnyIO deprecation warning.
This November 19 Step 4 run is distinct from the earlier Step 2/3 runs; it is
reused unchanged for the November 20 documentation/evidence refresh.

```powershell
$env:RUN_DB_TESTS = '1'
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -x -p no:cacheprovider -o junit_logging=all --junitxml=blueprint/.state/staging/feature-6-step-4/native.xml
```

Only `backend/.env.test` is loaded. Settings must name `garageguide_app_test`;
every physical test connection checks `SELECT current_database()` as its first
statement before exposure. No connection is redirected to the application
database, no schema is initialized/changed, and cleanup is registered before
writes. Exact snapshot/linked children are cleaned before services, vehicles
and users; exact synthetic catalog IDs are cleaned after their references.
Separate guarded connections verify absence. No truncation, prefix deletion,
sequence reset or adoption of ordinary data is permitted.

The captured JUnit report contains 535 exact synthetic cleanup receipts. The
remaining two tests (`test_real_database_health` and
`test_health_transaction_is_read_only_on_native_database`) are read-only health
checks without synthetic fixtures. Across the 535 receipts, these tracked
synthetic IDs were verified absent through separate guarded connections:

| Record type | Tracked IDs verified absent |
| --- | ---: |
| Users | 978 |
| Sessions | 944 |
| Vehicles | 460 |
| Services | 288 |
| Part snapshots | 50 |
| Maintenance completions | 19 |
| Schedules | 20 |
| Catalog entries | 30 |

These are verified fixture ID counts, including IDs already removed by a test,
not a claim of deleting that many rows during cleanup or clearing ordinary data.
All 537 cases passed and no cleanup failed. Raw results and the receipt summary
are in ignored `blueprint/.state/staging/feature-6-step-4/native.xml`,
`native.log`, and `cleanup.json`. Summarizing those recorded receipts opened no
additional database connection and did not rerun the suite.

Two new native tests exercise the test-terminal catalog controller directly:
create/change/replace/delete preserve snapshot text and parents, reject stale
previews, and refuse untracked linked rows. They do not start a browser/server
and must not be described as browser evidence. Existing native tests also prove
attachment/removal lock order in both directions using database blocking
evidence, ownership, transactions, safe API responses and Features 1-5 regressions.

## Prior-step results (historical, not new Step 4 runs)

- Step 1: 264 focused database-free schema passes.
- Step 2: 592 focused database-free passes; 95 native query/regression passes.
  All 95 per-test cleanup receipts confirmed absence of 190 users, 190 sessions,
  114 vehicles, 108 services, 31 snapshots, 12 completions, 13 schedules and
  20 catalog IDs. These are tracked synthetic ID counts, not ordinary deletions.
- Step 3: 184 focused API passes; 201 focused Node passes; complete gates then
  had 2638 backend/978 Node passes. Final native API run: 65 passed. All 65
  cleanup receipts confirmed 130 users, 130 sessions, 73 vehicles, 73 services,
  8 snapshots and 7 catalog IDs absent. An earlier 25-pass/1-failure API run
  exposed a test helper adding Content-Type to an intended missing-header case;
  raw JSON fixed that test setup. Three-case recheck and final 65 passed; all
  94 cleanup receipts across initial/recheck/final runs were verified. No
  application-policy relaxation was made.
- Earlier command/results/cleanup artifacts remain in ignored
  `blueprint/.state/staging/feature-6-step-2/` and `feature-6-step-3/`.
  They are distinct from final Step 4 results and are not checkpoint files.

## User-performed browser verification: complete

The user reported all performed Feature 6 checks passed, then explicitly
confirmed the entire checklist in BOTH Vite development and production preview,
including the full visible idle-deadline check. Test date: November 20, 2026.
Browser version: 157.0.8103.79. Browser product name was not separately supplied;
no name is inferred from an older feature's report. No checks were reported
skipped after the whole-checklist confirmation.

Real browser/backend coverage reported through that checklist: manual entry
with an empty catalog, exact catalog selection/miss, reviewed preview and stale
preview recovery, explicit manual switch, snapshot survival after catalog changes
or deletion, quantity and optional values, list/confirmed removal/cancel/re-add,
service deletion blocking, account isolation, protected navigation, headers and
deadline synchronization without extra authentication requests, local expiry
without polling/renewal, keyboard/focus/announcements and responsive widths/zoom.
These are the user's checklist observations, not agent-controlled browser runs
or newly inferred detailed traces. No numeric idle duration or unreported
assistive-technology testing is claimed.

### Simulated failures (separate from real behavior)

The checklist's simulated network/timeout, rejected/forbidden/unavailable,
malformed/unexpected response, required-refresh failure, stale work and lost
write-acknowledgment checks are covered by the user's complete pass report.
They remain browser simulations, not proof of real PostgreSQL outages, server
revocation or a genuinely lost commit acknowledgment. Recorded native tests
remain a separate category; no native suite or browser session was rerun by the
agent to enter this report.

### User-reported guarded cleanup

The user supplied this exact final backend message:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, schedules, and catalog entries are absent.
```

This confirms the reported guarded browser fixture cleanup, separately from the
535 automated native cleanup receipts above. Step 4 is complete and awaiting
final review. The repeatable procedure is retained in BROWSER_CHECKS.md.

## Limitations and review handoff

- Browser evidence is user-performed and covers the confirmed checklist; no agent
  browser run or earlier-feature browser evidence is substituted. No additional
  browser traces, product name, numeric idle duration or assistive-technology
  coverage is inferred. No independent audit has run for Feature 6.
- POST/DELETE uncertainty is preserved; list absence is not proof of failure.
  Identical attachments are allowed, with no automatic retry/idempotency layer.
- No real catalog seed, browsing, saved parts, fitment assertion, cost calculation,
  schema migration, ORM, dependency, session-algorithm change or F-04 repair.
- Existing Starlette/AnyIO and Node MockTimers warnings remain. Git's LF/CRLF
  conversion notices describe working-copy policy, not whitespace-test failure.
- Passing focused/full runtime evidence is reused while applicable code and
  environment are unchanged. Final documentation, hashes and checkpoint
  preparation cause file/whitespace checks, not repeated runtime suites.
- The final review packet/manifest freezes current code, specification progress
  and user-attributed evidence after browser confirmation. All 28 paths and raw
  hashes were refreshed; only three verification/progress documents changed
  since the passing candidate. It is a proposal for review, not staging, commit,
  independent-audit or feature-completion authorization.
