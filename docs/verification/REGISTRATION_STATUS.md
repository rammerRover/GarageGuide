# Feature 1 registration verification

Results recorded November 4, 2026 on Python 3.13.17 and pytest 8.3.5.
Scope: Build Step 2 direct queries/transactions, Build Step 3 registration
API behavior, Build Step 4 automated/user-browser verification, and Step 5 final
verification. **Build Steps 1-4 are approved. Step 5 checks passed; one local
review checkpoint is now approved and the independent audit is pending.** This
record does not declare the feature complete or ready for `$complete`.

## Build Step 2 results

| Check | Observed result |
| --- | --- |
| Database-free backend gate | 82 passed, 5 integration cases deselected; 2.47 seconds. Includes 23 database-access/guard/cleanup cases and the existing 59 cases. |
| Targeted native Step 2 gate | 4 passed; 2.19 seconds. `RUN_DB_TESTS=1` was enabled only for the command and its previous environment value was restored afterward. |
| Database safety | Settings required `garageguide_app_test` before connecting. Every native connection verified `SELECT current_database()` as its first statement before use; each new physical connection was checked once. |
| Schema prerequisites | Read-only metadata checks confirmed the existing `users` columns and `users_email_key` unique constraint. No schema was initialized, altered, or reset. |
| Committed account and sequential duplicate | A synthetic account was visible on a separate connection. Its returned public fields and stored hash matched; subsequent creation raised the duplicate-email error and left one account. |
| Failed transaction and recovery | Two inserts of one synthetic email triggered a native uniqueness failure. The entire transaction rolled back, the connection closed, and a new transaction successfully created that email afterward. |
| Cleanup after simulated lost response | Cleanup recovered the committed account's ID using its exact reserved email, deleted that ID/email pair, and verified absence. |
| Automatic fixture cleanup | Per-test finalizers removed only reserved synthetic records and verified their absence after commit. All teardown checks passed. |
| Native read-only mode | `SHOW transaction_read_only` returned `on` for the read-only connection. Existing database-free health tests also passed. |
| Whitespace validation | `git diff --check` passed for the reviewed changes. |

Both pytest runs emitted the existing Starlette/AnyIO deprecation warning about
`anyio.abc.BlockingPortal`. It did not fail either test run.

### Commands executed for Step 2

From the repository root:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider
```

With `RUN_DB_TESTS=1` temporarily set, without overriding `PGDATABASE`:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_user_queries_integration.py -m integration -p no:cacheprovider --maxfail=1
```

Native writes were limited to unique synthetic users in `garageguide_app_test`.
Cleanup used parameterized exact ID/email predicates, with no broad deletion,
truncation, schema changes, or sequence resets. Identity counters may advance.
No write to `garageguide_app`, `postgres`, or another database was authorized or
performed by these checks.

## Build Step 3 results

Observed November 4, 2026 using the same Python/pytest runtime.

| Check | Observed result |
| --- | --- |
| Complete database-free gate | 113 passed, 12 integration cases deselected; 7.30 seconds. Includes 31 registration API cases and all previous database-free cases. |
| Complete guarded native gate | 12 passed, 113 database-free cases deselected; 10.00 seconds. Includes 7 registration API cases, 4 direct-query cases, and the existing native health case. |
| Committed success | HTTP 201 returned exactly ID, normalized email, and a timezone-aware creation timestamp matching the committed row visible on a separate connection. The stored Argon2 hash verified the NFC-normalized password. |
| Duplicate handling | Normal sequential duplication and a forced precheck miss both returned the approved 409 response. The latter exercised a real PostgreSQL unique-constraint error without simultaneous requests. Exactly one synthetic account remained before cleanup. |
| Validation and redaction | Tests passed for missing/empty fields, malformed JSON/UTF-8, wrong types, invalid email, Unicode/length/matching failures, and unknown error metadata. Responses contain only safe locations/types and fixed messages. |
| Availability and unexpected failures | Tests confirmed generic 503 availability/timeout responses and generic 500 responses for query, hashing, dependency, and response-model failures. Credential/hash/SQL/driver markers embedded in exceptions were absent from responses and captured logs. No raw exceptions escaped the registration boundary. |
| Transaction rollback and retry | A native test inserted a synthetic row and then raised a simulated availability failure. The endpoint returned 503 after rollback, the row was absent, and a subsequent request succeeded with 201. |
| No sessions or cookies | The native success test found zero sessions for the created user. API response tests found no session cookie; the endpoint generates no token. |
| Database guards and cleanup | Existing settings and once-per-connection guards covered API-handler and cleanup connections. Per-test finalizers deleted only exact reserved synthetic accounts and verified absence. All native teardowns passed. |
| Existing health endpoints | Database-free liveness/failure/retry cases and the native database-health case passed with the registration router installed. |

Both final pytest runs emitted the existing Starlette/AnyIO deprecation warning.
No schema, frontend, dependency, or private environment file changes were made
in Step 3. Native writes remained limited to synthetic users in
`garageguide_app_test`; no other database was written or initialized.

### Commands executed for Step 3

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider
```

With `RUN_DB_TESTS=1` temporarily set, without overriding `PGDATABASE`, then
restoring the previous `RUN_DB_TESTS` value:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider --maxfail=1
```

## Build Step 4 results

Observed November 4, 2026. Frontend runtime: existing fnm Node 22.23.4 and npm
10.9.9; Vite 6.4.5. Python/pytest runtime is unchanged.

| Check | Observed result |
| --- | --- |
| Frontend dependency | Added exact `react-router-dom` 7.18.5. The lockfile adds `react-router-dom`, `react-router`, `cookie`, and `set-cookie-parser`; comparison with the previous lockfile found no existing package version changes. No additional direct dependency was added. |
| Frontend lint | `npm --prefix frontend run lint` passed. |
| Production build | `npm --prefix frontend run build` passed: 43 modules transformed. The initial sandboxed attempt could not resolve parent directories due to access restrictions; the approved retry outside the sandbox passed. |
| Complete database-free backend gate | Final run: 121 passed, 12 integration cases deselected, 1 existing Starlette/AnyIO warning; 3.74 seconds. Includes 8 new launcher safety/cleanup tests. |
| Guarded native backend regression gate | 12 passed, 121 database-free cases deselected, 1 existing Starlette/AnyIO warning; 4.40 seconds. Settings and once-per-connection guards remained active. All exact synthetic-fixture cleanup teardowns passed. `RUN_DB_TESTS` was restored afterward. |
| API-helper smoke checks | 15 passed using Node and mocked fetch only: exact public success shape, sanitized validation, duplicate/unavailable/unexpected responses, malformed JSON, network failure, actual 10-second timeout, one POST per call, and cancellation. This was a one-off check, not a new frontend runner or browser evidence. No HTTP/database request was sent by these smoke checks. |
| Manual backend launcher | Eight database-free tests passed for explicit opt-in, unsafe settings rejection, reserved-email restriction, setup-failure cleanup, restoration of patched functions, mocked server invocation, and no success marker on cleanup failure. The agent did not start the manual server. The user's subsequent manual run reported the verified-cleanup marker below. |
| Browser checks | **Passed, user-reported November 4, 2026**, in Google Chrome 156.0.8078.73, covering development and production preview. Detailed observations and cleanup confirmation are recorded below; these were not automated or agent-performed browser checks. |

The code mounts BrowserRouter once, defines only `/` and `/register`, uses Link
navigation, and adds labeled registration fields, field errors/focus feedback,
announcements, and pending/repeat-submit protection. The helper makes one
relative POST, bounds the request/JSON processing with a 10-second timer, and
does not automatically retry. Only fixed safe messages reach the UI. Passwords
are held in local component state, cleared on success/non-correctable failures,
and discarded on unmount/document departure. The user subsequently confirmed
password retention after correctable failures and clearing after success and
navigation during the manual browser checks below.
No sign-in, sessions, cookies, protected routes, or storage was added.

Step 4 native regression writes were limited to unique synthetic users in
`garageguide_app_test`; no development database writes, schema changes, private
environment edits, commits, merges, or pushes were performed. See the exact
guarded manual launch, synthetic emails, dev/preview checks, failure simulations,
and cleanup acceptance marker in [the browser guide](BROWSER_CHECKS.md).

### Commands executed for Step 4

Using the existing fnm Node installation on this process's PATH:

```powershell
npm --prefix frontend install --save-exact react-router-dom --no-audit --no-fund
npm --prefix frontend run lint
npm --prefix frontend run build
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_manual_registration_server.py -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider
```

The complete guarded native command from Step 3 was repeated with temporary
`RUN_DB_TESTS=1` and `--maxfail=1`, without overriding `PGDATABASE`. The one-off
Node mocked-transport check also ran without browser/database connections.

### User-performed Step 4 browser verification

**Date:** November 4, 2026. **Browser:** Google Chrome 156.0.8078.73.
**Environments:** development and production preview.
**Evidence source:** the user's reported observations; no browser checks were
rerun by the agent while recording these results.

| Check | User-observed result |
| --- | --- |
| Development routing | Passed direct loads, refresh, links, and Back/Forward. |
| Existing connection screen | Connection check and retry behavior passed. |
| Registration form | Validation, field-error clearing, focus behavior, and keyboard operation passed. |
| Real registration | Returned HTTP 201 and displayed the success message. |
| Normalized duplicate email | Reusing the normalized email returned the expected HTTP 409 message. |
| Pending submission | Prevented duplicate requests. |
| Simulated failures | Network, timeout, 503, 500, and malformed-response simulations displayed safe feedback. These are simulated UI results, separate from the real 201/409 observations. |
| Password retention | Passed after correctable failures. |
| Password clearing | Passed after success and navigation. |
| Responsive layouts | Passed at widths of 375, 768, and 1440 pixels without horizontal scrolling. |
| Development and preview | Both sets of checks passed. |
| Exact fixture cleanup | The final backend message was `Verified cleanup: all reserved synthetic accounts are absent.` |

**Step 4 status:** complete and subsequently approved by the user, with automated
results and user-performed browser evidence recorded separately.
Recording this report made no application changes, database connections, commits,
merges, or pushes.

## Build Step 5 final verification

Observed November 4, 2026 using the existing Python 3.13.17, pytest 8.3.5,
fnm Node 22.23.4, npm 10.9.9, and Vite 6.4.5. No dependencies were installed or
upgraded in Step 5. No application behavior changed. Only documentation was
updated; the earlier user-performed browser results above remain a distinct
evidence source and were not rerun by the agent.

| Check | Actual Step 5 result |
| --- | --- |
| Complete database-free backend suite | **121 passed, 12 deselected**, 1 existing Starlette/AnyIO deprecation warning, 3.50 seconds. No native database connection was required. |
| Guarded native PostgreSQL suite | **12 passed, 121 deselected**, 1 existing Starlette/AnyIO warning, 4.58 seconds. Includes 7 registration API cases, 4 query/transaction cases, and 1 native read-only health case. No skips or failures. |
| Exact synthetic-record cleanup | **Passed in all native teardowns.** Fixtures reserve unique, initially absent synthetic emails, register cleanup before writes, recover IDs by exact reserved email, delete only exact ID/email pairs, commit, and independently query those reserved emails to verify absence. A cleanup failure would fail the run and stop further native testing. |
| Database safeguards | Test settings rejected other database names before connection. `SELECT current_database()` ran once as the first statement on each new physical native connection, including API-handler and cleanup connections; the required result was `garageguide_app_test`. No `PGDATABASE` override was introduced. The prior `RUN_DB_TESTS` value was restored after the native command. |
| Transaction/native behavior | Successful responses matched committed rows visible on separate connections; normal and forced-constraint duplicate paths, rollback/retry, hash verification, and session-free behavior passed. Native health remained read-only. |
| Python dependencies | `pip check`: **No broken requirements found.** |
| Frontend lint | **Passed**, ESLint exit 0. |
| Frontend production build | **Passed**, 43 modules; JS 234.62 kB (gzip 75.56 kB), CSS 2.46 kB (gzip 1.05 kB). The first attempt hit sandbox access denial reading parent directories/configuration; the approved retry outside the sandbox passed. |
| Whitespace | `git diff --check` and a separate check covering untracked feature files passed. Git's LF-to-CRLF notices are line-ending warnings, not whitespace failures. |
| Git status and builder diff review | Reviewed all 30 paths below: 14 modified tracked files, 16 untracked files, zero staged files. Branch `feature/register-a-user-account`; no feature commit, merge, push, or archive was created. No schema or private environment file changed. |
| Independent audit | **Not performed: Phase A checkpoint precondition failed.** No reviewer findings, resolutions, request, or receipt exists; this is not a passing independent audit. See the blocker below. |

The 133 collected backend cases are partitioned into 121 database-free and 12
native cases. The deselected counts reflect that partition, not missing tests.
Database-free breakdown: 33 schemas, 20 security, 31 registration API, 23 database
access/guards/cleanup, 8 manual-launcher safety, and 6 existing health/settings
cases. The existing Starlette/AnyIO deprecation warning does not fail either run.

### Commands executed for Step 5

From the repository root, using the existing fnm Node on this process's PATH:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pip check
npm --prefix frontend run lint
npm --prefix frontend run build
git diff --check
git status --short
git diff --stat
git diff --name-status
git ls-files --others --exclude-standard
git rev-parse HEAD
git merge-base main HEAD
```

The native command was run with explicit opt-in and restoration of the flag:

```powershell
$previousRunDbTests = $env:RUN_DB_TESTS
try {
  $env:RUN_DB_TESTS = '1'
  backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider --maxfail=1
} finally {
  if ($null -eq $previousRunDbTests) {
    Remove-Item Env:RUN_DB_TESTS -ErrorAction SilentlyContinue
  } else {
    $env:RUN_DB_TESTS = $previousRunDbTests
  }
}
```

No additional database scan or prefix-based deletion was used as cleanup proof.
Native fixture teardown actually checked exact reserved-email absence after
deletion; the passing native run includes those checks. The separate manual
cleanup marker above remains user-reported browser-run evidence. Identity
sequences may advance and were not reset. No writes to `garageguide_app`,
`postgres`, or another database, schema changes, or initialization were performed.

### Diff review and independent-audit blocker

Builder review covered the feature's schema/credential helpers, exception
boundary, parameterized queries and transaction ownership, test guards/cleanup,
React form/routing, timeout/response handling, dependency delta, and documentation.
No confirmed application defect was identified during this self-review. Stale
browser-pending wording in README and the browser guide was aligned with the
user's report; these are documentation corrections, not application changes.
No browser checks need repetition because of Step 5 changes. Any future code
repair must identify its affected browser checks before reusing older evidence.

The requested `$audit independent current` was invoked for preflight only.
Installed [Audit](../../.agents/skills/audit/SKILL.md), Phase A, requires:
"The current full `HEAD` must be the approved application-code checkpoint."
Its [independent-review contract](../../.agents/skills/audit/reference/independent-review.md)
also requires a verified spec, a reliable non-equal base/target, and no differing
paths except the findings/review ledgers.

Current HEAD and the local `main` merge base are both
`bd763da52ba52c07f3fad3200cccade663dbe756`, the pre-feature baseline. All 30
candidate paths below are uncommitted. The user explicitly prohibited commits,
so the builder did not stage files, create a checkpoint, prepare a misleading
request, spawn a reviewer, or write a passing receipt. `review.md` and
`findings.md` retain their existing stubs. Independent findings and resolutions
are **unavailable**, not "none found by independent review". The configured
execution remains automatic, subject to its fresh-context/identity requirements
after checkpoint approval. At that preflight, Step 5 was unchecked and the spec
was not `verified`. The user subsequently approved one local review checkpoint;
the implementation checks are now marked complete/verified for Phase A, while
independent acceptance remains pending. This is not an audit pass or permission
to run `$complete`.

### Exact proposed checkpoint candidate / file purposes

This is a reviewable candidate only; nothing has been staged or committed.
`M` means modified tracked file; `??` means untracked file. Dependency directories,
build output, caches, private environments, and ignored activity are excluded.

| Git state | File | Purpose |
| --- | --- | --- |
| M | `README.md` | Describe registration, routes, safe errors, test guards, and current evidence. |
| M | `backend/app/database.py` | Shared bounded read-only/writable psycopg connection setup; preserve health behavior. |
| M | `backend/app/main.py` | Register the auth router beside the existing health router. |
| M | `backend/requirements.txt` | Declare pinned Pydantic, email-validator, and pwdlib Argon2 requirements. |
| M | `backend/tests/conftest.py` | Database-free connection prohibition and guarded native fixtures/finalizers. |
| M | `blueprint/context/coding-standards.md` | Align synthetic writes and once-per-connection guard/cleanup policy. |
| M | `blueprint/context/current-feature.md` | Approved Feature 1 contract, step progress, evidence, and review blocker. |
| M | `docs/verification/BROWSER_CHECKS.md` | Repeatable guarded manual browser procedure and user-evidence pointer. |
| M | `frontend/package-lock.json` | Lock the router and its transitive packages without unrelated upgrades. |
| M | `frontend/package.json` | Add only the approved react-router-dom direct dependency. |
| M | `frontend/src/App.jsx` | Preserve connection page and define `/`/`/register` with Link navigation. |
| M | `frontend/src/api.js` | Safe registration POST result handling, cancellation, 10-second bound, no retry. |
| M | `frontend/src/main.jsx` | Mount BrowserRouter once. |
| M | `frontend/src/styles.css` | Responsive form/navigation and accessible field/status styling. |
| ?? | `backend/app/routes/auth.py` | Synchronous registration and sanitized 201/422/409/503/500 boundary. |
| ?? | `backend/app/schemas.py` | SecretStr request fields, shared email normalization, and public response. |
| ?? | `backend/app/security.py` | Sole secret-unwrapping helper, NFC validation/matching, and Argon2 hashing. |
| ?? | `backend/app/user_queries.py` | Bound SELECT/INSERT queries, transaction completion, and duplicate translation. |
| ?? | `backend/tests/database_support.py` | Per-connection actual-name guard, fixture reservation, exact cleanup/verification. |
| ?? | `backend/tests/manual_registration_server.py` | Guarded synthetic-account-only browser backend and shutdown cleanup. |
| ?? | `backend/tests/registration_support.py` | Synthetic request/hash/redaction helpers that suppress sensitive failure output. |
| ?? | `backend/tests/test_database_access.py` | Query binding, transaction, guard, and cleanup unit coverage. |
| ?? | `backend/tests/test_manual_registration_server.py` | Manual launcher opt-in, restriction, restoration, and cleanup safety tests. |
| ?? | `backend/tests/test_registration.py` | Database-free API success, validation, redaction, and failure tests. |
| ?? | `backend/tests/test_registration_integration.py` | Guarded native HTTP persistence, duplication, rollback/retry, and redaction. |
| ?? | `backend/tests/test_schemas.py` | Email processing, SecretStr masking/types, and public response validation. |
| ?? | `backend/tests/test_security.py` | Unicode/password boundaries, matching, Argon2, and safe representations. |
| ?? | `backend/tests/test_user_queries_integration.py` | Native commit visibility, duplicate/rollback recovery, cleanup, and read-only checks. |
| ?? | `docs/verification/REGISTRATION_STATUS.md` | Separate automated, PostgreSQL, user-browser evidence and final review status. |
| ?? | `frontend/src/Register.jsx` | Accessible registration page and transient password/request lifecycle. |

**Proposed commit message:** `feat: add user account registration`.
The user subsequently approved exactly this one local review checkpoint and
message, solely to enable independent audit. The spec's verified implementation
status prepares Phase A; independent acceptance remains pending. No audit fixes,
second commit, archival, merge, push, deployment, or `$complete` is approved.

### Remaining limitations

- The mandatory independent review has not yet run; no passing receipt exists.
  One local checkpoint is now approved to enable it. `$complete` remains blocked
  pending independent acceptance and separate user approval.
- Browser evidence is the user's November 4, 2026 Chrome report, not an automated
  run. No additional browsers or assistive-technology-specific results were
  supplied; do not infer those checks from lint/build or general keyboard results.
- Real simultaneous requests remain optional hardening. Unique-constraint race
  translation has unit and forced-precheck-miss native coverage.
- No frontend unit/browser runner, combined Verify command, CI, fresh dependency
  vulnerability scan, production deployment/rewrites, load test, or pooling was
  introduced. `pip check` checks compatibility, not current vulnerability status.
- Registration creates accounts only. Sign-in/out, tokens, cookies, expiry,
  revocation, owner authorization, and authenticated CSRF decisions remain Feature 2.

## Remaining verification

- Step 4: complete and approved.
- Step 5: implementation checks passed and are marked verified for the approved
  checkpoint; independent audit and final Step 5 acceptance remain pending.
- A real simultaneous-request test remains optional hardening; unit tests cover
  translation of the database's email unique violation after rollback.

See the [active specification](../../blueprint/context/current-feature.md) for
step acceptance and the [browser guide](BROWSER_CHECKS.md) for manual checks.
Existing scaffold and historical SQL records remain separate and unchanged;
these results do not replace or relabel their evidence.
