# Authentication verification status

Feature 2: Sign in, sign out, and protect private sessions.

Current checkpoint: the original implementation was committed as
`fefa4b242047a0a18c02228963db3344ef2ce4fa`. Its independent audit requested
changes for F-01 and F-02. The approved frontend repairs passed automated checks
and separate user-performed focused browser verification in development and
production preview. The active spec is verified for a proposed repair checkpoint.
Both P1 findings are builder-marked fixed pending fresh independent review,
not reviewer-closed. The original changes-requested receipt is preserved and is
stale for the repairs. Nothing from the repair is staged or committed; explicit
checkpoint approval and a new passing `$audit independent current` receipt remain
required. Historical sections below retain their original evidence boundaries;
the repair follow-up at the end is the current status. No `$complete` has run.

## Build Step 1 — November 6, 2026

Implemented credential, response, token, configuration, and cookie/CSRF policy
foundations. Step 1 was subsequently approved before Step 2. No authentication endpoint,
session SQL, frontend page, or CSRF enforcement on existing routes is added yet.

Branch: `feature/sign-in-sign-out-and-protect-private-sessions`.
No commit created. Existing local workflow notes and private environment files
were preserved. Only tracked environment examples received new auth keys.

### Automated database-free evidence

Python 3.13.17; pytest 8.3.5. Commands run from the repository root:

| Check | Actual result |
| --- | --- |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_auth_security.py backend/tests/test_auth_contracts.py backend/tests/test_auth_settings.py backend/tests/test_auth_policy.py -p no:cacheprovider` | 121 passed; one existing dependency deprecation warning. |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider` | 242 passed, 12 integration tests deselected; one existing dependency deprecation warning. |
| `backend/.venv/Scripts/python.exe -m pip check` | No broken requirements found. |
| `git diff --check` | Passed; Git reported expected LF-to-CRLF notices. |

New test totals: 25 security, 20 schema/contract, 44 configuration, and 32
request/cookie-policy cases. Existing 121 database-free cases also passed,
including registration and health regressions. The dependency warning concerns
Starlette's deprecated AnyIO BlockingPortal alias; no dependency was changed.

Coverage includes shared trim/EmailStr/lowercase email processing, NFC password
normalization and length/Unicode rules, masked SecretStr representations,
Argon2 verification, exactly one verification for known/unknown accounts,
once-per-process dummy-hash initialization, opaque token format/SHA-256 hashing,
public response fields, explicit fail-closed auth configuration, origin/JSON/
custom-header validation, loopback serving checks independent of Host headers,
and matching session-cookie issuance/deletion attributes.

### Native PostgreSQL evidence

Not run. Step 1 opened no PostgreSQL connection and made no database writes.
The 12 existing integration tests were deselected, not counted as passes.
There are no Step 1 synthetic records or cleanup claims.

### Browser evidence

Not run: Step 1 adds backend foundations without a new observable browser flow.
Feature 1 browser evidence remains in REGISTRATION_STATUS.md and BROWSER_CHECKS.md;
it does not verify Feature 2 or the future registration CSRF changes.

### Remaining verification and limitations at Step 1

- Steps 2–5 remain unchecked; transaction/lifecycle, native session cleanup,
  endpoints, error translation, no-store responses, frontend, and independent
  review require their later approved steps.
- Cookie/CSRF helpers are deliberately not enforced on registration until Step 3
  updates its frontend and test callers in the same change.
- Invalid auth settings raise a fixed configuration error. Step 3 will translate
  that error to the approved safe unavailable response at the API boundary.
- Pydantic still exposes raw input through its structured validation-error API.
  Step 3 must retain/extend response sanitization; SecretStr alone is insufficient.
- Private environment files were not edited. Before later auth runtime checks,
  explicitly configure the approved auth keys using the corresponding example.
- Unit cookie-header checks do not prove browser delivery or deployed HTTPS.
- Login rate limiting remains an explicitly deferred production-security decision;
  no in-memory limiter, schema changes, or new dependencies were added.

## Build Step 2 — November 6, 2026

Implemented parameterized credential lookup and focused session transactions.
Step 2 was subsequently approved before Step 3. No login/session/logout HTTP endpoints,
registration CSRF enforcement, or frontend changes were introduced.

### Changed files in this step

| File | Purpose |
| --- | --- |
| `backend/app/user_queries.py` | Read-only normalized-email credential lookup, verification after closing the read connection, and public-only identity result. Existing registration functions are unchanged. |
| `backend/app/session_queries.py` | Session insertion/replacement, user-scoped housekeeping, atomic validation/extension, revocation, and typed internal/public results. |
| `backend/tests/database_support.py` | Read-only session schema prechecks, exact user/session ownership tracking, recovery, deletion, and independent cleanup verification. |
| `backend/tests/conftest.py` | Report successful exact cleanup without exposing account credentials, tokens, or hashes; preserve finalizer registration before writes. |
| `backend/tests/test_database_access.py` | Extend the existing cleanup expectations to include session absence and recorded cleanup counts. |
| `backend/tests/test_session_queries.py` | 20 database-free credential/query/transaction tests. |
| `backend/tests/test_session_fixture_safety.py` | Six database-free fixture ownership, recovery, schema, and cleanup-failure tests. |
| `backend/tests/test_session_queries_integration.py` | 18 native credential/session/lifecycle/rollback/lock-coordination/cleanup tests. |
| `blueprint/context/current-feature.md` | Check Step 2 only and record the next approval boundary. |
| `docs/verification/AUTHENTICATION_STATUS.md` | Record this checkpoint's actual evidence and remaining limitations. |

### SQL and transaction behavior

All variable values use psycopg parameters. Fixed SQL interval constants express
the approved lifetimes. No ORM, generic repository, migration, pooling, or schema
creation is involved. Existing connection and statement timeouts remain unchanged.

| Operation | Behavior |
| --- | --- |
| Credential SELECT | Bound normalized email; fetch public fields and stored password hash inside the verification boundary. Close the read-only transaction before the single real/dummy Argon2 verification. Return only the public user or no match. |
| Session lock | SELECT the row ID by bound SHA-256 token hash with FOR UPDATE. Raw tokens never enter SQL. |
| Time sample | SELECT clock_timestamp() after the row lock returns. Transaction/locking-statement start time cannot bypass expiration after waiting. |
| Session extension | UPDATE only the locked ID with revoked_at IS NULL and strict checks against idle and absolute deadlines; return database user ID and new deadline. Read public identity by that database user ID. |
| Current-browser replacement | Lock/recheck the presented session and revoke that one valid session inside the new session transaction, including account switching. Other active browser/device sessions remain valid. |
| Invalid-session housekeeping | DELETE only rows belonging to the newly authenticated user that are revoked, idle-expired, or absolute-expired. Another user's invalid rows remain untouched. |
| New session INSERT | One PostgreSQL clock sample supplies created_at and initial expires_at = created_at + 30 minutes. Bind the newly generated token's lowercase SHA-256 hash and trusted user ID. |
| Logout foundation | Lock the cookie-identified session and set revoked_at only when still null. Missing/unknown sessions and repetition are safe; no user-wide revocation. |

For PostgreSQL time N, validation requires revoked_at IS NULL,
N < expires_at, and N < created_at + eight hours. Equality is expired.
Valid activity sets expires_at to LEAST(N + 30 minutes, created_at + eight hours)
without changing created_at or clearing revoked_at. SQL retains all validity
predicates while the transaction holds the row lock.

Each public session operation owns its connection context and short transaction.
Success commits and closes before returning trusted identity or an issued session.
Failure rolls back and closes before reaching callers; driver failures remain
untranslated here for Step 3's safe API boundary. Session response validation and
serialization occur before commit. The creation callback allows Step 3 to prepare
the HTTP body/cookie before commit, without sending them. Callback failure rolls
back revocation, housekeeping, and insertion together, preserving the old session.
Argon2 credential verification occurs before callers open the creation transaction.

### Automated database-free evidence

Python 3.13.17; pytest 8.3.5. Commands run from the repository root:

| Check | Actual result |
| --- | --- |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_session_queries.py backend/tests/test_session_fixture_safety.py backend/tests/test_database_access.py -p no:cacheprovider` | 49 passed: 20 new query/transaction cases, six new fixture cases, and 23 existing database-access cases. |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider` | 268 passed; 30 integration cases deselected. |
| `backend/.venv/Scripts/python.exe -m pip check` | No broken requirements found. |
| `git diff --check` plus whitespace inspection of new files | Passed; only expected LF-to-CRLF notices. |

Each pytest run reported the existing Starlette/AnyIO BlockingPortal deprecation
warning. No dependency was installed, upgraded, or edited.

### Native PostgreSQL and exact cleanup evidence

Both native commands used RUN_DB_TESTS=1, loaded only backend/.env.test, and ran
through the settings-level garageguide_app_test guard. Every newly opened native
connection first executed SELECT current_database() once and required exactly
garageguide_app_test before exposure. This includes read, write, lock-worker,
housekeeping, fixture, and cleanup connections. No other database was written.

| Command | Actual result |
| --- | --- |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_session_queries_integration.py -m integration -p no:cacheprovider --capture=tee-sys` | 18 passed. |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration --ignore=backend/tests/test_session_queries_integration.py -p no:cacheprovider --capture=tee-sys` | 12 existing native registration/user-query/health cases passed; 268 database-free cases deselected. |

Total native evidence: 30 passing cases across the two complementary runs.
The existing session schema and constraints passed read-only prechecks; no DDL
or initialization was run.

Native coverage demonstrated real Argon2 credential verification, committed
hash-only session storage, PostgreSQL timestamps, independent devices,
current-browser account switching, user-scoped invalid cleanup, unchanged old
sessions after rollback, both expiry boundaries/cap, idempotent revocation,
and successful extension visible through a separate connection.

Seven deterministic lifecycle cases use a fixed PostgreSQL-generated instant
to check just-before/equal/after idle and absolute expiry, plus revocation.
Separate tests exercise the actual unfrozen PostgreSQL clock. The two concurrent
tests hold a row lock, confirm the extension worker is blocked using
pg_blocking_pids, then commit revocation or set expiry after the worker started.
The waiting worker rejects authentication; the expired/revoked row is not revived.
Polling and waits are bounded and observe database lock state, rather than relying
solely on sleeping to create a race.

Cleanup finalizers were registered before writes. Fixtures reserved unique,
initially absent emails, verified exact user/session ownership, and tracked
session IDs and hashes. Cleanup recovered committed sessions even when a simulated
lost response prevented tracking, using only those fixture-owned user IDs.
It deleted sessions by exact ID + user ID + token hash, and users by exact ID +
reserved email. After commit, a separate guarded read-only connection verified
absence of reserved users and tracked/owned sessions. No prefix deletion,
truncation, reset, or unrelated-record cleanup occurred.

All 18 new native tests completed verified exact cleanup. Existing native tests
that reserved records also reported verified cleanup; read-only health cases
created none. A dedicated lost-response test explicitly ran cleanup and confirmed
both synthetic users and the untracked committed session were absent. Cleanup
failure would fail/stop verification instead of reporting success.

### Remaining checks and limitations

- Steps 3–5 remain unchecked. No new endpoint or authentication dependency is
  wired into FastAPI; the transaction function returns the trusted context for
  that later dependency. No cookies were sent to a browser by these tests.
- Request/CSRF enforcement, API error/no-store behavior, frontend integration,
  manual test-backend restrictions for newly exposed session writes, and browser
  verification remain later work. The manual registration launcher currently
  exposes only the unchanged registration/health routes.
- No browser check, frontend lint/build, or independent audit was claimed for
  this backend-only step. Feature 1 browser evidence remains historical.
- Production HTTPS deployment and login rate limiting remain separately deferred.
- No commit, merge, push, dependency change, or schema change occurred.

## Build Step 3 — November 6, 2026

Implemented POST /api/auth/login, GET /api/auth/session, POST /api/auth/logout,
the reusable session dependency, cookie responses, CSRF enforcement, no-store
responses, and registration request compatibility. Step 3 is complete and awaits
review before Step 4 at that checkpoint. Step 3 was subsequently approved. No
React login/account/protected-route/logout UI was added during Step 3.

### Changed files in this step

| File | Purpose |
| --- | --- |
| `backend/app/routes/auth.py` | Share the safe authentication route boundary across registration and the three new endpoints. Check CSRF before body parsing; prepare successful login body/cookie before commit and return only afterward. |
| `backend/app/authentication.py` | Load validated auth settings once per request, parse cookie shape, and provide the synchronous trusted-session dependency with safe 401/503/500 handling and cookie removal only for authentication rejection. |
| `backend/app/main.py` | Preserve public health wiring and add no-store to authentication routing errors such as 404/405. |
| `frontend/src/api.js` | Keep relative URLs and the ten-second/no-retry behavior; explicitly use same-origin credentials and add the registration CSRF header. No new pages or auth state. |
| `backend/tests/conftest.py` | Give API clients an explicit valid loopback origin and validated testing AuthSettings; keep real database settings from .env.test and all native guards. |
| `backend/tests/registration_support.py` | Send approved Origin/JSON/custom headers in existing registration tests and assert no-store responses. |
| `backend/tests/database_support.py` | Add a read-only session ownership check for the guarded manual launcher before session writes. |
| `backend/tests/manual_registration_server.py` | Restrict registration, credential lookup, new-session replacement/housekeeping, extension, and revocation to reserved synthetic accounts/sessions; restore patches and verify exact cleanup. Load auth settings only from the test configuration. |
| `backend/tests/test_manual_registration_server.py` | Supply explicit valid auth settings and add four login/session ownership/restoration tests. |
| `backend/tests/test_session_fixture_safety.py` | Add two tests proving the manual session guard rejects another account without writes and handles missing/unknown cookies safely. |
| `backend/tests/authentication_support.py` | Reusable synthetic HTTP inputs, header cases, cookie handling, and redaction assertions without printing credentials or cookie values. |
| `backend/tests/test_authentication_api.py` | 86 database-free API contract, CSRF, cookie, dependency, failure, transaction-boundary, and cache tests. |
| `backend/tests/test_authentication_api_integration.py` | 57 guarded native API cases for real login/session/logout, rollback, identity/device isolation, and CSRF rejection without writes. |
| `README.md` | Document implemented APIs, explicit auth configuration, CSRF/cookie/session behavior, and remaining UI work. |
| `docs/verification/BROWSER_CHECKS.md` | Identify the registration checks that must be repeated after CSRF enforcement and document the expanded safe manual launcher/cleanup marker. No new browser pass recorded. |
| `blueprint/context/current-feature.md` | Check Step 3 only and stop before Step 4. |
| `docs/verification/AUTHENTICATION_STATUS.md` | Record this checkpoint's actual evidence and limits. |

### Request, transaction, cookie, and failure behavior

The authentication route boundary loads validated settings in a worker thread,
preserves the application's settings-provider override for tests, and caches the
result only in request state. Before parsing a mutation body it requires one
exact trusted Origin, JSON Content-Type, and X-GarageGuide-CSRF: 1. Bad/missing/
null/malformed/untrusted origins, missing/wrong markers, form/simple types, and
duplicate policy headers produce the fixed 403 without business operations or
cookie changes. GET session does not require mutation headers. No CORS was added.

Login validates LoginRequest's shared email process and SecretStr/NFC password
rules. The existing credential boundary closes its read connection and performs
one real/dummy Argon2 verification. Wrong password and unknown email return the
same fixed 401 and leave an old session/cookie untouched. Valid credentials call
the unchanged Step 2 transaction. Its callback constructs the public JSON and
cookie headers before commit; the route returns that prepared response only after
the transaction commits and closes. Failed preparation or commit sends no cookie.

GET session uses require_authenticated_session, which parses cookie shape before
hashing/querying and calls the unchanged atomic lock/time/extension transaction.
The returned identity comes only from the validated database session; a supplied
user_id cannot select identity. Missing/malformed/unknown/expired/revoked sessions
share 401 and matching cookie deletion. Database availability failures are safe
503 responses with no cookie mutation. The dependency also returns fixed safe
HTTP errors for future protected routes; a test-only protected route demonstrates
reuse without adding a product endpoint.

Logout prepares a matching deletion header, calls current-session revocation, and
returns the empty 204 only after the owned transaction succeeds. Missing/malformed/
unknown/expired/already-revoked cookies remain idempotent outcomes after CSRF
checks. Failure discards the prepared deletion response and preserves the cookie.
Other browser/device sessions remain active, including during account switching.

Issuance uses garageguide_session, HttpOnly, SameSite=Lax, Path=/, no Domain,
and no Max-Age/Expires. Secure=false requires explicitly validated loopback
development/testing and loopback serving; production issuance/deletion uses
Secure=true. Deletion uses matching scope/flags plus expiration/Max-Age=0.
The only raw-token transport is the cookie; JSON contains public user/expiry only.

All authentication responses, including registration, errors, and auth 404/405,
use Cache-Control: no-store. Registration retains its approved 201/422/409/503/
500 contracts behind the new 403 gate. Validation responses contain only fixed
safe loc/msg/type fields. Expected driver availability/timeout failures become
503; unexpected failures become generic 500. Application logs use fixed messages
without exception objects, bodies, passwords, hashes, tokens, or cookies. Both
health endpoints remain public and their read-only behavior is unchanged.

### Automated database-free and frontend evidence

Python 3.13.17; pytest 8.3.5; fnm Node 22.23.4; Vite 6.4.5.

| Check | Actual result |
| --- | --- |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_authentication_api.py backend/tests/test_registration.py backend/tests/test_manual_registration_server.py backend/tests/test_session_fixture_safety.py backend/tests/test_health.py -m "not integration" -p no:cacheprovider` | 143 passed; one native health case deselected. |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider` | 360 passed; 87 native cases deselected. |
| `backend/.venv/Scripts/python.exe -m pip check` | No broken requirements found. |
| `npm --prefix frontend run lint` | Passed. |
| `npm --prefix frontend run build` | Passed, 43 modules transformed. Initial sandbox attempt failed on parent-directory access; the approved unrestricted retry succeeded. |
| Node stdin smoke check importing the actual api.js helper with mocked fetch | Passed: relative POST, same-origin credentials, JSON/CSRF headers, bounded AbortSignal, safe network result, and no automatic retry. This is not browser evidence or a newly installed frontend test runner. |
| `git diff --check` and whitespace inspection of new files | Passed; expected LF-to-CRLF notices only. |

The complete database-free total includes the focused cases. Each pytest run
reported the existing Starlette/AnyIO BlockingPortal deprecation warning. No
dependency or package lock file was changed and no dependency was installed.

### Native PostgreSQL API and exact cleanup evidence

With RUN_DB_TESTS=1:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_authentication_api_integration.py backend/tests/test_registration_integration.py backend/tests/test_health.py -m integration -p no:cacheprovider --capture=tee-sys
```

Actual result: 65 passed, six database-free health cases deselected. This is
57 new authentication API cases, seven existing registration API cases, and
one existing read-only native health case. The other 22 native query/lifecycle
cases retain their Step 2 evidence and were not rerun in this Step 3 command;
the final Step 5 gate will run the complete native suite.

API clients used explicit validated testing/loopback auth settings; this does
not assert that a user's private AUTH_* entries have been populated. Database
settings came only from backend/.env.test, with the effective-name guard. Every
new physical connection checked SELECT current_database() once before exposure
and required garageguide_app_test. No garageguide_app/postgres/other DB writes,
schema initialization, or schema changes occurred.

Observed native API cases include committed public login, cookie restoration,
committed idle extension, generic credential failures preserving an old session,
all five unusable-session states, current-browser account switching, independent
devices/two-account identity isolation, logout/repetition, and 39 CSRF rejection
cases across registration/login/logout. An additional bad-CSRF logout case
preserved an existing session. Native failure injections after revocation/cleanup,
extension, or revocation updates proved rollback before 503 with cookie retention
and recovery afterward. A malformed stored credential hash produced a safe 500.

Existing registration cases passed committed 201, normal duplicate 409, forced
unique-constraint duplicate 409 with rollback, safe invalid input, failed-write
rollback/503, and retry. Their shared helper now also checks no-store and no
registration cookie/session creation.

All reserved accounts and their sessions received exact verified cleanup.
Finalizers were registered before writes; identities were unique and initially
absent. Cleanup recovered any untracked committed sessions by fixture-owned user
ID, deleted only exact session ID/user ID/hash and user ID/reserved email pairs,
committed, and checked absence on a separate guarded read-only connection.
CSRF-denial cases verified no matching account/session was created and then
verified their reservation remained absent. Read-only health created no fixtures.
No broad deletion/reset or cleanup claim for unrelated records was used.

### Remaining limits and next review boundary

- Step 4 UI and Step 5 final verification/independent audit remain unchecked.
  No login/account page, protected React route, session provider, or logout
  interface was implemented. Only registration's existing request helper changed.
- No dev server or browser was started. Native TestClient and mocked-fetch
  results do not prove browser behavior or deployed HTTPS. Repeat the affected
  registration checks in development and preview using BROWSER_CHECKS.md.
  Preserve the user's November 4 Feature 1 browser evidence as historical.
- Existing private environment files were not edited. Runtime auth/registration
  now requires explicit AUTH_* configuration from the appropriate example. The
  manual test launcher loads test auth configuration and fails closed if absent.
- Login rate limiting and deployed HTTPS verification remain separate later
  production-security/deployment decisions. No in-memory limiter was introduced.
- Nothing was staged or committed; no merge, push, schema change, or dependency
  installation occurred. Await approval before Build Step 4.

## Build Step 4 — November 6, 2026 — complete, awaiting final approval

The approved React interface is implemented. Automated checks below passed.
The user subsequently completed manual browser verification on November 6,
2026 in Google Chrome 156.0.8078.73, in development and production preview,
and reported the exact successful account/session cleanup marker. Step 4 is
checked complete in current-feature.md and awaits final user approval.
The agent did not perform browser automation, inspect private runtime config,
or rerun tests for this documentation update. Step 5 and independent audit
were not started.

### Changed files in this step

| File | Purpose |
| --- | --- |
| `frontend/src/App.jsx` | Preserve public connection/registration routes, add login and protected account routes/links, and wrap them in the session provider inside the existing BrowserRouter. |
| `frontend/src/api.js` | Add bounded, cancellable relative login/session/logout requests; same-origin credentials; JSON/CSRF mutations; safe public-response and error classification. Existing registration request behavior remains intact. |
| `frontend/src/credentialValidation.js` | Share the existing NFC/code-point password rules and email-presence validation between login and registration. No password trimming/lowercasing/composition rules. |
| `frontend/src/Register.jsx` | Import the extracted validation function; retain its existing submission, transient password, clearing, navigation, and feedback behavior. |
| `frontend/src/sessionState.js` | Feature-specific in-memory session state, cancellation/stale-response protection, restoration, mutation deduplication, visibility gating, and guest/unavailable distinction. No token or credential state. |
| `frontend/src/useSession.js` | Shared React context and consumer hook. Separate exports keep React refresh lint clean. |
| `frontend/src/SessionContext.jsx` | Connect the session store to React, route entry, visibility/document lifecycle, and a one-shot known-expiry recheck. No periodic keepalive. |
| `frontend/src/RequireSession.jsx` | Gate private rendering until this navigation has a successful session check; show loading/unavailable/retry or redirect guests with no authentication data in router state/URLs. |
| `frontend/src/Login.jsx` | Accessible labeled sign-in fields, focus/errors/live feedback, submission lock, and temporary password lifecycle. Success navigates to account. |
| `frontend/src/Account.jsx` | Display only public email/deadline and current-browser sign-out; show unconfirmed-logout retry feedback without claiming logout on failure. |
| `frontend/src/styles.css` | Reuse the existing responsive form panel styling for session/loading/account panels. |
| `frontend/tests/api.test.js` | 47 built-in Node checks for request contracts, safe response whitelists, cancellation/timeouts, no retry, and registration regressions. |
| `frontend/tests/credentialValidation.test.js` | 15 shared Unicode/NFC/length/space/case/confirmation checks. |
| `frontend/tests/sessionState.test.js` | 23 checks for restoration, guest/unavailable, protected rechecks, mutation failures, cancellation, stale identity, visibility/departure, and expired client deadlines. |
| `README.md` | Document the implemented UI/session flow and exact built-in Node check command. |
| `docs/verification/BROWSER_CHECKS.md` | Document safe config values, exact PowerShell launch/cleanup, fresh synthetic fixtures, real/simulated browser scenarios and separate evidence; the user's observed outcomes are recorded below. |
| `blueprint/context/current-feature.md` | Mark Step 4 complete from existing automated results and the user-performed browser report; leave Step 5 unchecked. |
| `docs/verification/AUTHENTICATION_STATUS.md` | Record automated, native and user-performed browser evidence separately, with their limits. |

### Frontend/session behavior reviewed in source and logic checks

The existing BrowserRouter remains mounted once in main.jsx. Public `/` and
`/register` remain, `/login` is added, and `/account` is behind RequireSession.
GET session runs on startup and before private content can display on a new
navigation. A route key ties validation to that navigation; visibility/document
return invalidates stale validation. Pending/cancelled/late work cannot replace
identity after navigation, sign-out, or a newer request. A single timeout at the
known expiry boundary requests revalidation; there is no interval keepalive.

200 stores only whitelisted public user/expiry data. 401 clears private React
identity and redirects protected navigation with a fixed in-memory notice.
503/network/timeout/malformed responses mean unavailable and explicit retry,
preserving potentially valid public identity internally while gating its display.
A deadline already past on the device clock also gates as unavailable instead
of creating an immediate renewal loop. Server validation remains authoritative.

Login posts only email/password with same-origin credentials, JSON and the
public CSRF marker; the browser supplies Origin. It handles generic 401,
sanitized 422, fixed 403, 503, timeout/network, malformed and unexpected results.
Passwords remain local to form state after correctable failures; other failures,
success, navigation and document departure/return clear them. Failed login never
discards a previously valid session. Logout sends JSON {}, prevents repeats,
and clears public identity only after confirmed 204; failures show safe retry.
No authentication data is put in browser storage, URLs or router state.

API requests retain a ten-second bound including response-body consumption and
never automatically replay POST. JavaScript never reads the cookie value or
Set-Cookie. HttpOnly transport, transactions, SQL, normalization, Argon2 and
server expiration are the unchanged approved backend from Steps 1–3.

Source and Node checks support these logic claims; they do not prove actual
React focus, spoken announcements, browser cookie behavior or responsive layout.

### Automated checks actually run

Node 22.23.4; Python 3.13.17; pytest 8.3.5; Vite 6.4.5.

| Check | Actual result |
| --- | --- |
| `node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js` | 85 passed, zero failed/cancelled/skipped/todo. Uses the already installed Node runtime; no external runner/dependency was installed. |
| `npm --prefix frontend run lint` | Passed without warnings/errors. |
| `npm --prefix frontend run build` | Passed, 50 modules transformed. Used the approved unrestricted build path for the known sandbox/esbuild directory restriction. |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider` | 360 passed; 87 native cases deselected. |
| `backend/.venv/Scripts/python.exe -m pip check` | No broken requirements found. |
| `git diff --check` and whitespace review including new files | Passed; expected LF-to-CRLF notices only. |

The backend run retained the existing Starlette/AnyIO BlockingPortal deprecation
warning. These are Step 4 requested checks, not the final Step 5 verification gate.
No dependency/package-lock/schema changes were made.

### Guarded native API regressions and cleanup actually run

With RUN_DB_TESTS=1:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_authentication_api_integration.py backend/tests/test_registration_integration.py backend/tests/test_health.py -m integration -p no:cacheprovider --capture=tee-sys
```

Result: 65 passed; six database-free health cases deselected. This is the same
57 authentication, seven registration, one health API scope used at Step 3.
Backend product/test code was unchanged during Step 4. The other 22 native
query/lifecycle cases were not rerun in this step; final Step 5 remains separate.

Database settings loaded only backend/.env.test. Effective settings required
garageguide_app_test, and every new physical connection checked
SELECT current_database() once before exposure. API test clients used explicit
validated loopback auth settings, so passing native tests do not prove private
AUTH_* values are populated for a real manual server.

All created synthetic user/session identities and unused reservations received
verified exact cleanup. Finalizers existed before writes; deletion targeted
only exact fixture-owned session ID/user ID/hash and user ID/email pairs.
After commit, separate guarded read-only connections checked absence. No
garageguide_app/postgres/other database write or schema operation occurred.
Native results prove backend registration/login/session/logout behavior, not
the rendered React pages or browser-to-Vite transport.

### Configuration and manual browser boundary

Only the public backend/.env.example and backend/.env.test.example were read
to identify auth keys. Private files were neither displayed nor edited.

| Key | Local .env | Guarded .env.test |
| --- | --- | --- |
| AUTH_ENVIRONMENT | development | testing |
| AUTH_COOKIE_SECURE | false | false |
| AUTH_API_ORIGIN | http://127.0.0.1:8000 | http://127.0.0.1:8000 |
| AUTH_FRONTEND_ORIGIN | empty | empty |

The instructions require any missing keys to be added privately without
overwriting PostgreSQL credentials or changing the test database name. Browser
writes use only the guarded manual launcher and its unique fixture emails.
The full PowerShell instructions and cleanup marker remain in BROWSER_CHECKS.md.
The agent did not inspect or modify the user's private configuration.

### User-performed browser observations — November 6, 2026

Evidence source: the user's report in this conversation. Browser: Google Chrome
156.0.8078.73. The user reported development and production preview passed.
These are user-performed observations, separate from the automated Node checks,
database-free pytest checks, and native PostgreSQL API tests recorded above.

| Reported browser check | User-reported result |
| --- | --- |
| Development routing and direct refresh | Passed. |
| Guest access to /account | Denied without exposing private content. |
| Invalid login | Displayed the generic credentials error. |
| Valid login | Created a session and opened the correct account. |
| Refresh restoration | Restored the authenticated session. |
| Logout and Back/Forward | Revoked the current session and protected history navigation. |
| Repeated logout | Remained safe. |
| Two independent browser sessions | Remained isolated; logging out one did not log out the other. |
| Registration regression | Success, duplicate handling, validation and CSRF behavior passed. |
| Failure behavior | Network, timeout, 403, 503 and unexpected failure behavior passed. |
| Password lifecycle | Retention and clearing behavior passed. |
| Accessibility | Keyboard, focus, labels, errors and announcements passed. |
| Responsive layout and zoom | Passed at 375, 768 and 1440 pixels and 200% zoom. |
| Development and production preview | Passed. |
| Authentication token handling | No token appeared in JavaScript state, browser storage, URLs, response bodies or screenshots. The intended HttpOnly cookie transport is unchanged. |
| Final synthetic cleanup | The exact successful account/session cleanup message was reported. |

User-reported final backend message:

```text
Verified cleanup: all reserved synthetic accounts and sessions are absent.
```

This is the user's observed manual cleanup result; it is not a new database query
or cleanup run by the agent. Earlier native cleanup evidence remains separate.
The failure report does not individually distinguish live from simulated cases;
no additional live-outage claim is inferred. Timed 30-minute/eight-hour browser
expiration and account-switching observations were not separately reported and
are not added as browser passes. Their existing automated/native coverage retains
its original evidence classification. Deployed production HTTPS is not proved by
local production preview. The November 4 Feature 1 browser report remains historical.

Step 4 is complete and awaiting final user approval. Step 5 and its independent
audit remain unstarted. Only this status document and current-feature.md were
updated for the browser report; no application code, tests, private configuration,
database state, commits, landing, or deployment were changed.

## Build Step 5 — November 6, 2026 — verified implementation, audit pending

The user approved Step 4 and authorized final verification/checkpoint preparation.
All requested final checks below passed. No application behavior changed during
this builder pass, so no additional browser rerun is required because of a new
implementation change. This is the builder's verification and source review,
not an independent audit or approval to complete the feature.

Step 5's checklist now records completed verification/checkpoint preparation.
The passing independent review remains an explicit separate completion gate
after the user approves an immutable checkpoint. API/security/product contracts
are unchanged. The active specification is set to verified for Audit's checkpoint
precondition; no receipt is claimed. Freeze its final bytes before the checkpoint
and do not edit the spec or this evidence record after review just to update status.

### Final automated evidence

Python 3.13.17; pytest 8.3.5; Node 22.23.4; Vite 6.4.5. Commands from repository root:

| Check | Actual result |
| --- | --- |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider` | 360 passed; 87 native tests deselected. |
| `node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js` | 85 passed; zero failures, cancellations, skips or todo cases. |
| `backend/.venv/Scripts/python.exe -m pip check` | No broken requirements found. |
| `npm --prefix frontend run lint` | Passed without errors/warnings. |
| `npm --prefix frontend run build` | Passed; 50 modules transformed. Used the previously approved unrestricted build path for the known esbuild/sandbox directory restriction. |
| `git diff --check` and direct whitespace checks of all 44 candidate files | Passed, including all untracked additions; expected LF-to-CRLF notices only. |
| Git status, cached diff and ignore checks | 21 modified tracked files, 23 new untracked files; no staged paths. Private .env/.env.test ignored and untracked. |

The Python runs reported the existing Starlette/AnyIO BlockingPortal deprecation
warning. There is no combined Verify command. The existing frontend command
uses only the installed Node runtime; no dependency, runner, package-lock, CI,
or authoritative schema change was introduced.

### Final native PostgreSQL evidence and exact cleanup

The command explicitly set RUN_DB_TESTS=1 before running:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider --capture=tee-sys
```

Actual result: 87 passed, 360 database-free cases deselected; zero skipped native
cases. Counts are 57 authentication API, seven registration API, one health,
18 session-query/lifecycle/concurrency and four existing user-query cases.
Together the two backend commands covered all 447 collected backend cases.
With 85 frontend cases, 532 test cases passed across the three suites.

Native settings loaded only backend/.env.test. Effective database name had to be
garageguide_app_test before connecting. Every physical native connection ran
SELECT current_database() once as its first statement, required that exact name,
and closed on mismatch before exposure/writes. The guard covered fixture,
credential lookup, API, session-touch, housekeeping, lock-worker, cleanup and
verification connections. Existing schema/constraint inspection was read-only;
no initialization, DDL or writes to garageguide_app/postgres/another DB occurred.

Exact cleanup succeeded throughout the full run. Finalizers were registered
before writes. Unique, initially absent reserved emails establish fixture
ownership; exact user/session IDs and hashes were tracked and committed sessions
were recovered by those owned users after simulated lost responses. DELETE used
exact session ID + user ID + hash and user ID + reserved email. After commit,
separate guarded read-only connections verified absence of the reserved users
and tracked/owned sessions. Unused reservations were also verified absent.
Read-only health cases created no fixtures. Cleanup failure would fail and stop
the run; none occurred. No broad deletion, truncate, reset or unrelated cleanup.

### Builder contract and complete candidate-diff review

The builder reviewed all 44 proposed changed/untracked files, their callers and
the approved contracts, including nearby unchanged health/registration behavior.
The tracked diff and every untracked addition are included in the local review
packet under blueprint/.state/staging. Existing committed branch context was
also checked for scope. Generated/dependency/cache/private files are excluded.
No additional confirmed implementation defect was identified and no product or
test fix was made in this pass. This is not a substitute for fresh independent
review; findings.md and review.md remain their unchanged empty stubs.

| Contract reviewed | Supporting evidence |
| --- | --- |
| Password secrecy, shared email/NFC rules and validation redaction | SecretStr/schema/security tests and API tests; fixed safe messages/log records; public response whitelists. |
| Generic credentials and one Argon2 verify | Known/unknown API cases plus security call-count tests and once-per-process dummy-hash test; real native verification. No perfect end-to-end constant-time claim. |
| Token secrecy and hash-only storage | Canonical random 32-byte tokens, lowercase SHA-256 binding, masked internal token object, native hash-only storage checks; no token/hash in public JSON. |
| Fixation prevention and transaction boundaries | Fresh token insertion; presented-valid-session-only revocation; user-scoped invalid-row cleanup; pre-commit response preparation; rollback/close and commit-failure API cases. |
| Idle/absolute expiration and concurrency | Native strict before/equal/after boundaries, eight-hour cap, immutable creation, and two bounded row-lock tests confirming pg_blocking_pids before release. Time sampled after lock acquisition. |
| Multi-account/device isolation | Native account switching and independent cookie jars; database-derived identity; user-reported independent browser sessions and isolated logout. |
| Cookie attributes and 401/503 distinction | Shared matching issuance/deletion attributes, Secure production and loopback-only insecure settings, no persistent issuance lifetime; API tests for deletion on rejection and preservation on availability failure. |
| CSRF/trusted Origin and no-store | Exact trusted origins, JSON/custom marker and duplicate-header rejection before body parsing/business writes; 39 native denial cases, registration regressions, and authentication routing-error cache checks. |
| Registration and health regressions | Both duplicate paths, committed 201, sanitized 422, failed-write rollback/retry; public health and native read-only transactions. |
| Frontend stale work and protected routes | 23 state cases, 47 request-helper cases, 15 credential cases; abort/stale-result ownership, visibility/route gates, no POST replay or interval keepalive; user browser report. |
| Browser storage/URLs/logs/JSON | Source/diff inspection, safe API/log assertions, strict response fields and the user's no-token observation. JavaScript does not read cookies/Set-Cookie or use storage/router state for auth data. |
| Accessibility/responsiveness | Existing JSX labels/ARIA/focus/pending behavior and responsive styles; user's Chrome report at 375/768/1440 and 200% zoom. No new screenshots or browser automation claimed. |

Focused feature modules, shared credential rules and the session state controller
trace directly to approved requirements. No ORM, generic repository, JWT,
pooling, new dependency, login limiter, extra product page or unrelated feature
was added. No skipped/focused/placeholder tests were used to claim success;
marker exclusions separate unit and native runs and both sets were run fully.

### Browser and simulated evidence remain separate

The November 6, 2026 user-performed Chrome 156.0.8078.73 development/preview
report above remains the browser evidence, including its exact manual cleanup
marker. The agent did not start a server/browser or repeat those observations.
The user's reported keyboard/focus/labels/errors/announcements, layouts/zoom,
authentication, registration/CSRF and no-token results are preserved as reported.

Node mocked-fetch/state tests, deliberate native exception injections,
lost-response recovery and the guide's browser failure shim are simulated
evidence. Native transactions/locking/hash storage use real PostgreSQL in the
guarded test DB. The user's failure report did not label each failure as live or
simulated; no actual outage or extra browser case is inferred. Timed 30-minute/
eight-hour browser expiration and account-switching observations were not
separately reported; their existing native/automated coverage is not relabeled.

### Git scope, checkpoint proposal and freeze boundary

Branch: feature/sign-in-sign-out-and-protect-private-sessions.
Current parent HEAD: 6d4fcdcd3a1ae2b29b256af9bf5c1da9b9a845e8.
Local main/origin-main recorded tip: 4153c5a4a2d9c8ba6e19c75b9a485257ec413811.
Enforceable review base ref: refs/remotes/origin/main; its merge base with this
branch is bd763da52ba52c07f3fad3200cccade663dbe756.

The branch retains Feature 1's original commits, whose product tree was already
squash-landed on main, and the user's pre-existing local workflow-notes commit.
Main versus current HEAD differs only in .gitignore and backend/prepapp.txt.
Those already-committed files are unchanged by Feature 2 and are not new staging
paths. A future current audit must use the real merge-base range, which includes
inherited Feature 1 history and notes; do not pretend its base is main's tip.
No rebase, cherry-pick, branch transition, remote access or history edit occurred.

The exact proposal is 44 files: 21 modified tracked plus 23 new files. Nothing
is staged, and the tree is intentionally dirty with the reviewed implementation.
Private backend/.env and backend/.env.test are ignored, untracked and unstaged;
only public environment examples are proposed. Virtual environments,
node_modules, dist, caches and Blueprint generated state are excluded. The full
inventory/purposes, candidate diff and raw/Git-normalized content hashes are in:

- blueprint/.state/staging/feature-2-review-packet.md
- blueprint/.state/staging/feature-2-builder-review.diff
- blueprint/.state/staging/feature-2-checkpoint-proposal.json

Proposed local checkpoint message: `feat: add secure account sessions`.
No git add/commit was run. Explicit approval is needed before staging exactly
the proposed files and creating the immutable checkpoint. Only afterward run
`$audit independent current` against the new exact HEAD. Do not prepare a receipt
against today's old/incomplete HEAD, and do not run `$complete` yet.

The frozen spec hash and exact proposed tree/content manifest accompany the
review packet. After checkpoint/review, preserve specification and verification
record bytes; record live audit state only in review.md/findings.md. Those two
files are the workflow's allowed post-checkpoint evidence differences. If a real
finding needs repair, use the approved repair/new-checkpoint workflow rather
than silently changing reviewed code or entering a status/commit/audit loop.

### Remaining limitations and gates

- Independent audit has not run and no receipt exists; completion is blocked
  until an approved checkpoint receives a fresh passing current review.
- Login rate limiting remains a separately approved production-security task;
  there is no in-memory placeholder. Deployment/TLS/proxy setup and actual
  production HTTPS cookie delivery remain later deployment verification.
- Timed browser idle/absolute-cap observations and individually labeled live
  failure outages are not claimed; native boundary/concurrency and simulated
  failure evidence are explicitly identified above.
- A connection/HTTP failure after a server commit cannot undo that commit.
  POST is never automatically replayed; reconciliation uses GET session or a
  deliberate user action. Unavailable UI preserves the distinction from logout.
- Local configured checks are not a network dependency-vulnerability scan.
  No network-backed audit, deployment or remote action was run.
- Check is configured manual and was not separately invoked. The configured
  read-only try guide is included in the verified spec/final packet, using the
  existing guarded walkthrough. Guide generation is not new test evidence.
- Feature 2 is not archived or marked complete in build-plan.md. No commit,
  merge, push, deploy, `$complete`, or Feature 3 work was performed.

## F-01/F-02 repair follow-up: user browser observations and checkpoint proposal

This follow-up supersedes pending-repair status only. It does not rewrite the
earlier builder results, native evidence, November 6 Chrome report or independent
audit. The user approved repairs for these two findings only, then supplied the
focused browser observations below for development and production preview.
No new observation date or browser version was supplied; the original Chrome
version, viewport sizes and dates are not automatically reused for this report.

### Original audit and repair boundaries

Original reviewed HEAD: `fefa4b242047a0a18c02228963db3344ef2ce4fa`.
Original specification SHA-256:
`993c246ddf15d9c85b53b0d451dc630ebf89b6279862f88d3c1e37fd01cb22b4`.
Reviewer: Codex gpt-6.1-sol in a fresh isolated subagent. Result:
changes-requested, with F-01 and F-02 originally open at P1.

The original receipt in blueprint/context/review.md remains byte-for-byte
unchanged, SHA-256
`5ecd89201df1f29025290616d1d8ed8535c36a0e4d8670c87e06019dfffbf209`.
It is historical evidence and is stale for the repaired code/specification.
The ledger retains each original explanation, reproduction and recommendation;
builder repair notes now mark both findings fixed pending independent review.
Fixed is not closed and still blocks completion. No independent reviewer has
approved these repairs. Local ignored copies of the original receipt and open
ledger are retained under blueprint/.state/staging for comparison.

F-01 now uses React Router matching for account navigation instead of an exact
pathname comparison. F-02 replaces the renewing expiry request with local
identity clearing, pending-request cancellation and safe session-ended behavior.
Backend validity, transactions, schema, cookies, API contracts and dependencies
are unchanged. No additional Feature 2 product work is included.

### Automated repair evidence, reused from the preceding repair pass

These are actual earlier repair-pass results, not checks rerun while recording
this browser report. Python 3.13.17, pytest 8.3.5, Node 22.23.4 and Vite 6.4.5:

| Command | Repair-pass result |
| --- | --- |
| `node --test frontend/tests/sessionState.test.js` | 63 passed, zero failures. |
| `node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js` | 125 passed; zero failures, cancellations, skips or todo cases. |
| `npm --prefix frontend run lint` | Passed. |
| `npm --prefix frontend run build` | Passed, 50 modules; approved outside-sandbox retry after the known esbuild parent-directory access denial. |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider` | 360 passed, 87 native cases deselected; existing deprecation warning. |
| `backend/.venv/Scripts/python.exe -m pip check` | No broken requirements found. |
| `git diff --check` | Passed; expected LF-to-CRLF notices only. Rechecked for this documentation/checkpoint preparation. |

The focused tests cover route matching/history/failures/stale responses and
fake-clock expiry with normal, ahead and behind device clocks, equality,
post-expiry deliberate revalidation and no idle-extension loop. Node labels its
mock-timer API experimental. These are automated simulations, not browser runs.

No backend file changed during the repairs. The agent did not reconnect to
PostgreSQL or rerun native tests during the repair or this documentation turn.
The earlier 87 guarded native passes and their cleanup evidence remain
historical native evidence, separate from the user's new browser cleanup report.

### User-performed focused browser observations

The user reported passing these checks in both development and production
preview. The agent did not independently perform or observe these browser runs.

| Reported check | User-observed result |
| --- | --- |
| `/account`, `/account/`, `/ACCOUNT` | Each required fresh session validation. |
| `/accounting` | Did not match the protected account route. |
| Direct loads, refresh and Back/Forward | No cached private identity after logout or a rejected session. |
| Unavailable session response | Cached account content remained gated. |
| Idle expiration | Private identity cleared locally. |
| Expiration network behavior | No `/api/auth/session` requests, polling or repeated requests. |
| Deliberate navigation, visibility return and retry | Behaved according to the documented session flow. |
| Late responses | Did not restore cleared identity. |
| Logout/history protection and account isolation | Worked as expected. |
| Focus, announcements and responsive layouts | Worked as expected. |
| Guarded backend cleanup | Exact reserved synthetic account/session absence message observed. |

The user reported:

```text
Verified cleanup: all reserved synthetic accounts and sessions are absent.
```

This is user-observed guarded-backend cleanup, not a new agent SQL query or
native suite. The report does not establish a separately timed 30-minute or
eight-hour browser observation, a browser clock-skew run, production HTTPS
deployment, or individually labeled live-versus-simulated failure cases. No
unreported mixed-case variant, exact viewport or zoom result is inferred.

### Exact unstaged repair checkpoint candidate

Branch: `feature/sign-in-sign-out-and-protect-private-sessions`.
Parent HEAD: `fefa4b242047a0a18c02228963db3344ef2ce4fa`.
Proposed message: `fix: prevent stale account views and idle session renewal`.

The proposed checkpoint contains exactly these eight modified tracked files:

| File | Purpose |
| --- | --- |
| `frontend/src/SessionContext.jsx` | Pass the pathname for router matching and connect the non-renewing local expiry watcher. |
| `frontend/src/sessionState.js` | Router-consistent protected navigation, local expiry clearing and stale-request cancellation. |
| `frontend/tests/sessionState.test.js` | Route/history/failure and fake-clock regressions. |
| `blueprint/context/current-feature.md` | Approved repair step, verified implementation/user-browser evidence and pending independent-review gate. |
| `docs/verification/BROWSER_CHECKS.md` | Correct expiry expectations, repeatable repair checklist and separately attributed report. |
| `docs/verification/AUTHENTICATION_STATUS.md` | Separate repair automated/browser/cleanup evidence, historical audit and checkpoint boundaries. |
| `blueprint/context/findings.md` | Original audit findings plus builder-fixed notes awaiting fresh independent review. |
| `blueprint/context/review.md` | Preserve the unchanged original changes-requested receipt in the checkpoint history. |

The original receipt and findings were already uncommitted audit output before
repairs; including them preserves that review history. The original 44-file
proposal is not overwritten. New ignored review artifacts are:

- blueprint/.state/staging/feature-2-repair-checkpoint-proposal.json
- blueprint/.state/staging/feature-2-repair-review-packet.md
- blueprint/.state/staging/feature-2-repair-review.diff

The new manifest freezes all eight raw file hashes and Git-normalized blob
hashes, the new specification hash, parent and predicted tree. No staging,
commit, independent audit, completion, merge, push or deployment is authorized
by preparation. Private environment files remain ignored and unstaged; no
backend code, database file, dependency, build output or unrelated file is
included. After review, explicit checkpoint approval is required before staging
and committing this exact candidate. A new independent current review is a
later gate and must not be replaced by these builder/user verification claims.
