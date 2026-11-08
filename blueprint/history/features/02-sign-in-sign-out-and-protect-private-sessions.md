# Feature: Sign in, sign out, and protect private sessions

**From build-plan:** feature 2
**Build attempt:** 1
**Branch:** feature/sign-in-sign-out-and-protect-private-sessions
**Archive path:** blueprint/history/features/02-sign-in-sign-out-and-protect-private-sessions.md
**Status:** verified
**Independent-review gate:** required; the latest receipt for 4250092b58e8a73048e879fe00e9f4025cfd5d9b requested changes, leaving F-01 open and independently closing F-02. That receipt and ledger remain unchanged as historical evidence and are stale for the new code/specification. Automated checks and the user's November 7, 2026 Chrome development/preview observations support the encoded-path implementation. Checkpoint approval and a fresh independent audit remain pending. F-01 stays open; verified does not mean finding closure or feature completion.

## Goal

Users can sign in at `/login`, refresh without losing a valid session, view only
their own account at `/account`, and sign out. FastAPI authenticates every
protected request from an opaque, revocable PostgreSQL session, with precise
idle/absolute expiry and safe failures. Registration and both health endpoints
continue working.

This packet incorporates the approved decisions and twelve clarifications.
It authorizes no implementation, installation, database connection, branch
creation, commit, merge, or push until the appropriate subsequent approval.

## In scope

- Login, current-session lookup, and current-browser logout endpoints.
- Shared email/password processing, Argon2 verification, one process-local dummy
  hash, opaque session tokens, SHA-256 token hashes, and secure cookie handling.
- Atomic session validation/idle extension, fixation prevention, revocation,
  independent device sessions, and narrowly scoped session housekeeping.
- A reusable authenticated-user/session dependency and server-derived identity.
- Same-origin JSON requests, explicit trusted origins, CSRF enforcement, and
  registration regressions for the changed request-header requirements.
- Accessible `/login`, minimal protected `/account`, transient React session
  state, refresh restoration, and safe expiration/logout/navigation behavior.
- Database-free tests, guarded native tests and exact cleanup, manual browser
  checks, and separate authentication evidence.

## Out of scope

- Password reset, email verification, OAuth/social login, account deletion,
  administrator roles, shared accounts, and remember-me choices.
- Vehicle CRUD, service routes, a finished authenticated dashboard, session/device
  management screens, sign-out-everywhere, and background cleanup jobs.
- Schema changes or initialization, Django, ORMs, JWT/framework adoption,
  new dependencies, pooling, CI, or incidental browser-test tooling.
- Production deployment and production rate limiting. Record rate limiting as
  a production-security limitation; do not add an unreliable in-memory limiter
  or change schema/dependencies without a separate decision.

## Build loop

- `$implement` begins only after this specification is approved, on the exact
  dedicated branch above. This planning command does not create or switch branches.
- `workflow.stepReview: every` requires a review stop and approval after each
  build step. `checkpointCommits: enabled` permits offers, not automatic commits.
- Run the database-free Test gate for backend logic and lint/build for frontend
  changes. Native testing requires explicit opt-in and the guards below.
- Authentication is sensitive: the final `$audit independent current` gate must
  cover the whole feature. A required immutable checkpoint needs separate commit
  approval. Preserve reviewed spec bytes after a receipt; do not create another
  documentation/commit/audit loop merely to update status after review.
- `$check` is manual; `$check guide` supplies the configured human try path.
  `$complete` alone owns approved archival and completion bookkeeping. Every
  commit, merge, push, and deployment requires its applicable explicit approval.

## Build steps

- [x] 1. Define credentials, session contracts, and validated authentication settings.
  Reuse `AccountEmail` and factor shared password normalization inside the
  credential-security boundary. Add verification, one dummy hash, token helpers,
  public response models, cookie settings, and origin/CSRF policy helpers.
  Keep enforcement off existing routes until Step 3 updates their callers.
  **Done when:** focused database-free tests prove identical registration/login
  normalization, one verification for valid-shaped known/unknown-email attempts,
  dummy initialization once, token/hash properties, safe representations,
  cookie attributes, and rejection of insecure non-loopback/production settings;
  the complete database-free suite and pip check pass without PostgreSQL.

- [x] 2. Add session queries, transactions, and owned native fixtures.
  Add parameterized credential lookup and session operations. Build the reusable
  dependency's validation/extension transaction, fixation-safe replacement,
  revocation, and user-scoped housekeeping. Extend existing test guards/cleanup
  for users and sessions before any native writes.
  **Done when:** database-free tests prove binding, lock/time ordering, failure
  rollback/close, and fixture safety. Opted-in native tests against only
  `garageguide_app_test` prove committed sessions, both expiry limits,
  revocation/extension serialization, replacement, independent sessions, and
  verified exact fixture cleanup. An absent schema stops verification; no DDL.

- [x] 3. Wire the three authentication endpoints and enforce CSRF safely.
  Connect existing helpers and queries; do not duplicate normalization or SQL.
  Introduce the shared authenticated-user/session dependency. Extend the safe
  auth error boundary and cookie handling. In this same step, update registration's
  React request helper and existing test callers with required headers, keeping
  the existing registration page usable before adding new pages.
  **Done when:** database-free and guarded native API tests pass the response,
  cookie, transaction, CSRF, cache, redaction, expiry, and identity-isolation
  contracts. Registration still returns its approved results with valid headers;
  both health endpoints retain existing behavior. Frontend lint/build pass.

- [x] 4. Add login, session restoration, protected account UI, and logout.
  Reuse the one existing BrowserRouter and React Router navigation. Add transient
  session state, protected-route loading/denial handling, and accessible forms
  and status feedback. Add no dashboard or vehicle management.
  **Done when:** lint/build and the database-free suite pass; browser checks in
  development and preview demonstrate valid/invalid login, refresh restoration,
  rejection/availability distinction, logout/history safety, password lifetime,
  pending/error/retry behavior, and layouts near 375/768/1440 pixels. Repeat
  registration browser checks with the required origin/JSON/custom header.
  **Checkpoint:** Complete. Automated results are recorded separately from the
  user's November 6, 2026 manual development/preview observations in Chrome
  156.0.8078.73. Reported checks passed for routing, guest denial, login/restoration,
  logout/history/repetition, independent sessions, registration/CSRF, failures,
  password lifetime, accessibility, responsive widths and 200% zoom, with the
  exact synthetic account/session cleanup marker confirmed. See
  docs/verification/AUTHENTICATION_STATUS.md for the report and evidence limits.
  The user subsequently approved Step 4 before final verification.

- [x] 5. Verify the complete slice and prepare independent review.
  Run the applicable final gates and guarded native suite, verify exact cleanup,
  and record authentication evidence separately from registration history.
  Record browser observations honestly and prepare the configured independent
  audit for its separately approved immutable checkpoint. No automatic audit
  fixes or commits.
  **Done when:** each acceptance claim has identified automated/native/browser
  evidence, registration/health regressions pass, cleanup is verified, limitations
  are explicit, and the exact checkpoint proposal is ready for user approval.
  **Required completion gate after checkpoint approval:** run `$audit independent current`
  against that committed HEAD and require a current passing receipt before the
  final completion handoff. This gate remains pending and is not claimed passed
  by this checkbox or the verified implementation status.
  **Final evidence:** 360 database-free backend tests, all 87 guarded native
  tests with verified exact cleanup, and 85 frontend checks passed; pip check,
  frontend lint/build and whitespace checks passed. Browser evidence is the
  user's November 6, 2026 Chrome report, kept separate from automated/native
  and simulated evidence in AUTHENTICATION_STATUS.md. No application behavior
  changed during final verification. Freeze this specification at the proposed
  checkpoint; subsequent audit state belongs in review.md/findings.md.

### Approved audit repair step

- [x] 6. Repair only independent-audit findings F-01 and F-02.
  Use React Router matching for all protected account-route variants, without
  matching unrelated paths. Gate cached private content until deliberate
  navigation revalidation succeeds, including Back/Forward and failure cases.
  Replace the activity-extending expiry request with local identity clearing
  and session-ended behavior. Cancel pending work so late responses cannot
  restore identity after expiry. Add route/history and fake-clock regressions.
  **Done when:** focused and complete frontend tests, lint/build, database-free
  backend tests, pip check and whitespace checks pass; the user repeats affected
  browser checks and reviews the repairs. No PostgreSQL connection, staging,
  commit or new audit is authorized by this repair step. Preserve the original
  findings and receipt as historical evidence; they cannot approve changed code.
  Neither finding is resolved by unit tests alone.
  **Automated repair evidence:** 63 focused session tests and all 125 frontend
  tests passed; frontend lint/build, all 360 database-free backend tests (87
  native cases deselected), pip check and whitespace checks passed. Node's
  fake-clock API reports an experimental warning; the backend retains its
  existing Starlette/AnyIO deprecation warning. The build passed on an approved
  retry outside the sandbox after an esbuild parent-directory access denial.
  No backend file changed, no PostgreSQL connection was made and no native test
  was rerun. The user's separate focused repair report now records passing
  development and production-preview observations for /account, /account/,
  /ACCOUNT, unrelated /accounting, direct loads/refresh/history, rejected and
  unavailable session gating, local expiration without session requests or
  polling, deliberate navigation/visibility/retry, late responses, logout,
  account isolation, focus, announcements and responsive layouts. The user
  observed: `Verified cleanup: all reserved synthetic accounts and sessions are absent.`
  This is user-performed browser/cleanup evidence, not an agent database run or
  reviewer finding closure. No browser version, observation date, exact viewport
  sizes, clock-skew browser run or timed server-expiration duration was supplied
  for this follow-up; do not inherit those details from the original report.
  See AUTHENTICATION_STATUS.md for the separate evidence record. Both findings
  are builder-marked fixed pending fresh independent review, not closed.

- [x] 7. Repair only the remaining F-01 encoded-path classification defect.
  Share the actual Account route descriptor between App.jsx and sessionState.js.
  Classify protected navigation with React Router's public matchRoutes API so
  decoding, case and end-of-path semantics agree with route rendering. Do not
  implement a custom decoder or add routes. Cover literal and encoded variants,
  unrelated/malformed paths, direct load/refresh, loading/401/unavailable states,
  Back/Forward and stale results. Preserve the independently closed F-02 behavior.
  **Automated evidence (November 7, 2026):** 108 focused session tests, 170 complete
  frontend tests and all 360 database-free backend tests passed; 87 native cases
  were deselected. Frontend lint/build and pip check passed. The production build
  passed on the approved outside-sandbox retry after the known esbuild access
  denial. Existing Node mock-timer and Starlette/AnyIO warnings remain. The new
  encoded navigation/history cases first reproduced the gap before the matcher
  correction. No backend, database, schema or dependency changes were made; no
  PostgreSQL connection or native rerun occurred.
  **User-performed browser evidence:** on November 7, 2026, Chrome 156.0.8078.73
  in Vite development and production preview validated /account, /account/,
  /ACCOUNT, /%61ccount, /acc%6Funt and /%41CCOUNT before displaying identity.
  Direct loads, refresh and Back/Forward passed; valid session checks returned
  200. Loading gated identity; rapid navigation canceled stale work. Simulated
  rejection/unavailability stayed safe, and restored real fetch plus Try again
  restored the valid session only after a fresh 200. Unrelated paths showed no
  Account content. Direct malformed HTTP paths produced Vite's URI malformed
  rejection before React loaded, a server-boundary observation only. Deliberate
  history checks are user activity, not expiry polling. F-02 application code
  was unchanged and no full 30-minute real idle observation was repeated. The
  user reported: `Verified cleanup: all reserved synthetic accounts and sessions are absent.`
  See AUTHENTICATION_STATUS.md for the separately attributed evidence and limits.
  **Pending:** explicit approval of the final F-01 repair checkpoint, then fresh
  independent review. F-01 remains open, and the previous receipt/findings are
  preserved unchanged. No staging, commit/amend, audit, completion, landing or
  push is authorized by this documentation/checkpoint-preparation pass.

## Files / areas

| File or area | Responsibility |
| --- | --- |
| `backend/app/schemas.py`, `security.py` | Shared typed credentials, NFC processing, Argon2 verification/dummy hash, opaque token generation/hash, public response schemas. |
| `backend/app/config.py`, backend environment examples | Validated authentication environment, origins, and cookie settings; preserve database settings and ignored private files. |
| `backend/app/user_queries.py` | Parameterized normalized-email credential lookup; preserve registration queries. |
| `backend/app/session_queries.py` (new) | Focused parameterized session lookup/locking, insertion, extension, revocation, and user-scoped cleanup. No generic repository framework. |
| `backend/app/authentication.py` (new) | Reusable synchronous authenticated-session dependency, trusted actor context, and shared request/cookie policy. |
| `backend/app/routes/auth.py`, `main.py` where needed | Endpoint orchestration, safe responses, cookie delivery, no-store headers, and existing router wiring. |
| `backend/tests/conftest.py`, `database_support.py`, registration helpers/tests | Test settings, cookie-aware clients, guarded owned session fixtures, redaction, and registration header regressions. |
| New focused backend authentication/config/session tests | Unit/API/native contracts, lifecycle concurrency, identity isolation, and cleanup. |
| `backend/tests/manual_registration_server.py` or a clearly named replacement | Guarded manual backend restricted to fixture-owned accounts and all their session writes; reuse existing safety support. |
| `frontend/src/api.js`, `App.jsx`, `main.jsx`, `styles.css`, `Register.jsx` where needed | Same-origin API helpers, routing, auth provider wiring, styles, and registration compatibility. |
| `frontend/src/Login.jsx`, `SessionContext.jsx`, `RequireSession.jsx`, `Account.jsx` (new) | Login form, public session state, protected UI gating, minimal account/sign-out page. |
| `README.md`, applicable coding standards, `docs/verification/BROWSER_CHECKS.md` | Document actual authentication contracts, configuration, safety, and manual checks. |
| `docs/verification/AUTHENTICATION_STATUS.md` (new during implementation) | New observed authentication and registration-regression evidence; reference prior records without relabeling them. |

Requirements files, frontend package files, and numbered SQL files need no
dependency/schema changes. Keep `database.py` health connections read-only and
retain existing three-second connection and 3000-ms statement timeouts.

## Data / contracts

### Credentials and public responses

- Login accepts exactly the credential fields `email` and `password`; no password
  confirmation, user ID, timestamp, token, or hash controls identity/session data.
- Use the existing shared process: trim surrounding email whitespace, validate
  with EmailStr, use its normalized result, then lowercase the account identifier.
- Password is SecretStr. Unwrap only inside credential-security helpers; share
  NFC normalization and the existing 15-128 Unicode-code-point rules. Preserve
  case and spaces; never trim, lowercase, truncate, or add composition rules.
- Reuse installed pwdlib Argon2 verification. Generate the dummy Argon2 hash
  once per backend process and retain only that hash. Every syntactically valid
  known-email or unknown-email attempt performs exactly one password-verification
  call using the stored hash or dummy hash. Validation rejection happens before
  lookup/verification. Never generate a dummy hash per request or claim perfectly
  constant end-to-end timing. Malformed stored hashes are unexpected failures.
- Public `user` contains exactly positive integer `id`, normalized `email`, and
  timezone-aware RFC 3339 `created_at` from users. Session `expires_at` is the
  effective idle deadline, also timezone-aware RFC 3339. Never return a session
  token, token hash, password hash, session-row ID, or revocation internals.

| Endpoint / outcome | Status and contract |
| --- | --- |
| `POST /api/auth/login`, correct credentials and committed session | 200, exactly `{user: {id, email, created_at}, expires_at}` plus the session cookie. |
| Login with unknown email or wrong password | 401, `{"detail":"Invalid email or password."}`. Same response for both; do not disturb an existing session or cookie. |
| `GET /api/auth/session`, valid session | 200, exactly `{user: {id, email, created_at}, expires_at}` after atomic validation/extension commits. |
| Session lookup without a usable session | 401, `{"detail":"Not authenticated."}`, and delete the unusable cookie. Missing/malformed/unknown/expired/revoked cases share this response. |
| `POST /api/auth/logout`, body `{}`, valid CSRF policy | 204, no body; revoke the current session and clear the cookie. Missing/malformed/unknown/expired/already-revoked sessions also produce 204 and clear the cookie. |
| Invalid request fields or malformed JSON | 422 with sanitized `detail` entries containing only safe loc/msg/type and fixed messages. No raw input/ctx or secret values. |
| Origin, JSON content-type, or custom-header policy rejection | 403, `{"detail":"Request not allowed."}`. No session or cookie changes. |
| Database availability/statement-timeout failure | 503, `{"detail":"Authentication unavailable. Please try again."}`. Do not clear or replace a potentially valid cookie. |
| Unexpected authentication failure | 500, `{"detail":"Internal server error"}`. No private details or cookie mutation. |

All authentication responses, including denials/errors and existing registration
responses, carry `Cache-Control: no-store`. Registration keeps its existing
201/public-body, sanitized 422, approved 409, and generic 503/500 contracts after
the new CSRF gate; the gate itself may reject with the fixed 403 above. Both
health endpoints remain public with their existing contracts.

### Cookie, environment, and CSRF

- Cookie name is `garageguide_session`; HttpOnly, SameSite=Lax, Path=/, host-only
  with no Domain. Issuance sets neither Max-Age nor Expires. Cookie flags do not
  replace server-side expiration checks or guarantee logout on browser shutdown.
- Secure=True in production. Secure=False is allowed only in explicitly selected
  loopback development/testing, never as an implicit fallback. Configuration must
  reject false for production or non-loopback use before any auth SQL/cookie write.
- Define validated auth settings separately enough to preserve existing database
  settings/health callers: environment (development/testing/production), strict
  secure-cookie boolean, canonical API origin, and production frontend origin.
  Safe defaults must not silently enable insecure development. An invalid auth
  configuration fails closed with a fixed unavailable response, not raw settings.
- Local canonical API origin is `http://127.0.0.1:8000`. Local trusted frontend
  origins are exactly `http://127.0.0.1:5173` (development) and
  `http://127.0.0.1:4173` (preview). Production requires separately configured
  canonical HTTPS origins; do not guess a production hostname or allow wildcards.
  An insecure setting requires loopback API/frontend configuration and loopback
  serving; spoofed forwarding/Host headers cannot enable that mode. Test clients
  must use explicitly valid loopback/HTTPS settings, not a general test bypass.
- On registration, login, logout, and future protected mutations, require a single
  valid exact trusted Origin, media type application/json, and
  `X-GarageGuide-CSRF: 1`. Reject missing/null/malformed/untrusted Origin values,
  form/simple content types, and missing/wrong headers before business writes.
  Accept ordinary JSON charset parameters. Do not fall back to Referer, permissive
  CORS, inferred forwarding hosts, or browser-readable authentication tokens.
- The custom header is a public CSRF request marker, not a secret/token. Attach
  it only to explicit relative application API requests; do not override global
  fetch or add unrestricted credentialed cross-origin behavior. GET session lookup
  does not require mutation headers. Session activity accounting is incidental;
  GET performs no product-data mutation or session-token rotation.
- Setting and deleting use the same name, Path, SameSite, Secure, HttpOnly and
  host-only behavior. Deletion alone uses expiration/Max-Age=0 to remove the
  cookie. Factor the shared attributes so logout/401 cannot leave a second cookie.

### Session lifecycle, transactions, and actor identity

- Generate a new token from 32 cryptographically random bytes for every successful
  login, encoded as unpadded URL-safe text. Hash its ASCII representation with
  SHA-256, storing only the lowercase 64-character hexadecimal digest in the
  existing unique token_hash column. Validate cookie shape/length before lookup.
  No JWT, bearer-token response, browser storage, or additional token library.
- `created_at` is immutable and begins the eight-hour absolute lifetime.
  `expires_at` is the current 30-minute idle deadline. Initial expiry is
  created_at + 30 minutes. Both timestamps come from PostgreSQL time, not input.
- With server time N, a session is valid only if revoked_at is null,
  N < expires_at, and N < created_at + eight hours. Equality means expired.
- Valid authenticated activity sets expires_at to the earlier of
  N + 30 minutes and created_at + eight hours. Never extend past the cap, rewrite
  created_at, clear revoked_at, or extend a session that failed validation.
- Validation/extension must be one short atomic transaction using the session
  row lock. Acquire the row lock first, then sample PostgreSQL current time after
  any lock wait (for example clock_timestamp in a separate statement), recheck
  all validity predicates, and extend only the still-valid locked row. Transaction-
  start/statement-start time sampled before waiting is insufficient. Retain SQL
  predicates protecting revocation/expiry; parameterize every variable value.
- Logout, replacement, and extension serialize on the same session row. An
  extension waiting behind committed revocation/expiry must reject, never revive
  the row. Commit a successful extension before returning authenticated identity.
- The reusable synchronous dependency in authentication.py is used by
  GET /api/auth/session and future protected routes. It returns a trusted public
  user and internal session context derived only from the validated database
  session. Never trust a browser-supplied owner/user ID. Future resource queries
  must also scope by this trusted identity; this dependency alone does not prove
  vehicle/service authorization for routes that do not exist yet.
- Verify login credentials before opening the short write transaction. After
  credential success, generate a completely new token. If the presented cookie
  identifies an existing valid session, lock/recheck and revoke that specific
  session inside the successful login transaction, even when switching accounts.
  Preserve other active sessions. Never accept/reuse the old token as the new one.
- In that transaction, remove only the newly authenticated user's expired or
  already-revoked session rows, and insert the new session. Do not delete active
  sessions, another user's rows, or account/product data. No background/global
  cleanup is introduced. Retained invalid rows cannot authenticate.
- Logout identifies only the cookie's session, commits revocation when applicable,
  then clears the cookie and returns 204. Repetition remains safe. Never revoke
  all devices by user ID. Independent cookie jars may hold independent sessions;
  do not invent device tracking, a session limit, or a device-management UI.
- Prevalidate/serialize the success payload and prepare cookie headers before
  the final commit; send neither until commit succeeds. Pre-commit failures roll
  back replacement/cleanup/insertion and preserve the old session/cookie. Do not
  query aborted transactions; close connections before safe error translation.
- A connection drop/HTTP timeout after commit cannot undo that commit. Do not
  automatically replay POST. Show uncertainty, retain no token in JavaScript,
  and reconcile through the current-session endpoint or deliberate user retry.
- GET/dependency authentication rejection is 401 with cookie removal. A login
  credentials 401 preserves existing authentication; logout's idempotent outcome
  is 204 after CSRF checks. Availability failures are 503, never fabricated 401s,
  and never delete a potentially valid cookie.

### React behavior and secret lifetime

- Preserve `/` and `/register`; add separate `/login` and minimal protected
  `/account` showing the current email and sign-out control. Keep the single
  BrowserRouter and use Routes/Route/Link and protected-route gating.
- All frontend API calls use relative `/api` URLs and explicit
  credentials: same-origin. Validate public response shapes before use.
  Retain the 10-second bound/cancellation and no automatic POST retries.
- A session provider holds only public user data, effective expiry, and UI state
  in React memory. Initialize through GET /api/auth/session on refresh. Unknown
  state gates private content; 401 means guest; 503/network/unexpected startup
  failure means unavailable with retry, not an invented successful login/logout.
- On a protected request's 401, discard private state and redirect to `/login`
  with a safe session-ended message. Login's invalid-credentials 401 instead
  displays its generic error and must not clear a previously valid session.
- Recheck on deliberate protected navigation, visibility return, refresh/startup
  or retry. At the known local expiry boundary, clear private React identity
  and enter the safe session-ended/login flow without an API request. An expiry
  timer must never call an endpoint that extends idle activity. Until
  revalidation, gate potentially stale private content. Server time remains
  authoritative; client timers never grant access.
  Cancel/ignore stale requests after navigation, identity change, or logout so
  late responses cannot repopulate private state. Do not refresh on an interval
  merely to keep an otherwise idle session alive.
- Login has labeled email/password inputs, autocomplete=email/current-password,
  associated errors, focus on first invalid field/feedback, live announcements,
  pending indication, disabled repeat submission, and deliberate retry. Render
  text with React escaping. No password-confirmation field is needed for login.
- Keep passwords only in temporary Login component state after correctable
  validation/invalid-credential/network failures. Clear after success, other
  failures, navigation, and document departure/return. No shared password state.
- On successful login, update public session state, clear password, and navigate
  to `/account`. On successful logout, clear private state and navigate to login;
  Back/Forward must not restore an authenticated view. A failed logout shows safe
  retry feedback without claiming revocation or clearing a potentially valid cookie.
- Tokens/passwords/hashes must never appear in localStorage, sessionStorage,
  router state, URLs, logs, telemetry, screenshots, frontend bundles, or JSON
  responses. Only the HttpOnly cookie transports the authentication token.

### Test database and cleanup boundary

- No database connection is authorized by this planning command. During approved
  implementation verification, native tests require RUN_DB_TESTS=1 and effective
  database name exactly garageguide_app_test; load only backend/.env.test.
- Retain the settings guard and run SELECT current_database() once immediately
  after opening each physical native connection, before exposing it or writing.
  Check API-handler, fixture, session-touch, housekeeping, and cleanup connections.
  Do not repeat the name query before every statement. A mismatch closes without writes.
- Extend read-only schema prechecks for existing users/user_sessions fields and
  constraints. A missing/unprepared schema stops testing; never initialize or alter it.
- Reserve unique, initially absent synthetic accounts and register finalizers
  before writes. Track exact owned user IDs/emails and session IDs/hashes; recover
  committed sessions by their test-owned user IDs after a lost response. Do not
  print token/hash/password values or full client/cookie/request representations.
- Delete only exact fixture-owned sessions/users, using the existing session FK
  cascade where appropriate, then explicitly verify absence of both user and
  session records on guarded connections. Never delete by prefix, truncate,
  reset sequences/databases, remove unrelated rows, or write to garageguide_app,
  postgres, or another database. Cleanup failure fails/stops native verification.
- Extend the manual test backend's restrictions to every login, session extension,
  logout, and housekeeping write, not only registration. It must accept/use only
  its reserved synthetic accounts/sessions and verify exact shutdown cleanup.

## Testing

No checks were run as evidence of Feature 2 behavior during specification work.
There is no configured combined Verify or Browser tests command. Use the existing
commands during implementation; do not install a runner incidentally.

| Gate | Command from repository root |
| --- | --- |
| Database-free backend | `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider` |
| Python dependency consistency | `backend/.venv/Scripts/python.exe -m pip check` |
| Frontend lint | `npm --prefix frontend run lint` |
| Frontend build | `npm --prefix frontend run build` |
| Opt-in guarded native suite | `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider` with RUN_DB_TESTS=1 and guarded garageguide_app_test only. |

- Unit/API tests: identical normalization; SecretStr/redaction; dummy hash once
  and exactly one verify per valid-shaped attempt; opaque token/hash format;
  cookie issuance/deletion matching; environment/origin validation; CSRF and
  no-store on all auth outcomes; public response whitelist; generic 401s;
  401-versus-503 cookie behavior; failed login preserving an existing session;
  commit-before-cookie/success, rollback/close, and safe unexpected failures.
- Lifecycle tests: creation/deadlines, just-before/equal/after both expiry limits,
  activity capped at eight hours, immutable creation, revocation/replacement,
  idempotent logout, independent sessions, and user-scoped invalid-row cleanup.
- Native tests: committed state visible on another connection, real hashing and
  hashed-only token storage, two-account current-user isolation, rejection of
  supplied owner IDs, lifecycle/rollback/availability recovery, and exact cleanup.
  Deterministic two-connection row-lock coordination with bounded waits must
  prove a waiting extension cannot revive a revoked/expired session; time must
  be sampled after lock acquisition. Do not rely solely on sleep-based races.
- Registration regression tests: valid Origin + JSON + custom header still
  produce committed 201, normal/constraint duplicate 409, and safe validation;
  missing/wrong/null/malformed/untrusted origins, missing/wrong custom header,
  and non-JSON form submissions are rejected without account/session changes.
  Preserve the existing connection/health behavior and read-only health mode.
- Manual browser checks: development and preview direct loads/refresh/history;
  login failures/success; restored session; pending/disabled state; protected
  denial versus unavailable/retry; logout/repeat logout; idle/absolute expiry;
  multiple independent cookie jars; safe failures and secret clearing; keyboard,
  field associations/focus/announcements; widths 375/768/1440 and zoom. Repeat
  registration success/duplicate/error checks with the required headers.
- Browser verification uses only the guarded test backend and unique fixtures
  with verified cleanup. Any shortened expiry controls belong only to that test
  launcher/fixtures, never product bypass endpoints. No populated-secret
  screenshots, HAR exports, cookie dumps, or browser/request-body logging.
  Local browser/API cookie evidence and HTTPS test-client flag checks do not
  prove deployed production HTTPS; deployment verification remains Feature 15.
- Record commands, totals, cleanup, runtime/browser versions and observed cases
  in AUTHENTICATION_STATUS.md. Keep automated, native, manual, and simulated
  evidence distinct. If behavior changes after browser checks, identify and
  repeat affected checks. An unavailable browser environment leaves explicit
  pending checks with exact manual instructions; build output is not UI proof.

## Notes for the AI

- Write/review this specification only now. Do not implement, install, connect
  to PostgreSQL, create a branch, commit, merge, or push. Await user approval.
- First build attempt is 1; the exact new branch/archive names were checked for
  availability and historical collisions. Freeze them through implementation.
- Preserve existing local workflow notes, private/ignored files, and prior
  feature refs during any later approved branch transition. This planning
  request does not move the user's notes commit or create the Feature 2 branch.
- Keep Python 3.13/FastAPI/direct psycopg, parameterized SQL and numbered schema
  authority. No schema changes, ORM, JWT framework, new dependency, or unrelated
  feature is authorized. Small focused helpers suffice.
- Production login rate limiting remains an explicit security limitation for a
  separate deployment/security decision; no in-memory placeholder is acceptable.
- There are no unresolved product choices after the approved clarifications.
  Native schema readiness and deployed HTTPS configuration still require actual
  later verification and must never be assumed from this specification.

## Try it now

Run or do:

Using the guarded test backend and frontend started as documented in
docs/verification/BROWSER_CHECKS.md, use a fresh reserved synthetic account at
http://127.0.0.1:5173/login. Sign in, refresh /account, sign out, then use Back.
Stop the guarded backend normally afterward and wait for its exact cleanup marker.

Expected:

The account email returns after refresh; sign-out goes to /login, and Back does
not reveal private account content. The launcher reports:
`Verified cleanup: all reserved synthetic accounts and sessions are absent.`

This proves:

That browser's sign-in, cookie-based restoration, current-session sign-out and
history protection for the synthetic account. This optional guide is not a new
test result or an independent-review receipt.


<!-- blueprint:completion {"schemaVersion":2,"specBytes":37019,"specSha256":"b65e2da5acc0e6dac2755f3e8657459bbbceabb05ca1b07c189bef64b030cf8a","branch":"refs/heads/feature/sign-in-sign-out-and-protect-private-sessions","head":"af562929d28ceb704bebc918eeb395f6bab2465a","baseRef":"refs/heads/main","baseCommit":"4153c5a4a2d9c8ba6e19c75b9a485257ec413811","sourceTree":"a2c21a964ebe0254e829835ac8b307682ad08b0c","landing":"local-merge","absentOptional":[]} -->

## Completion record

Prepared November 7, 2026 (America/Chicago) for explicit completion-commit review.
Feature 2, build attempt 1. This archive is the completion record; its preparation
does not approve a commit, landing, push, deployment or Feature 3.

The original verified specification above is preserved byte-for-byte, including
its historical planning/checkpoint wording and existing Try it now guide. The
passing receipt below establishes the final review of af562929d28ceb704bebc918eeb395f6bab2465a; earlier
pending/open statements in frozen records describe their own earlier stages.
The receipt is not relabeled as reviewing a later completion or landing commit.

### Final completion checks run in this preparation

| Command | Actual result |
| --- | --- |
| `node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js` | 170 passed; no failures, cancellations, skips or todo cases. |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider` | 360 passed; 87 native cases deselected; existing Starlette/AnyIO deprecation warning. |
| `backend/.venv/Scripts/python.exe -m pip check` | No broken requirements found. |
| `npm --prefix frontend run lint` | Passed. |
| `npm --prefix frontend run build` | Passed, 51 modules; established approved outside-sandbox path for the known esbuild directory restriction. |
| Whitespace and completion-transform checks | Passed before preservation; rechecked on the final proposed diff including this new archive. |

Node's mock-timer API reports its existing experimental warning. No dependencies,
application code, tests, configuration, SQL or live verification documents were
changed by completion bookkeeping. The normal Git index remains empty.

### Evidence categories and limitations

- Automated evidence above is a new completion run. Recorded native PostgreSQL
  evidence is reused: the complete guarded 87-case run and exact synthetic
  user/session cleanup are preserved in the verification record. No PostgreSQL
  connection, native rerun or new agent cleanup was performed in this pass.
- The final independent reviewer also reused recorded native results and
  user-performed browser evidence after checking applicable code equality.
  Its rerun commands, reuse decisions and limitations remain verbatim below.
- Browser observations are the user's reports, including November 7, 2026,
  Chrome 156.0.8078.73 in Vite development and production preview. They are not
  agent/reviewer browser execution. Simulated rejected/unavailable responses
  are labeled separately from real-fetch 200 recovery and the user-observed
  exact cleanup marker.
- Direct malformed HTTP paths were rejected by Vite with URI malformed before
  React loaded. That is development/preview-server boundary evidence, not React
  browser coverage for malformed paths. Matcher/store coverage is automated.
- The full 30-minute real browser idle observation was not repeated during the
  final F-01 repairs or this completion pass. Fake-clock checks are simulations;
  native strict idle/absolute expiry/locking evidence keeps its original scope.
- Deliberate protected navigation, refresh, visibility return and retry are
  user activity. The local expiration timer clears identity without a request,
  polling, retry or idle renewal. PostgreSQL enforces actual session deadlines.
- Login rate limiting and deployed HTTPS/proxy/cookie verification remain later
  production-security/deployment work. No current network dependency scan,
  additional browser/assistive-technology result or load/profile claim is made.
- Check is configured manual and was not required by the independent request.
  The existing Try it now guide is retained in the frozen specification and is
  instructions, not a new runtime observation.

### Independent finding closure history

| Archived ID | Independent closure and later confirmation |
| --- | --- |
| 2/F-01 | Encoded-path repair independently closed at c3391f30d9139034f89550609274be2fe87bea48; reconfirmed by the ancestry review and final review at af562929d28ceb704bebc918eeb395f6bab2465a. |
| 2/F-02 | Independently closed at 4250092b58e8a73048e879fe00e9f4025cfd5d9b; reconfirmed by subsequent fresh reviews, including af562929d28ceb704bebc918eeb395f6bab2465a. |
| 2/F-03 | README correction independently closed by the final fresh review at af562929d28ceb704bebc918eeb395f6bab2465a. |

The complete original explanations, builder notes, reopenings, reproductions and
reviewer closure evidence are preserved in Findings below. No finding was
silently accepted or discarded.

## Implementation history

Local default base: `refs/heads/main` at `4153c5a4a2d9c8ba6e19c75b9a485257ec413811`.
Reviewed final feature HEAD: `af562929d28ceb704bebc918eeb395f6bab2465a`.

The complete branch-only history below includes inherited original Feature 1
commits because Feature 1 was squash-landed on main. They are labeled as
inherited history, not new Feature 2 implementation. The approved two-parent
ancestry merge made main an ancestor while preserving the exact application,
specification and November 7 browser-evidence bytes. Its only content changes
from the first parent preserved the then-current audit records.

| Commit | Parent(s) | Subject | Role |
| --- | --- | --- | --- |
| `ab831c9cea3c173804447cbecb0ae68cc3244dcc` | `bd763da52ba52c07f3fad3200cccade663dbe756` | feat: add user account registration | Inherited Feature 1/local-note history |
| `73f0b72801f903ce81ba7b8db7c69e7e68241919` | `ab831c9cea3c173804447cbecb0ae68cc3244dcc` | docs: record registration verification and audit | Inherited Feature 1/local-note history |
| `163810de0b926418ddbfc381b6b346b41d9ce16a` | `73f0b72801f903ce81ba7b8db7c69e7e68241919` | feat: register user accounts | Inherited Feature 1/local-note history |
| `6d4fcdcd3a1ae2b29b256af9bf5c1da9b9a845e8` | `163810de0b926418ddbfc381b6b346b41d9ce16a` | docs: add local backend workflow notes | Inherited Feature 1/local-note history |
| `fefa4b242047a0a18c02228963db3344ef2ce4fa` | `6d4fcdcd3a1ae2b29b256af9bf5c1da9b9a845e8` | feat: add secure account sessions | Feature 2 checkpoint/repair |
| `4250092b58e8a73048e879fe00e9f4025cfd5d9b` | `fefa4b242047a0a18c02228963db3344ef2ce4fa` | fix: prevent stale account views and idle session renewal | Feature 2 checkpoint/repair |
| `c3391f30d9139034f89550609274be2fe87bea48` | `4250092b58e8a73048e879fe00e9f4025cfd5d9b` | fix: align protected navigation with router decoding | Feature 2 checkpoint/repair |
| `29122e55d5eae32f22dc8c977c7ce872e556473d` | `c3391f30d9139034f89550609274be2fe87bea48 4153c5a4a2d9c8ba6e19c75b9a485257ec413811` | chore: reconcile main ancestry for authentication | Approved ancestry reconciliation |
| `af562929d28ceb704bebc918eeb395f6bab2465a` | `29122e55d5eae32f22dc8c977c7ce872e556473d` | docs: clarify local session expiration behavior | Feature 2 checkpoint/repair |

## Preserved input identities

| Original input | UTF-8 bytes | Raw SHA-256 |
| --- | --- | --- |
| `blueprint/context/current-feature.md` | 37019 | `b65e2da5acc0e6dac2755f3e8657459bbbceabb05ca1b07c189bef64b030cf8a` |
| `blueprint/context/findings.md` | 17716 | `fc094b69636fbf17db063503a7d0f5e5abb89febb5d69923ef6d225d147c571c` |
| `blueprint/context/review.md` | 12904 | `c96fd4069add81f52fd93a0e9701d127f5b04cff93730c41138c3a901eaa8e22` |
| `docs/verification/AUTHENTICATION_STATUS.md` | 67818 | `6e41ca26c0b2f57ef7249226b4a580b90c169646d49ea300449abf57607358f1` |
| `docs/verification/BROWSER_CHECKS.md` | 33936 | `d8d3bdbfa361723125306921b6529f6a39d15e55524bf55e083cbe895e31c3be` |

## Findings

### 2/F-01 [P1] closed - Account URL variants bypass navigation revalidation

**File:** frontend/src/SessionContext.jsx:12
**Found:** 2026-11-07 by /audit independent (scope: current; lenses: quality, security, tests)
**Why it matters:** The provider marks only the exact pathname `/account` as protected. React Router's configured `/account` route also matches `/account/` and `/ACCOUNT`. With an already cached authenticated identity, entering either variant calls `store.enter` as a public navigation. It sets `checkedFor` to the new location key without requesting the server, so RequireSession permits the cached account email even if that session has since expired, been revoked, or changed in another tab. This violates the approved requirement to revalidate before showing private content on protected navigation. Backend authorization remains enforced.
**Evidence:** A reviewer-run Node reproduction used the installed router's actual `matchRoutes`, the actual `createSessionStore`, and the gate's predicates. For both variants, the router matched Account, session requests remained at one after navigation, status remained authenticated, and the private gate allowed rendering despite a simulated next response of guest. This is a logic reproduction with a simulated API, not browser observation. Existing state tests pass booleans directly and do not cover route classification.
**Suggested fix:** Use the router's matching semantics to classify the protected account route, or let the matched protected route own revalidation. Add regression coverage coupling actual route matching to revalidation for trailing-slash and case variants, including a rejected server session.
**Resolution:** Builder repair, pending fresh independent review. Session navigation now uses React Router matchPath('/account', pathname), with full-path matching and the router's default case handling. The existing private gate waits for revalidation for every account-route variant. Regression tests use actual router matching and memory-router Back/Forward, plus rejected/unavailable sessions and stale responses. The user separately reported passing focused development and production-preview browser checks for /account, /account/, /ACCOUNT, unrelated /accounting, protected history, rejection and unavailable gating, late responses, logout/account isolation and accessibility/layout behavior. All 63 focused session tests and 125 complete frontend tests passed during the repair pass. The original audit evidence above is preserved; this fixed status records builder repair and user observations only, not independent-review closure. A fresh passing current review remains required.

**Independent re-review (2026-11-07):** Reopened at checkpoint 4250092b58e8a73048e879fe00e9f4025cfd5d9b. The literal trailing-slash/case examples are repaired, but the same defect remains for percent-encoded account paths. Current affected location: frontend/src/sessionState.js:134. The installed router's matchRoutes decodes pathname segments before matching, while matchPath('/account', pathname) receives the raw pathname. A reviewer-run Node reproduction using the installed matchRoutes/matchPath, actual createSessionStore, and RequireSession's gate predicates confirmed /%61ccount, /acc%6Funt and /%41CCOUNT all match Account but are classified public. After cached identity was restored on a public page, each navigation left session requests at one and allowed the private gate, although the next simulated API result was guest. No private values were printed. This is a logic reproduction with a simulated API, not a browser observation. The existing 63 focused and 125 full frontend tests pass but omit percent-encoded variants. Suggested repair: use actual route matching semantics including decoding, or let the matched protected route own revalidation; add encoded-path rejection/unavailable/history regression cases and repeat affected browser checks. Backend authorization remains enforced. The original finding and builder evidence above are retained; F-01 is not closed.

**Independent final re-review (2026-11-07):** Closed at checkpoint c3391f30d9139034f89550609274be2fe87bea48 after a fresh review of the complete 63-path merge-base-to-target delta across quality, security, performance and tests. App.jsx renders the shared accountRoute descriptor, and sessionState.js:134 classifies navigation with public matchRoutes using that same descriptor. Rendering and classification therefore share router decoding, case and full-path semantics. The reviewer independently exercised the installed router, actual store and RequireSession gate predicates for 20 route/failure combinations, including the originally reported encoded variants, fully encoded account, case, trailing slash and multiple trailing slashes: each navigation initiated a second validation, gated pending identity, and never permitted private rendering after guest or unavailable responses. All 108 focused session tests and all 170 frontend tests passed, including direct-load/refresh, Back/Forward with reused keys, unrelated/malformed paths and stale-result regressions. Source review confirmed cancellation and the private gate remain intact; no new defect in this repair was identified. The user's November 7 Chrome 156.0.8078.73 development/preview report is separate supporting evidence, not reviewer-observed browser execution. Its malformed direct HTTP cases were rejected by Vite before React loaded and prove only that server boundary; React malformed-path coverage is automated. No full real 30-minute idle observation was repeated. Original finding, reopening and builder notes above remain historical. F-01 is explicitly closed by this review.

**Independent ancestry re-review (2026-11-07):** Remains closed at merge checkpoint 29122e55d5eae32f22dc8c977c7ce872e556473d. This fresh Codex gpt-6.1-sol subagent reviewed the complete 49-path current inventory from main, excluding the two audit records from application scope, plus nearby callers and contracts. App.jsx and sessionState.js still share accountRoute and matchRoutes semantics; RequireSession gates unmatched location keys, hidden/loading/unavailable state and rejected identities. Reviewed literal/encoded path, direct-load/refresh, reused-key history, failure and stale-response cases; all 170 frontend tests passed. The merge preserves all frontend/spec/browser-record bytes from c3391f3, and every conflict retains the exact first-parent Feature 2 blob. No regression in F-01 or new blocking issue was found. User-performed Chrome observations remain separately attributed; malformed direct HTTP rejection remains Vite-boundary evidence only.

**Independent README-checkpoint re-review (2026-11-08):** Remains closed at af562929d28ceb704bebc918eeb395f6bab2465a. This fresh Codex gpt-6.1-sol subagent reviewed the complete 49-path current delta across all four lenses, excluding the two audit records from application scope. App and the navigation store share accountRoute and public matchRoutes semantics, including encoded segments, case and trailing slashes. RequireSession gates visibility, unmatched navigation keys, loading, guest and unavailable states. All 170 frontend tests passed in this review, including the 108 session cases covering encoded navigation, direct load/refresh, reused-key history, rejection/unavailability and stale responses. No regression or new defect was found. November 7 Chrome observations remain user-performed; malformed direct HTTP rejection remains Vite-boundary evidence only.

### 2/F-02 [P1] closed - A fast device clock turns expiry checks into idle keepalive

**File:** frontend/src/SessionContext.jsx:36
**Found:** 2026-11-07 by /audit independent (scope: current; lenses: quality, security, performance, tests)
**Why it matters:** The timer subtracts device `Date.now()` from a server timestamp, then calls GET session, which extends valid sessions by 30 minutes. Each successful response changes `expires_at` and schedules another timer. If the device clock leads the server by five minutes, the timer fires after 25 server minutes while the session is still valid. That request renews the idle deadline, and the cycle repeats without user activity. An idle visible page therefore stays authenticated until near the absolute cap, contradicting the explicit prohibition on automatic requests that keep an otherwise idle session alive. The server's absolute cap remains enforced.
**Evidence:** A reviewer-run simulation used the actual session store, the provider's exact timeout calculation, an injected device clock five minutes ahead, and simulated server responses following the reviewed PostgreSQL validity/extension rules. After only three timer callbacks and no user activity, 75 server minutes had elapsed, four session requests had occurred, the idle deadline had advanced to minute 105, and state remained authenticated. Existing tests cover deadlines already past on the client, but do not exercise a smaller positive clock offset or repeated expiry callbacks. This is simulated timing evidence, not a real timed browser run.
**Suggested fix:** Ensure automatic deadline handling cannot repeatedly renew idle activity because the device clock is ahead. Gate private content at the deadline and require deliberate user activity before further renewal, or use a server-aligned time basis with conservative expiry behavior. Add a clock-skew regression that advances a motionless page past 30 server minutes and proves automatic callbacks do not keep extending its idle lifetime.
**Resolution:** Builder repair, pending fresh independent review. The expiry watcher now ends the local session without an API call, clears private React identity and the deadline, cancels pending work and discards deferred rechecks. Late responses cannot restore cleared identity. Deliberate navigation, visibility return, refresh/startup and retry may still revalidate; backend expiration remains authoritative. Fake-clock regressions cover normal/ahead/behind clocks, equality, post-expiry actions, no repeated requests or renewal loop, and pending session/login/logout responses. The user separately observed local identity clearing, no expiry-triggered session requests/polling/repeated requests, safe deliberate revalidation and rejection of late responses in development and production preview. The user reported exact guarded cleanup of reserved synthetic users/sessions. Clock-skew checks remain automated simulations, not live browser expiration proofs. The original audit evidence above is preserved; this fixed status is not reviewer closure. A fresh passing current review remains required.

**Independent re-review (2026-11-07):** Closed at checkpoint 4250092b58e8a73048e879fe00e9f4025cfd5d9b. Reviewed frontend/src/sessionState.js:121 and endSession, SessionContext.jsx's watcher lifecycle, RequireSession's guest gate, all frontend callers and regression tests. Deadline handling only calls endSession; it cannot call getSession or a mutation. endSession aborts active work, clears identity/deadline/busy state and deferred checks, and stale-result ownership prevents late restoration. The reviewer reran all 63 focused session cases and all 125 frontend cases successfully, including normal/+5/-5-minute fake clocks, equality, no further calls over nine hours, explicit post-expiry revalidation, pending session/login/logout cancellation and obsolete timers. This independently supports removal of the renewal loop without a new defect in this repair. The separately recorded user-performed focused development/preview observations support local clearing and absence of expiry-triggered requests; they were not repeated or observed by this reviewer. Clock-skew evidence remains automated simulation; native server expiry evidence is reused separately. The original explanation, reproduction and builder notes remain historical above. This closure does not resolve F-01 or constitute a passing feature receipt.

**Independent preservation review (2026-11-07):** Remains closed at checkpoint c3391f30d9139034f89550609274be2fe87bea48. Re-examined watchExpiry/endSession, provider timer cleanup, all session callers and the private gate while reviewing the complete new delta. Expiry still only clears local state, aborts active work and discards deferred checks; it performs no network request. Request ownership rejects late results, and obsolete timers cannot clear a deliberately renewed session. The current 108 focused/170 full frontend passes include normal/+5/-5-minute fake clocks, equality, nine hours without renewal, deliberate post-expiry actions and pending session/login/logout cancellation. These remain automated simulations. F-02 application behavior was unchanged by the encoded-path repair; earlier native expiry/locking evidence and user-performed browser reports are reused with their original boundaries. No PostgreSQL connection, native rerun, reviewer browser execution or full real 30-minute idle observation occurred in this pass. No regression or new finding was identified.

**Independent ancestry re-review (2026-11-07):** Remains closed at merge checkpoint 29122e55d5eae32f22dc8c977c7ce872e556473d. Fresh source review confirms watchExpiry calls only endSession, which aborts active work, discards deferred checks and clears local identity/deadline. Provider cleanup cancels obsolete timers; request ownership rejects late results. All 170 frontend tests passed, including normal/ahead/behind fake clocks, equality, no renewal over nine simulated hours and pending session/login/logout cancellation. The merge did not change this behavior. Backend application/tests, SQL and dependency manifests exactly match fefa4b2, permitting reuse of the recorded 87 guarded native passes and cleanup evidence. No PostgreSQL connection, native rerun, server/browser startup or full real 30-minute idle observation was performed by this reviewer. F-02 remains explicitly closed; F-03 below concerns inaccurate README wording only.

**Independent README-checkpoint re-review (2026-11-08):** Remains closed at af562929d28ceb704bebc918eeb395f6bab2465a. Fresh review of watchExpiry/endSession, provider effect cleanup, recheck/mutation ownership and the private gate confirms that expiry performs local clearing and cancellation only. No timer branch calls an API or schedules a renewal/retry. Late responses cannot restore cleared identity, and deliberate navigation/visibility/retry is still server-validated. All 170 frontend tests passed, including normal/ahead/behind fake clocks, equality, nine simulated idle hours, pending session/login/logout cancellation and obsolete timers. PostgreSQL validity and capped extension remain unchanged. Fake clocks are simulations; historical native and user-browser reports were reused only after applicable-code equality checks. No native rerun, reviewer browser execution or repeated real 30-minute idle observation occurred.

### 2/F-03 [P3] closed - README still describes an expiry-triggered session recheck

**File:** README.md:143
**Found:** 2026-11-07 by /audit independent (scope: current; lens: quality)
**Why it matters:** The current frontend description groups the known expiry boundary with navigation and visibility session rechecks. The repaired watchExpiry in frontend/src/sessionState.js:122 performs local identity clearing without a request. The README therefore describes the activity-extending behavior that F-02 deliberately removed and conflicts with the verified contract and browser guide. This is documentation drift; current application behavior and the F-02 repair remain correct.
**Suggested fix:** Replace the two-sentence passage with: "Session restoration uses GET /api/auth/session on startup; protected navigation and visibility return revalidate before displaying private content. At the known local expiry boundary, the app clears private identity without an API request." Keep the following loading/unavailable description. No behavior change is needed.
**Resolution:** Confirmed in the fresh merge-checkpoint review; left open and unaccepted. README and frozen source/spec/browser evidence were not edited. Nonblocking P3.

**Independent closure (2026-11-08):** Closed at af562929d28ceb704bebc918eeb395f6bab2465a after fresh review of the complete current delta and the committed README-only repair. README.md:143-155 now says the known local deadline clears React identity without calling /api/auth/session, the timer does not poll/retry/extend idle activity, later deliberate actions may validate with the server, and PostgreSQL determines actual idle/absolute expiry. This agrees with watchExpiry/endSession, provider timer cleanup, recheck/resume/enter and backend lock/time/expiry SQL. The original inaccurate passage is gone; no behavior change or new documentation defect was introduced. The reviewer reran 170 frontend tests, 360 database-free backend tests, pip check, lint/build and whitespace checks successfully. Historical receipt/findings were excluded from the README commit and their preserved raw hashes were verified. No acceptance on the user's behalf, source/spec/status/browser-record edit, native rerun or browser execution was performed. F-03 is explicitly closed by this independent review.


## Independent review

Original source: `blueprint/context/review.md`. Preserved verbatim; historical status text retains
its original target and evidence boundaries.

~~~~markdown
# Independent Review

**Status:** passed
**Target commit:** af562929d28ceb704bebc918eeb395f6bab2465a
**Base commit:** 4153c5a4a2d9c8ba6e19c75b9a485257ec413811
**Base ref:** refs/remotes/origin/main
**Spec hash:** b65e2da5acc0e6dac2755f3e8657459bbbceabb05ca1b07c189bef64b030cf8a
**Prepared by:** codex
**Builder model:** unknown (runtime did not expose exact model)
**Requested reviewer:** codex
**Requested model:** gpt-6.1-sol
**Requested execution:** automatic
**Requested at:** 2026-11-08T04:43:33.967453+00:00
**Workflow:** regular
**Check required:** no

**Reviewer adapter:** codex
**Reviewer model:** gpt-6.1-sol
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-08T04:49:14Z
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** passed
**Check result:** not-required

## Handoff

Review the active specification and complete 4153c5a4a2d9c8ba6e19c75b9a485257ec413811..af562929d28ceb704bebc918eeb395f6bab2465a delta in a generic
fresh isolated subagent without the builder conversation. Follow the installed
project-local Audit skill and independent-review contract across all four lenses.
Existing findings are context, not the scope. Independently reconsider F-03:
README now documents local expiry identity clearing without a session request,
no timer polling/retry/idle renewal, later deliberate server validation, and
PostgreSQL authority for idle/absolute deadlines. Confirm F-01/F-02 remain closed.
The one-file checkpoint excludes the previous receipt/findings. Their exact
historical bytes remain in ignored feature-2-f03-readme-repair backups and hashes.
The spec/source/config/test/browser-evidence bytes are unchanged from the approved
ancestry merge. Do not edit source, tests, README, spec/status/config, accept
findings, stage, commit/amend, complete, merge, push, deploy or install.
Write only findings.md, review.md and prescribed ignored activity. Do not start
a server/browser or connect to PostgreSQL. Adequate native/browser evidence may
be reused only as explicitly historical/user-provided evidence, not new reviewer
execution. Malformed direct HTTP paths were rejected by Vite before React loaded;
no React browser coverage or repeated full 30-minute real idle observation is
claimed. Fake clocks remain simulations. Run required appropriate database-free
checks and record actual commands, reused evidence and unavailable signals.

## Commands

- `node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js`: passed, 170 cases, zero failures/cancellations/skips/todo. This includes all 108 session cases; no separate focused rerun is claimed. Output was limited with PowerShell Select-Object. Used the prescribed fnm Node 22.23.4 installation on PATH for Node/npm commands.
- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider`: passed, 360 cases, 87 native cases deselected, one existing Starlette/AnyIO deprecation warning. No PostgreSQL connection or native test was run.
- `backend/.venv/Scripts/python.exe -m pip check`: passed, no broken requirements.
- `npm --prefix frontend run lint`: passed.
- `npm --prefix frontend run build`: passed on the prescribed require_escalated retry, Vite 6.4.5, 51 modules. The first sandbox attempt failed with esbuild's parent-directory access denial; that attempt was an environment failure, not a passing build.
- `git diff --check 4153c5a..HEAD`, `git diff --check`, and `git diff --cached --check`: passed. Working/index whitespace checks also passed after writing the receipt and ledger. Expected LF-to-CRLF notices are not whitespace failures.
- Read-only Git branch/status/ref/merge-base/parent/path/blob comparisons and Python raw-byte/SHA-256 verification: passed. HEAD, base, spec, README proposal and both preserved historical audit hashes match. All 128 baseline files outside README and the two audit records are unchanged.
- Targeted source/test searches and reads: completed. An initial rg invocation used literal wildcard paths unsupported by Windows; directory-based searches were used afterward. Only the two explicit native opt-in pytest skips were found; no focused/skipped/todo frontend tests or placeholder tests were found.
- Dashboard helper: initial start could not find Node; the retry with the prescribed PATH succeeded, and the milestone update succeeded. No manual activity-file write was used.
- Final read-only Python validation: passed for receipt identity/execution/required sections, all three closed finding headers, exact target/base/spec, allowed dirty paths and frozen baseline hashes.

## Evidence

- A generic fresh isolated Codex subagent, exact runtime-selected model gpt-6.1-sol, performed this review without the builder transcript. Review instructions came from the installed project-local Audit skill and independent-review contract. Adapter/model/automatic execution match the pending request; valid project configuration makes Check manual, so Check was not required or executed.
- HEAD is af562929d28ceb704bebc918eeb395f6bab2465a on feature/sign-in-sign-out-and-protect-private-sessions. Its parent is 29122e55d5eae32f22dc8c977c7ce872e556473d. The locally recorded origin default is refs/remotes/origin/main; it resolves to 4153c5a4a2d9c8ba6e19c75b9a485257ec413811, exactly the re-derived merge base. The complete reviewed range is 4153c5a4a2d9c8ba6e19c75b9a485257ec413811..af562929d28ceb704bebc918eeb395f6bab2465a.
- The tracked specification is verified with all seven steps checked. Its exact raw SHA-256 is b65e2da5acc0e6dac2755f3e8657459bbbceabb05ca1b07c189bef64b030cf8a and its bytes equal the target Git blob. No Spec snapshot field exists or is needed. Only findings.md and review.md differ from target, with no staged or other untracked paths.
- Verified the last checkpoint changes README.md only. Its raw hash and Git blob match checkpoint-proposal.json. Historical review/findings are excluded from that commit and preserved in ignored blueprint/.state/staging/feature-2-f03-readme-repair/historical-review.md and historical-findings.md; both hashes match proposal and commit metadata. Those historical records were context, never a substitute for this review.
- Reviewed the full 49-path current inventory across quality, security, performance and tests. The two audit records were excluded from application-code scope. All other 47 paths were covered: .gitignore, README, public environment examples and local launcher notes; backend authentication/config/main/routes/schemas/security/session/user modules; native guard/fixture/manual-launcher helpers and every added/changed backend test; active spec, authentication evidence and browser guide; all added/changed frontend pages/provider/private gate, shared route descriptor, API/credential/session helpers, styles and tests. Nearby unchanged database/health helpers, SQL session schema/indexes, registration callers, BrowserRouter entry, Vite proxy and dependency/pytest configuration were inspected as needed.
- Quality/security: credential normalization and verification stay shared and secret-safe, public identity comes from a validated database session, mutations check exact Origin/JSON/custom marker before body parsing and business writes, cookie issuance/deletion share attributes, and auth responses/errors remain sanitized with no-store. SQL values are bound; locks precede PostgreSQL time samples, validity predicates remain strict, extension is capped, replacement/cleanup are scoped, and pre-commit preparation preserves rollback/cookie boundaries. Health remains public/read-only and startup creates no schema. No new blocking defect was identified.
- Performance: examined short indexed session lookups, transaction/lock lifetime, bounded frontend requests, cancellation and stale-result ownership, timer cleanup, no idle-renewal loop and user-scoped invalid-session cleanup. No confirmed performance issue was found; no profiling or production-scale claim is made. Test review covered meaningful contract/error assertions, transaction ordering/rollback, native ownership/cleanup and bounded row-lock coordination, plus frontend path/history/failure/expiry cases. Native tests were deselected deliberately, not counted as new passes.
- F-01 remains closed: App rendering and navigation classification use the same accountRoute through public matchRoutes, with RequireSession gating unvalidated navigation and visibility. F-02 remains closed: watchExpiry invokes only endSession, which clears identity/deadline, aborts active work and discards deferred checks. Current tests cover encoded/literal paths, direct load/refresh, reused-key history, rejection/unavailability, stale responses, normal/ahead/behind fake clocks and pending mutations. No new regression was found.
- F-03 is explicitly closed by this review: README now accurately distinguishes local expiry clearing without a request from later deliberate server validation and PostgreSQL authority over actual idle/absolute deadlines. Reviewed the committed wording against watchExpiry/endSession, enter/resume/recheck, provider cleanup and backend lifetime SQL. No application repair was made by this reviewer.
- Reused historical native evidence only: AUTHENTICATION_STATUS.md records the November 6 final 87-case guarded native run and exact synthetic user/session cleanup. Read-only Git comparisons prove backend application/tests, authoritative SQL and dependency manifests are unchanged from fefa4b242047a0a18c02228963db3344ef2ce4fa through this target. This reviewer made no database connection, reran no native test and did not reobserve cleanup.
- Reused user-performed browser evidence only: original November 6 Chrome 156.0.8078.73 development/preview report, separately bounded repair observations, and November 7 Chrome 156.0.8078.73 encoded-route follow-up. Frontend/spec/verification records exactly match c3391f30d9139034f89550609274be2fe87bea48 through this target. November 7 malformed direct HTTP requests were rejected by Vite before React loaded, proving only that server boundary. React malformed-path checks and fake-clock results are automated simulations. Simulated rejection/unavailability and restored real-fetch 200 recovery remain distinguished. No repeated full real 30-minute idle observation, reviewer browser execution, new accessibility/layout measurement or deployed HTTPS proof is claimed.
- Applied project proportional-engineering, React/FastAPI organization, direct psycopg/parameter binding, secret-safe response/logging, transient accessible forms/session state, guarded tests and approval rules. Dependencies, dist/cache/bytecode, private environments, vendored/minified output and unrelated directories were excluded. No source/test/README/spec/status/config/browser-record edit, install, staging, commit/amend, completion/archive, merge, push, deployment or server/browser startup occurred. Only findings/review and prescribed ignored activity were written.

## Findings

- F-03 [P3] closed after independent examination of the committed README repair and actual expiry/server lifetime behavior.
- F-01 [P1] closed and F-02 [P1] closed remain explicitly closed at this target after fresh full-scope review. No P0/P1 finding is open or fixed, and no new confirmed finding was identified across the four lenses. No repair order remains.

## Remaining risk

- The opt-in native integration command was not rerun under the explicit no-database boundary. Historical 87-case results and cleanup are applicable unchanged-code evidence; they do not establish current database availability.
- No server/browser startup or new browser verification was authorized. User reports remain attributed; no full real 30-minute idle run was repeated, and timed eight-hour browser expiry, browser clock skew and deployed HTTPS remain unproved. Vite malformed-HTTP rejection is not React browser coverage.
- Node mock timers remain experimental simulations and the backend has the existing Starlette/AnyIO deprecation warning. No configured combined Verify, typecheck or browser-harness command exists. No runtime profiling or network-backed dependency vulnerability scan was run; npm audit requires network approval and was not invoked. Pip consistency and local source/manifest review do not provide those unavailable signals.
- Production login rate limiting and deployed HTTPS/cookie verification remain explicit later deployment/security decisions. The minimal account/session slice does not establish authorization for future resource routes.
- Frozen spec/status/browser documents retain historical pending-review statements by design. This receipt and findings ledger are the current audit state. A later target/code/test/config/spec change makes this receipt stale and requires a fresh checkpoint review.
~~~~

## Verification evidence

Original source: `docs/verification/AUTHENTICATION_STATUS.md`. Preserved verbatim; historical status text retains
its original target and evidence boundaries.

~~~~markdown
# Authentication verification status

Feature 2: Sign in, sign out, and protect private sessions.

Current checkpoint: `4250092b58e8a73048e879fe00e9f4025cfd5d9b` contains the
first F-01/F-02 repair. Its fresh audit independently closed F-02 but left F-01
open for encoded account paths. The subsequent F-01-only correction passed
automated checks and the user's November 7, 2026 Chrome 156.0.8078.73 development
and production-preview observations. The active specification is verified for
the proposed final F-01 repair checkpoint, not independently approved. F-01
remains open; the previous receipt and ledger remain unchanged and historical.
The receipt is stale for the new code/specification. No final F-01 repair is
staged or committed. Explicit checkpoint approval and a fresh passing
`$audit independent current` receipt remain required. Historical sections retain
their original evidence boundaries; the final F-01 follow-up at the end is the
current status. No `$complete` has run.

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

## Final F-01 encoded-path repair: November 7, 2026 browser follow-up

This section records the user's focused report after the remaining encoded-path
repair. It supersedes pending-browser status for this correction only. Earlier
automated/native results, browser reports and independent findings retain their
own targets and classifications. No independent audit was run in this recording
pass, and no application code was changed while recording these observations.

### Previous independent audit remains historical

Reviewed checkpoint: `4250092b58e8a73048e879fe00e9f4025cfd5d9b`.
Reviewed specification SHA-256:
`e050b64b673f684f61709ad2365670ea4ca86c64e7a8c6d7bd976129e4127aad`.
Reviewer: Codex gpt-6.1-sol, fresh isolated subagent. Verdict: changes-requested.
F-01 stayed open because encoded routes bypassed navigation revalidation; F-02
was independently closed because local expiry could no longer renew idle time.

The current review.md and findings.md are preserved byte-for-byte, including
the original explanations, repair notes and independent re-review evidence:

- Receipt raw SHA-256: `1c9615addaf7fe49fff8b98b2e10fec7609a8d12cbd6cf94223b27fcb56cc882`.
- Findings raw SHA-256: `26021c0c3cb6f39872fb882b4dd54306b8a1252a1edc9604fd482831e2645256`.

The receipt is stale for the new implementation/specification. F-01 remains
open until a fresh independent audit confirms this repair. The user's browser
report does not close the finding. F-02's recorded independent closure remains
historical evidence; its application code was unchanged in this correction.

### Existing automated results, not rerun for this documentation pass

The November 7 encoded-path repair introduced a shared Account route descriptor
used by App.jsx and sessionState.js. Public matchRoutes now supplies the same
decoding and matching semantics as route rendering, without a custom decoder.
Encoded navigation/history regressions first reproduced the defect with the old
matcher, then passed with the correction.

| Previously run repair check | Actual result |
| --- | --- |
| `node --test frontend/tests/sessionState.test.js` | 108 passed, zero failures. |
| `node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js` | 170 passed; zero failures, cancellations, skips or todo cases. |
| `npm --prefix frontend run lint` | Passed. |
| `npm --prefix frontend run build` | Passed; 51 modules. Approved outside-sandbox retry after the known esbuild parent-directory denial. |
| `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider` | 360 passed, 87 native cases deselected. |
| `backend/.venv/Scripts/python.exe -m pip check` | No broken requirements found. |
| Scoped whitespace checks, including new accountRoute.js | Passed; rechecked during final checkpoint preparation. |

Node's experimental mock-timer warning and the existing Starlette/AnyIO
deprecation warning remain. Backend application/tests, authoritative SQL and
dependency manifests were not changed by this repair. No PostgreSQL connection,
native test or agent cleanup was run in the repair or this documentation pass.
Earlier guarded native evidence remains separate and is not relabeled as new.

### User-performed browser observations

Date: November 7, 2026. Browser: Google Chrome 156.0.8078.73. Environments:
Vite development and production preview. The agent did not perform or observe
these browser interactions; the following results are the user's report.

| User-reported check | Observation |
| --- | --- |
| `/account`, `/account/`, `/ACCOUNT`, `/%61ccount`, `/acc%6Funt`, `/%41CCOUNT` | All required session validation before displaying Account identity. |
| Encoded direct loads, refresh and Back/Forward | Worked as expected. |
| Valid protected navigation | `/api/auth/session` returned 200; identity stayed hidden until validation completed. |
| Rapid navigation and late responses | Stale session work was canceled; stale responses did not restore outdated content. |
| Simulated rejected sessions | Private content stayed hidden and entered the login/session-ended flow. |
| Simulated unavailable sessions | Account stayed gated with deliberate retry. |
| Restored real fetch and Try again | Valid session restored only after a fresh 200 response. |
| `/accounting`, `/account/settings` and encoded unrelated paths | Did not display Account content. |
| Direct malformed HTTP paths | Vite rejected them with URI malformed before React loaded; GarageGuide worked normally afterward. |
| Deliberate Back/Forward session checks | Expected user-driven activity, separate from prohibited expiry polling. |
| Guarded backend cleanup | Exact reserved synthetic account/session absence message observed. |

The user reported:

```text
Verified cleanup: all reserved synthetic accounts and sessions are absent.
```

The cleanup marker is user-performed browser-backend evidence, not a new agent
SQL verification. Rejected/unavailable responses were simulations; restored
real-fetch 200 recovery is reported separately. Vite's URI malformed rejection
is a development/preview-server boundary observation, not React browser
coverage for malformed paths. React matcher/store malformed-path coverage is
automated only. No full 30-minute real idle-expiration observation was repeated
for this focused F-01 report. Do not infer browser clock-skew, eight-hour expiry,
new responsive/accessibility measurements or deployed HTTPS coverage here.

### Proposed final F-01 checkpoint and unrelated local work

Branch: `feature/sign-in-sign-out-and-protect-private-sessions`.
Parent HEAD: `4250092b58e8a73048e879fe00e9f4025cfd5d9b`.
Proposed message: `fix: align protected navigation with router decoding`.

Exactly nine files are proposed (eight modified tracked files and one new file):

| File | Purpose |
| --- | --- |
| `frontend/src/accountRoute.js` (new) | The actual Account route descriptor shared by rendering and classification. |
| `frontend/src/App.jsx` | Render Account from that shared descriptor. |
| `frontend/src/sessionState.js` | Use public matchRoutes with the shared descriptor for decoding-consistent navigation checks. |
| `frontend/tests/sessionState.test.js` | Encoded/literal route, refresh/history/failure/stale-response and malformed-path regressions. |
| `blueprint/context/current-feature.md` | Verified implementation/browser-progress record with F-01 still open and fresh audit pending. |
| `docs/verification/BROWSER_CHECKS.md` | Record attributed observations and the malformed-server/idle-expiration limitations; retain the repeatable guide. |
| `docs/verification/AUTHENTICATION_STATUS.md` | Separate final F-01 automated, user-browser, simulated and historical audit/native evidence. |
| `blueprint/context/review.md` | Preserve the unchanged previous changes-requested receipt in checkpoint history. |
| `blueprint/context/findings.md` | Preserve the unchanged ledger with F-01 open and F-02 independently closed. |

The two audit records already differed from HEAD before this preparation;
including their exact existing bytes preserves the previous review in history.
The original and first-repair proposals remain untouched. New ignored artifacts:

- blueprint/.state/staging/feature-2-final-f01-checkpoint-proposal.json
- blueprint/.state/staging/feature-2-final-f01-review-packet.md
- blueprint/.state/staging/feature-2-final-f01-review.diff

Each proposed file has a frozen raw SHA-256 and Git-normalized blob hash in the
manifest, along with the specification hash, parent and predicted tree. The
predicted tree is HEAD plus only these nine files, computed without staging.

An unrelated local edit in backend/prepapp.txt was discovered and left untouched.
It is explicitly excluded from this checkpoint and its review diff. It must be
resolved by a separate user decision before a later independent audit can meet
its clean-target rule. Do not silently stage, stash, discard or commit it. Its
presence does not turn it into an approved repair file.

The index remains empty. Private backend/.env and backend/.env.test remain
ignored, untracked and unstaged; no dependency, virtual environment, node_modules,
build output, cache, dump or schema is proposed. Nothing has been staged,
committed/amended, audited, completed, merged or pushed in this pass. Explicit
approval is still required before staging or committing the exact candidate.
~~~~

The following browser document is a repeatable guide with separately attributed
user reports. Instructions and simulation shims are not additional execution
evidence. The final reviewer did not run a browser or repeat real idle timing.

## Browser guide and observation boundaries

Original source: `docs/verification/BROWSER_CHECKS.md`. Preserved verbatim; historical status text retains
its original target and evidence boundaries.

~~~~markdown
# Manual browser verification

Feature 1 Step 4 browser checks were completed by the user on November 4, 2026
in Google Chrome 156.0.8078.73, in development and production preview, with
verified synthetic-record cleanup. The reported observations are recorded in
[registration verification](REGISTRATION_STATUS.md), separately from automated
and native backend tests. No browser-control tool or configured browser harness
was available to the agent. The instructions below remain the repeatable manual
guide; unreported individual checks are not additional observed evidence. Keep
historical scaffold evidence separate.

Feature 2 Step 4 adds login, session restoration, protected account routing, and
logout. Its automated/backend/native checks do not replace browser observations.
The user's November 6, 2026 report in Chrome 156.0.8078.73 covers development,
production preview, authentication, registration/CSRF, failure behavior,
accessibility and responsive layouts, with the exact cleanup marker. Those
observations are recorded in AUTHENTICATION_STATUS.md. The instructions below
remain repeatable guidance; unreported cases are not additional browser passes.

## Guarded test backend and Vite

Run from the repository root. Stop any ordinary backend on port 8000 first.
Use the existing initialized `garageguide_app_test` and private
`backend/.env.test`; do not edit or display credentials. Exported PostgreSQL
variables override that file, so remove unintended overrides privately.
Do not initialize databases or run schema scripts for these checks.

The test launcher now also requires the explicit authentication keys from
`backend/.env.test.example`, including `AUTH_ENVIRONMENT=testing`,
`AUTH_COOKIE_SECURE=false`, `AUTH_API_ORIGIN=http://127.0.0.1:8000`, and empty
`AUTH_FRONTEND_ORIGIN`. Add only missing auth keys privately; do not overwrite
database settings or display credentials. An invalid configuration stops startup.

The exact non-secret keys are below. Add only missing keys to the appropriate
private file yourself; the agent has not inspected or edited those files.
Do not replace their PostgreSQL credentials or copy the development database
name into test configuration. Browser verification stays pending until the test
auth keys are configured. Environment overrides must agree with testing mode.

For `backend/.env` (ordinary development, not the browser verification backend):

```dotenv
AUTH_ENVIRONMENT=development
AUTH_COOKIE_SECURE=false
AUTH_API_ORIGIN=http://127.0.0.1:8000
AUTH_FRONTEND_ORIGIN=
```

For `backend/.env.test` (the guarded browser verification backend):

```dotenv
AUTH_ENVIRONMENT=testing
AUTH_COOKIE_SECURE=false
AUTH_API_ORIGIN=http://127.0.0.1:8000
AUTH_FRONTEND_ORIGIN=
```

In a dedicated PowerShell terminal:

```powershell
$previousRunDbTests = $env:RUN_DB_TESTS
try {
  $env:RUN_DB_TESTS = '1'
  backend/.venv/Scripts/python.exe backend/tests/manual_registration_server.py
} finally {
  if ($null -eq $previousRunDbTests) {
    Remove-Item Env:RUN_DB_TESTS -ErrorAction SilentlyContinue
  } else {
    $env:RUN_DB_TESTS = $previousRunDbTests
  }
}
```

The test-only launcher requires the test database in settings, verifies
`SELECT current_database()` once as the first statement of each new connection,
checks existing schema read-only, and reserves three unique, initially absent
synthetic emails. Wait for Uvicorn to report listening on `127.0.0.1:8000`.
Use **only those three printed emails**, called A, B, and C below. Reservation
does not insert accounts. Other emails are rejected before user queries by
this test-only launcher; that restriction is not normal product behavior.
Access logging is disabled. Passwords and credentials are never printed.
Login/session/logout operations are restricted to the same reserved users and
their sessions. The launcher verifies session ownership before session writes;
its final cleanup covers both users and sessions. Only `/`, `/register`, `/login`,
and the protected `/account` are application pages.

Before recording the new registration contract as passed:

1. Use the exact development/preview addresses shown below. On a real registration
   with a reserved email, inspect only the required header names/values and safe
   status: browser Origin matches port 5173 or 4173, Content-Type is JSON, and
   X-GarageGuide-CSRF is 1. Expect committed 201, then normalized duplicate 409;
   repeat invalid-form/error clearing, focus, pending state, and password clearing.
2. Confirm authentication responses carry Cache-Control: no-store. Do not copy
   request bodies, cookie values, full header dumps, or populated-secret screenshots.
3. With the guarded backend, this empty logout request deliberately omits the
   marker and must return fixed 403 without changing a session:
   `fetch('/api/auth/logout', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, body: '{}'}).then(r => r.status)`.
   Missing/null/malformed/untrusted Origin cases are covered by native tests;
   do not weaken browser security or attempt to set the forbidden Origin header.
4. Record new observed results and final exact cleanup in AUTHENTICATION_STATUS.md.
   The earlier November 4 report remains historical evidence for Feature 1.

In another terminal, use the existing fnm Node installation (22.12+). If Node
is absent from PATH, enable this project's current installation for this terminal:

```powershell
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
npm --prefix frontend run dev
```

Use disposable synthetic passwords entered directly into the form. Do not
inspect/copy request payloads, export HAR files, enable request-body logging,
paste passwords in the console, or take screenshots while password fields are
populated. Inspect request method, URL, status, timing, and public responses only.
Do not save passwords in browser storage or password-manager prompts. A
browser's own password manager is separate from application state.

## Connection button and routes

1. Open `http://127.0.0.1:5173`. Confirm the initial ready-to-check message.
2. Tab to **Check connection**, confirm visible keyboard focus, then press Enter.
3. Confirm **Checking…** appears and the button is disabled during the request. Browser network throttling can make this short state easier to observe.
4. Confirm **Connected. GarageGuide is ready.** Developer tools should show `GET /api/health/db` returning HTTP 200 with `status: ok`, `database: connected`, and `schema: ready`.
5. Confirm requests use the frontend origin, contain no database credentials, and produce no console errors.
6. Confirm `/api/health` still returns 200. Use **Create account** to reach
   `/register`, with focus on its heading. Use header links between both routes;
   Network's Document filter should show no page reload for those links.
7. Directly load and refresh `/register`. Exercise Back/Forward and full-document
   departure/Back. After leaving a populated form, returning must show empty
   passwords. `/` and `/register` remain public; `/login` is also public, while
   `/account` must confirm a valid server session before showing account content.

## Form validation and real registration

1. Navigate using only the keyboard. Check visible focus, associated labels,
   masked password inputs, and a readable requirements hint. With a screen
   reader, check field descriptions/errors and pending/result announcements.
2. Submit empty fields. Expect field errors and focus on email. Correct a field
   and confirm its obsolete error clears; resubmit and check stale feedback clears.
   Inspect `aria-invalid` and `aria-describedby` associations.
3. With A, exercise 14/15/128/129 NFC-normalized Unicode code-point boundaries,
   astral characters, equivalent composed/decomposed Unicode, preserved spaces
   and case, and mismatch. Test invalid cases first. For accepted boundary cases
   before creating A, use simulated network mode below to avoid creating accounts.
4. Restore real transport. Submit a nonempty invalid email with valid matching
   passwords. Expect actual 422 containing only safe `loc`, `msg`, and `type`
   entries, email focus/error, no raw input, and retained temporary password state.
   Correct email; its stale error must clear. Browser email constraints must not
   override the server's agreed email-validation contract.
5. Submit A with surrounding whitespace and uppercase letters, plus valid
   matching synthetic passwords. Expect one relative `POST /api/auth/register`,
   then 201 with exactly `id`, normalized lowercase `email`, and timezone-aware
   `created_at`. Existing native backend tests separately establish committed
   persistence and hashing. Confirm no session cookie/token or sign-in redirect,
   **Account created successfully.**, focus on success feedback, and empty
   password fields. Remain on `/register`.
6. Re-enter passwords and submit the normalized variant of A again. Expect 409
   and **An account with this email already exists.**, focus on email, and
   passwords retained only in current component state. Correct email to B;
   confirm its stale error clears. Do not submit B yet.
7. During pending, confirm **Creating account**, announced status, disabled
   fields/button, and no duplicate POST from repeated click/Enter. The timeout
   simulation below makes pending easy to observe.

## Deterministic failure simulations (no database request)

Record these as **simulated** UI checks, separately from real HTTP/native
evidence. This console snippet does not inspect, log, or save request bodies.
It stores only mode, count, and a restore function. Paste it once on `/register`:

```javascript
(() => {
  const originalFetch = window.fetch.bind(window)
  const check = { mode: 'network', calls: 0 }
  check.restore = () => {
    window.fetch = originalFetch
    delete window.registrationCheck
  }
  window.registrationCheck = check
  window.fetch = (resource, options) => {
    if (resource !== '/api/auth/register') return originalFetch(resource, options)
    check.calls += 1
    if (check.mode === 'network') return Promise.reject(new TypeError())
    if (check.mode === 'timeout') {
      const signal = options.signal
      return new Promise((resolve, reject) => {
        const abort = () => reject(new DOMException('', 'AbortError'))
        if (signal.aborted) abort()
        else signal.addEventListener('abort', abort, { once: true })
      })
    }
    const status = check.mode === '503' ? 503 : check.mode === 'malformed' ? 201 : 500
    const body = status === 503
      ? { detail: 'Registration unavailable. Please try again.' }
      : status === 500 ? { detail: 'Internal server error' } : {}
    return Promise.resolve(new Response(JSON.stringify(body), {
      status, headers: { 'Content-Type': 'application/json' },
    }))
  }
})()
```

Enter B and valid matching synthetic passwords directly into the form:

1. With `registrationCheck.mode = 'network'`, submit. Expect a generic
   connection error and retained passwords, with no application logs.
2. Set `registrationCheck.mode = 'timeout'; registrationCheck.calls = 0`.
   Submit once and attempt repeated click/Enter during pending. After about 10
   seconds, expect the timeout warning that an account may already have been
   created. Passwords remain for deliberate retry. Inspect
   `registrationCheck.calls`: it must be 1 and stay 1 after another 10 seconds.
   No automatic POST retry occurs. Cancellation cannot undo a server commit.
3. Set `registrationCheck.mode = '503'`. Submit; expect unavailable feedback,
   re-entry instruction, focus on feedback, and both password fields cleared.
4. Repeat with `registrationCheck.mode = 'unexpected'` (500), then
   `registrationCheck.mode = 'malformed'` (invalid 201 body). Expect generic
   unexpected feedback and cleared passwords, never raw response details.
5. In timeout mode, submit and navigate to `/` while pending. Return with links
   and Back/Forward. Passwords must be empty, with no late feedback from the
   abandoned request. Repeat departure after a correctable error.
6. Run `registrationCheck.restore()` before real requests. Submit B successfully
   if desired to check recovery. Refresh also removes the mock.

## Responsive foundation

1. Use device emulation at widths of 375, 768 and 1440 pixels, then resize between them.
2. Confirm no horizontal scrolling, clipped text, overlaps or inaccessible controls. On mobile, the button sits beneath the status; wider layouts place it alongside.
3. Repeat at 200% zoom and navigate by keyboard. Confirm readable text, visible focus and reachable controls. Status must be understandable without relying on color.
4. Repeat with the longer unavailable message. Record which browsers and sizes were actually checked.

## Connection retry, preview, and verified cleanup

1. At `/`, use browser Offline mode, press **Check connection**, and expect
   unavailable feedback and enabled **Try again**. Restore Online and retry;
   expect success without refresh. Do not modify private database configuration
   or stop a shared PostgreSQL service to simulate an outage.
2. Stop Vite dev with Ctrl+C, keep the guarded backend running, then run:

   ```powershell
   npm --prefix frontend run build
   npm --prefix frontend run preview
   ```

3. At `http://127.0.0.1:4173`, repeat direct loads/refresh of both routes, Link
   navigation/history, connection check, invalid form feedback, and clearing
   after departure. Use C for real 201 and duplicate 409 checks. Repeat important
   responsive/keyboard/failure checks. Dev and preview must proxy relative API
   requests to the guarded backend. Production rewrites are a later feature.
4. Restore any fetch mock, stop preview, then Ctrl+C the guarded backend. Wait
   for this exact message before recording a pass:

   ```text
   Verified cleanup: all reserved synthetic accounts and sessions are absent.
   ```

Cleanup recovers IDs by exact reserved email and sessions by those owned user IDs,
deletes sessions by exact ID/user ID/token hash and users by exact ID/email,
commits, then verifies absence on a separate guarded connection. Never
force-kill the launcher during cleanup. If the marker is missing, do not record
a pass or continue native testing. Retain only the printed fixture-email list
and resolve those exact fixtures; never use broad deletion, truncate/reset, or
write to `garageguide_app`. Sequence gaps are expected. Record safe outcomes
and the verified-cleanup marker in `REGISTRATION_STATUS.md`.

## Feature 2 Step 4 session walkthrough — instructions

These are instructions; the user's reported results are recorded separately in
AUTHENTICATION_STATUS.md. Configure the non-secret test auth
keys above first. Use a fresh run of the guarded backend with its new printed
A/B/C emails for this walkthrough. If you already consumed those emails in the
earlier detailed registration checklist, stop that launcher, wait for verified
cleanup, and start a new one. Do not reuse old fixture identities across runs.

Use a clean disposable browser profile, plus an independent Incognito/profile
cookie jar for the second browser. Two Incognito windows in the same profile can
share cookies and do not prove independent sessions. Decline password-manager
storage. Do not view/export cookies, request payloads, HAR files, populated-secret
screenshots, or authentication data in console logs.

1. At `http://127.0.0.1:5173`, check the connection screen and both public health
   endpoints. Direct-load/refresh `/register` and `/login`; use Link navigation
   and Back/Forward. With no cookie, direct-load `/account`: it must show the
   session check, then `/login` with safe feedback and no account email/content.
2. At `/register`, check labels, empty/invalid input, stale-error clearing,
   focus, keyboard operation, pending lock, and the existing password lifecycle.
   Register A using a disposable password entered only into the form. Expect 201,
   success feedback and cleared passwords. Reuse normalized A for 409. Confirm
   JSON, the browser's exact Origin, custom CSRF header and same-origin URL, and
   no-store responses without exposing payloads or cookie values.
3. At `/login`, check labeled email/current-password autocomplete and field
   descriptions/errors. Empty fields and invalid Unicode length must focus the
   first invalid field. Enter an invalid email to exercise a real sanitized 422;
   fix it and confirm the error clears. Try A with a wrong valid-length password,
   then the still-unregistered reserved C with a valid-length password: both must
   display exactly the same invalid-credentials message. Passwords remain transient
   after those correctable failures. Do not use an unreserved email: the manual
   launcher deliberately rejects it rather than querying an unrelated account.
4. Sign in as A correctly. Expect one POST, cleared password, `/account`, email A,
   the public session deadline, and Sign out. Direct-load/refresh `/account`:
   no private content appears until GET session succeeds. Leave/return via a
   public page and via tab visibility. Inspect only safe request metadata; a new
   GET must validate the session before private content returns. No periodic
   polling should occur just to keep the idle session alive.
5. In the independent cookie jar, sign in as A. Sign out in the first browser:
   expect one POST, empty 204, no private UI, and `/login`. Back/Forward and direct
   `/account` must not restore account content. In the second browser, refresh
   `/account`: A remains signed in. In the first browser, repeat logout safely
   with this empty, secret-free request; it must return 204:

   ```javascript
   fetch('/api/auth/logout', {
     method: 'POST', credentials: 'same-origin',
     headers: {'Content-Type': 'application/json', 'X-GarageGuide-CSRF': '1'}, body: '{}'
   }).then(response => response.status)
   ```

6. In the first browser, sign in as A again, register B, then use `/login` to
   switch to B. The account page must show B only. The independent browser must
   still show A after revalidation. A failed login attempt while B is signed in
   must preserve B's valid session; use the Account link to confirm. No vehicle,
   dashboard, editing, role or device-management functionality should appear.
7. Use the simulated failures below for login/logout pending state and safe
   feedback, and for unavailable/protected 401 behavior. Also block only the
   `/api/auth/session` request in browser Network request blocking and refresh
   `/account`. The page must show unavailable/retry, not a successful logout or
   private content. Unblock it and press Try again: the real valid cookie can
   restore B. Do not stop PostgreSQL or alter database credentials for this check.
8. Restore real fetch and remove request blocking. For real idle expiration,
   keep the account page visible without navigating or returning from a hidden
   tab for at least 30 minutes after the last valid activity. At its known
   deadline it must clear private React identity and route to login with the
   safe session-ended message, without sending GET session or any other request
   that extends idle activity. It must not poll or retry automatically afterward.
   Deliberate navigation, visibility return, refresh/startup or retry may
   revalidate; server expiration remains authoritative.
   Native tests separately prove the eight-hour absolute cap and strict equality.
   To claim an actual eight-hour browser observation, keep a fresh session active
   through deliberate visits less than 30 minutes apart until eight hours from
   login, then verify rejection despite that activity. If not performed, record
   absolute-cap evidence as native only; never invent an eight-hour browser pass.
9. At 375, 768 and 1440 CSS pixels, and at 200% zoom, check all four pages and
   loading/unavailable/error states for wrapping and absence of horizontal scroll.
   Use keyboard-only navigation, visible focus, associated labels/errors,
   first-error/feedback focus, polite pending announcements and error alerts.
   If no screen reader is used, distinguish inspected ARIA from a spoken-output
   observation. Never capture a screenshot with populated password fields.
10. Stop only Vite dev (Ctrl+C), keeping the guarded backend alive. In the frontend
    terminal run the exact commands below, then open `http://127.0.0.1:4173`:

    ```powershell
    $env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
    npm --prefix frontend run build
    npm --prefix frontend run preview
    ```

    Repeat direct loads/refresh/history, login success/failure, restoration,
    unavailable/retry, logout/back safety, keyboard/zoom/responsive checks, and
    registration validation/clearing. Use C for preview registration 201/duplicate
    409 only after the earlier unknown-account test. Preview Origin is exactly
    http://127.0.0.1:4173. Test the independent cookie jars again as appropriate.
11. Restore all mocks and blocking, sign out test browsers, stop preview, then
    Ctrl+C the guarded backend and wait for:

    ```text
    Verified cleanup: all reserved synthetic accounts and sessions are absent.
    ```

    The launcher commits exact owned-record cleanup and independently verifies
    absence. Do not force-kill it or claim cleanup if this message is absent.
    Record new dated results, browser version, dev/preview cases, simulations,
    pending cases and the cleanup marker in AUTHENTICATION_STATUS.md. Keep the
    November 4 registration report as historical evidence, without overwriting it.

### F-01/F-02 repair browser checks and reported observations

The user subsequently reported completing focused repair verification in both
development and production preview. The report confirms /account, /account/,
/ACCOUNT, unrelated /accounting, protected history, rejected/unavailable gating,
local expiry without session requests or polling, deliberate revalidation,
late-response rejection, logout/isolation, focus, announcements and responsive
layouts. The exact synthetic account/session cleanup marker was reported.
See the separate follow-up in AUTHENTICATION_STATUS.md. No agent browser or
database check, reviewer closure, clock-skew browser run, exact timing or
unreported route/viewport case is inferred. The checklist below remains the
repeatable guide; its entire contents are not a claim of observed coverage.
The earlier November 6 Chrome report describes the original checkpoint.
Reuse only the guarded test-backend setup and reserved synthetic
accounts above, in both development and production preview. Keep all request
payloads, passwords and cookie values out of logs, screenshots and exports.

1. Sign in, then navigate from a public page to `/account`, `/account/`,
   `/ACCOUNT` and `/AcCoUnT/`. Use direct loads/refresh and browser Back/Forward
   as well. Each protected navigation must check the session before displaying
   account identity. `/accounting`, `/accounts` and `/account/settings` must not
   render Account or be classified as the protected account route.
   For each variant, direct-load it while signed in, leave using the Connection
   check Link, then use Back to return to the original variant and Forward to
   leave again. This exercises cached identity and reused history keys; an
   address-bar reload alone does not test that cache boundary.
2. With cached identity, repeat variant navigation using the existing session
   failure shim below: simulated 401 must show the safe login flow, while
   unavailable/network/503 must show the unavailable gate and deliberate retry.
   No cached email may flash or remain visible. Delayed session responses from
   an earlier navigation must not overwrite a later rejection or account switch.
   Restore real fetch and remove blocking before testing real sessions.
3. Repeat the real visible idle check in item 8. Watch only safe Network request
   metadata, then keep the page visible without navigating or changing tab
   visibility. At the displayed local deadline the account must disappear and
   the session-ended login notice must appear. There must be no expiry-triggered
   GET, POST or follow-up retry, including after waiting past the deadline.
4. After local expiration, deliberately navigate to an account variant, refresh
   or return from a hidden tab. Gate identity until the new check succeeds;
   server rejection must stay guest and availability failure must stay gated.
   Repeat unavailable/retry, logout and Back/Forward, account switching and
   independent-browser isolation. An aborted/delayed pre-expiry response must
   not restore expired identity.
5. Check focus, announcements, keyboard operation and responsive/zoom behavior
   for the changed loading, unavailable and session-ended transitions. Stop the
   guarded backend normally and record its exact synthetic user/session cleanup
   marker before reporting a browser pass.

The automated fake-clock tests cover normal time, five minutes ahead and five
minutes behind, equality, stale responses and the absence of an idle-extension
loop. Those are simulations, not browser evidence. Device clock skew can change
when local UI hides; only PostgreSQL decides whether a session is valid. Do not
claim these client tests prove a real 30-minute or eight-hour server boundary.

### Encoded-path F-01 browser verification and reported observations

The November 7 encoded-path correction uses matchRoutes with the same Account
descriptor rendered by App.jsx. The user reported focused verification on
November 7, 2026, using Chrome 156.0.8078.73 in both Vite development and production
preview. All six listed account variants validated before identity appeared;
encoded direct loads/refresh/history, valid 200 responses, stale-work cancellation,
simulated rejection/unavailability and real-fetch retry recovery passed. Unrelated
paths showed no Account content, and exact guarded cleanup was reported.
Direct malformed HTTP paths were rejected by Vite with URI malformed before
React loaded. That is server-boundary evidence, not React browser coverage.
Deliberate history requests are user activity, not automatic expiry polling.
The user did not repeat a full 30-minute real idle observation; F-02 application
code was unchanged. See AUTHENTICATION_STATUS.md for the full attributed report.
F-01 remains open pending a fresh independent audit. The guide below is retained
for repeatability; its entire checklist is not a claim of observed coverage.

Use the existing guarded backend restricted to garageguide_app_test and its
reserved synthetic accounts. Repeat in development (127.0.0.1:5173) and production
preview (127.0.0.1:4173), rebuilding preview first. Do not use the development
database, export requests/cookies, log passwords or capture populated secrets.

1. Sign in, then direct-load and refresh each of `/account`, `/account/`,
   `/ACCOUNT`, `/%61ccount`, `/acc%6Funt` and `/%41CCOUNT`. Expect the checking
   gate before Account appears, then only the server-confirmed account email.
   Inspect safe Network metadata to confirm each navigation/refresh revalidates.
2. For each encoded variant, leave via the Connection check Link, then use Back
   to return and Forward to leave. This preserves the encoded history entry and
   exercises cached React identity; address-bar reload alone does not test that
   boundary. Restore valid identity, leave again, then use the failure shim
   below with `authCheck.path = 'session'` and `authCheck.mode = 'rejected'`.
   Back must gate cached content and redirect to login without displaying email.
3. Repeat with `authCheck.mode = 'unavailable'` and with network failure. Account
   must remain gated and offer deliberate retry. Restore real fetch before
   pressing Try again; only a successful fresh check may restore identity.
   Check loading/unavailable focus and announcements with keyboard navigation.
   Record shim failures as simulations, not actual revocation or database outage.
4. With session requests throttled or held pending, navigate away from one
   encoded entry and return through another; let the earlier request finish
   after a newer rejection, logout or account switch. It must not restore the
   earlier identity. Repeat logout and Back/Forward for the encoded entries.
5. Open `/accounting`, `/account/settings` and encoded unrelated variants such
   as `/%61ccounting` and `/%61ccount/settings`. No Account content may appear.
   Open malformed paths `/%`, `/acc%ount`, `/account%` and `/%E0%A4%A`.
   In development/preview Vite may reject the direct request with URI malformed
   before React loads. Record that server boundary separately; it does not prove
   React's handling of malformed locations. React-level malformed-path behavior
   is covered by the automated matcher/store tests, not by that direct HTTP result.
6. Optional F-02 preservation check, not repeated in this focused report:
   while an encoded Account entry stays visible and idle,
   local expiry must clear identity and show the safe login flow without a
   session request, polling or automatic retries. A late response must not undo
   the cleared state. Deliberate later navigation/visibility/retry may revalidate.
   Record actual idle duration separately; fake-clock tests are simulations.

Restore every shim/blocking rule, sign out the test browsers and stop the guarded
backend normally. Require the exact marker before recording a browser pass:

```text
Verified cleanup: all reserved synthetic accounts and sessions are absent.
```

Report the browser/version, dev/preview cases, visible results, simulation modes,
idle duration and cleanup observation. Do not infer server-expiration or browser
coverage from unit tests, or close F-01 based on this guide alone.

### Safe session failure simulations

This browser-only shim intercepts one selected auth path without reading,
retaining, or logging request bodies or cookie values; it uses the abort signal.
It never sends the matched
request to the database while a failure mode is active. Other paths still reach
only the guarded backend. Restore it before real tests. A simulated 401 does
not actually revoke or delete a server cookie and is not proof of real expiration.

```javascript
(() => {
  const originalFetch = window.fetch.bind(window)
  const check = { path: 'login', mode: 'off', calls: 0 }
  check.restore = () => { window.fetch = originalFetch; delete window.authCheck }
  window.authCheck = check
  window.fetch = async (resource, options) => {
    if (resource !== '/api/auth/' + check.path || check.mode === 'off') {
      return originalFetch(resource, options)
    }
    check.calls += 1
    if (check.mode === 'network') throw new TypeError('Simulated network failure')
    if (check.mode === 'timeout') {
      return new Promise((resolve, reject) => {
        const abort = () => reject(new DOMException('Aborted', 'AbortError'))
        if (options?.signal?.aborted) abort()
        else options?.signal?.addEventListener('abort', abort, {once: true})
      })
    }
    if (check.mode === 'malformed') return new Response('invalid JSON', {status: 200})
    const outcomes = {
      forbidden: [403, 'Request not allowed.'],
      unavailable: [503, check.path === 'register' ?
        'Registration unavailable. Please try again.' : 'Authentication unavailable. Please try again.'],
      unexpected: [500, 'Internal server error'],
      rejected: [401, check.path === 'login' ? 'Invalid email or password.' : 'Not authenticated.'],
    }
    const [status, detail] = outcomes[check.mode] ?? outcomes.unexpected
    return new Response(JSON.stringify({detail}), {status, headers: {'Content-Type': 'application/json'}})
  }
})()
```

- For login, set `authCheck.path = 'login'`. Exercise network, timeout, forbidden,
  unavailable, unexpected, malformed and rejected modes. Timeout must last about
  ten seconds with one POST and disabled repeated submission. Network/timeout/
  rejected feedback retains only temporary form passwords; 403/503/500/malformed
  responses clear them. After every departure/return, passwords must be empty.
- For logout, select `authCheck.path = 'logout'`. Network/timeout/503 must show
  safe retry feedback without claiming logout or dropping the prior public session.
  The sign-out button must prevent repeats while pending. Restore the shim and
  deliberately retry to prove real 204 behavior.
- For protected availability, select `authCheck.path = 'session'` and an unavailable,
  network, timeout or malformed mode, then leave/return to Account or regain tab
  visibility. Private content must remain gated with deliberate Try again. Restore
  real transport and retry. A rejected mode must instead clear private React state
  and go to login; record it as a simulation, then reconcile through the real API.
- Registration's earlier simulation section remains valid. To use this shim for
  its 503/500/network/timeout cases, select `authCheck.path = 'register'`. Restore
  either shim before using the other; do not layer them.
- Finish with `authCheck.restore()`. Record counts/modes/statuses only, without
  copying credentials or cookie values. Build output and these instructions do
  not count as observed browser acceptance.
~~~~
