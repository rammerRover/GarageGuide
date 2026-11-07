# Feature: Sign in, sign out, and protect private sessions

**From build-plan:** feature 2
**Build attempt:** 1
**Branch:** feature/sign-in-sign-out-and-protect-private-sessions
**Archive path:** blueprint/history/features/02-sign-in-sign-out-and-protect-private-sessions.md
**Status:** verified
**Independent-review gate:** required; checkpoint commit approval and a current passing receipt are still pending. Verified here means implementation and final checks, not independent-review approval or feature completion.

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
- Recheck when returning to a protected page or regaining visibility, and at the
  known expiry boundary. Until revalidation, gate potentially stale private
  content. Server time remains authoritative; client timers never grant access.
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
