# Feature: Register a user account

**From build-plan:** feature 1
**Build attempt:** 1
**Branch:** feature/register-a-user-account
**Archive path:** blueprint/history/features/01-register-a-user-account.md
**Status:** verified
**Independent review:** passed for checkpoint ab831c9cea3c173804447cbecb0ae68cc3244dcc; post-review status edits remain uncommitted and require freshness reconciliation before completion.

## Goal

A visitor can open `/register`, submit an email and matching password fields,
and create one account in the existing PostgreSQL `users` table. Provide clear,
accessible success and safe error feedback without creating a session.

Build Steps 1-4 are approved, including the user's November 4, 2026 browser
verification. Step 5's automated/native verification and builder diff review
passed. The user approved one 30-file local checkpoint with message
`feat: add user account registration` solely for independent audit. Implementation
verification and the independent audit are complete. Step 5 is complete and
awaits the user's final approval. The fresh reviewer returned a passing receipt
with no confirmed findings for checkpoint
`ab831c9cea3c173804447cbecb0ae68cc3244dcc`. Post-review status documentation remains
uncommitted as requested. Stop before `$complete`; do not archive, merge, push,
deploy, begin Feature 2, make audit fixes, or create another commit.

## In scope

- A public synchronous `POST /api/auth/register` with Pydantic request/response
  models, `SecretStr` password fields, shared normalization, and Argon2 hashing.
- Direct parameterized psycopg queries, duplicate-email detection and race
  protection, short transactions, rollback, cleanup, and bounded waits.
- React Router navigation between `/` and `/register`, with an accessible
  registration form and explicit pending, success, validation, and error states.
- Database-free tests, opted-in native tests with synthetic fixtures and exact
  cleanup, manual browser checks, and registration-specific evidence.
- During implementation, align test-policy documentation with the approved
  once-per-writable-connection database check. Step 2 has aligned the README
  and coding standards with the implemented guard and cleanup fixtures.

## Out of scope

- Sign-in/out, session tokens/cookies, expiry/revocation, private authorization,
  and authenticated-request CSRF decisions belong to Feature 2.
- Login/protected routes, password reset, email verification/delivery, account
  deletion, vehicle/catalog features, and deployment.
- Django, SQLAlchemy, SQLModel, Tortoise ORM, Alembic, automatic schema creation,
  schema changes, fixture SQL scripts, pooling, and async database conversion.
- A frontend test runner, CI, a combined Verify command, or unrelated dependencies.

## Build loop

- After approval, `$implement` uses the exact branch above and builds one step
  at a time. Do not implement from `$feature`.
- `workflow.stepReview: every` requires approval after each step's checks.
  `checkpointCommits: enabled` permits offering optional checkpoints after
  approval; it does not authorize a commit.
- Run the configured backend Test gate for logic and lint/build for frontend
  work. There is no combined Verify or Browser tests command.
- `$check` and `$audit current` are manual under current configuration.
  Registration selects the `when-sensitive` independent-review gate: use
  `$audit independent current` after implementation verification, following the
  installed isolated-reviewer flow or its manual fallback. Any review checkpoint
  commit requires separate explicit approval.
- Use `$check guide` for the configured Try it now handoff and offer the final
  read-only code walkthrough. A guide does not prove behavior.
- `$complete` owns final gates, archival, the final feature commit, and separately
  approved landing. Current approval covers Step 5 final verification, including
  native tests guarded to `garageguide_app_test` and independent review. The user
  subsequently approved exactly one local checkpoint containing the 30 reviewed
  paths, with the exact message `feat: add user account registration`. No further
  commits or audit fixes are approved. Stop for approval before `$complete`;
  archival, merge, push, deployment, schema changes, and Feature 2 remain prohibited.

## Build steps

- [x] 1. Add credential schemas and validation/hashing helpers.
  Declare the approved backend dependencies during implementation. Implement the
  exact email order below. Type both password fields as `SecretStr`; unwrap only
  in the credential-validation helper, normalize NFC, validate length/matching,
  and return only an Argon2 hash. Add focused tests with safe representations.
  **Done when:** the database-free Test command passes email-order tests,
  SecretStr masking tests, password boundaries at 14/15/128/129 normalized code
  points, astral-character counting, NFC equivalence, matching/mismatch,
  preserved spaces/case, and real hash verification. Imports do not connect to
  PostgreSQL or expose plaintext.
  **Observed validation:** the configured database-free Test command passed
  59 tests (53 new credential/schema cases and 6 existing cases), with the one
  integration test deselected. `pip check` passed. No PostgreSQL connection was
  made during Step 1. Step 1 has since been approved by the user.

- [x] 2. Add writable database access and safe native-test fixtures.
  Reuse small connection setup while retaining read-only health behavior. Add
  parameterized user queries and transaction ownership. Reject unsafe test
  settings before connection; check `SELECT current_database()` once immediately
  after opening every writable native-test connection, including endpoint and
  cleanup connections. Register exact fixture cleanup before writes.
  **Done when:** database-free tests prove parameter binding, rollback/close,
  settings rejection, one actual-name check before the first write on each
  connection, no repetition before subsequent statements, and failure without
  writes when verification fails. Opted-in native checks demonstrate persistence
  visible from a second connection and verified cleanup of only test-owned rows.
  If the existing test database/schema is unavailable, stop without provisioning.
  **Observed validation:** 82 database-free cases passed, with 5 integration
  cases deselected. The 4 targeted native Step 2 tests passed against guarded
  `garageguide_app_test`, including committed persistence, sequential duplication,
  rollback/recovery, lost-response cleanup, and native read-only mode. Per-test
  teardown verified absence of the reserved synthetic records. See
  `docs/verification/REGISTRATION_STATUS.md`. No API endpoint or schema changes
  were made during Step 2; the user has since approved that step.

- [x] 3. Expose the registration API and sanitize failures.
  Register the synchronous auth router and safe validation-error boundary.
  Unit-test normal duplicates and `psycopg.errors.UniqueViolation` translation,
  including a unique violation after a successful precheck. Translate the email
  constraint only after rollback; preserve generic handling of other failures.
  **Done when:** the database-free Test command passes the API/redaction contract
  and existing health tests. Required native tests show a successful 201 followed
  by a sequential duplicate 409 with exactly one account, valid stored hashing,
  committed persistence, failure recovery, and verified fixture cleanup. A real
  simultaneous duplicate-request test is optional hardening, not a gate.
  **Observed validation:** the full database-free suite passed 113 cases,
  including 31 registration API cases, with 12 integration cases deselected.
  The guarded native suite passed all 12 cases: 7 registration API cases,
  4 Step 2 query/transaction cases, and the existing database health case.
  Native tests verified committed 201 responses, normal and forced-constraint
  duplicate 409 responses, sanitized validation, rollback before 503 and retry,
  no session/cookie creation, and verified synthetic-record cleanup. Logs contain
  only fixed registration failure messages without exception details. See
  `docs/verification/REGISTRATION_STATUS.md`. The user has since approved Step 3.

- [x] 4. Add React Router and the registration interface.
  Add `react-router-dom` with npm during implementation, updating both
  `frontend/package.json` and `frontend/package-lock.json`. Mount `BrowserRouter`
  once in `main.jsx`; define `/` and `/register` using `Routes`/`Route` in
  `App.jsx`, with `Link` navigation. Keep the connection screen at `/` and add
  `Register.jsx` at `/register`. Add no login/protected routes. Extend the existing
  API helper and CSS with the interaction contract below.
  **Done when:** lint/build pass and browser evidence confirms links, direct
  loads, refresh, Back/Forward, keyboard/focus behavior, Unicode validation,
  submission states, and layouts near 375/768/1440 pixels in dev and preview.
  Correctable failures retain only temporary React password state; success and
  leaving the page clear both fields, including when navigating back afterward.
  **Observed validation:** `react-router-dom` 7.18.5 is installed and locked;
  no existing dependency version changed. Frontend lint and production build
  passed. All 121 database-free backend cases and 12 guarded native cases passed,
  including verified exact cleanup. Fifteen mocked API-helper smoke checks
  passed, including the actual 10-second timeout and cancellation, without
  browser/database requests. Eight new database-free tests cover the guarded
  manual backend launcher. The agent had no browser tool or configured harness
  and did not start a dev server. The user subsequently completed manual checks
  on November 4, 2026 in Google Chrome 156.0.8078.73: development routing,
  direct loads, refresh, links, Back/Forward, connection check/retry, registration
  validation, field-error clearing, focus, keyboard operation, real 201 success,
  normalized-email 409, pending duplicate prevention, and safe network/timeout/
  503/500/malformed-response simulations all passed. Password retention after
  correctable failures and clearing after success/navigation passed. Layouts
  passed at 375/768/1440 pixels without horizontal scrolling; development and
  production preview checks passed. The user reported the final backend message:
  `Verified cleanup: all reserved synthetic accounts are absent.` Detailed
  user-reported evidence is in `docs/verification/REGISTRATION_STATUS.md`;
  manual steps remain in `docs/verification/BROWSER_CHECKS.md`. The user has since
  approved Step 4 and authorized Step 5 final verification.

- [x] 5. Verify and record the complete registration slice.
  Run applicable checks and the manual walkthrough using the guarded test
  backend and synthetic fixtures. Record new registration results in the proposed
  `docs/verification/REGISTRATION_STATUS.md`; link existing evidence without
  copying historical results. Run the selected `$audit independent current`
  workflow before the final implementation review packet.
  **Done when:** required checks have observed evidence, cleanup is verified,
  and remaining limitations are explicit. Native persistence cannot be accepted
  from mocks or the prior successful connection check. An unavailable native
  prerequisite stops verification without changing development data.
  **Observed Step 5 validation (November 4, 2026):** the complete database-free
  suite passed 121 cases (12 integration cases deselected), and the guarded
  native suite passed 12 cases (121 database-free cases deselected). All native
  cleanup finalizers passed: exact reserved ID/email pairs were deleted and
  absence was verified on separate guarded connections. `pip check`, frontend
  lint, production build, and whitespace checks passed. Build required an
  approved retry outside the sandbox after an access-denied configuration read.
  Builder review covered all 30 changed/untracked feature paths. No application
  behavior changed, so no additional browser repetition is required by this
  pass; the user's earlier browser report remains a separate evidence source.
  **Independent-review prerequisite:** `$audit independent current` Phase A requires
  an approved committed application-code checkpoint, a verified spec, and a
  matching working tree. At initial preflight, HEAD and the local `main` merge base were both
  `bd763da52ba52c07f3fad3200cccade663dbe756`, the pre-feature baseline; 14 tracked
  modifications and 16 untracked feature files differed from it at preflight.
  The user has now approved one local checkpoint, resolving the permission
  blocker. The approved checkpoint was created with exactly 30 files and the
  requested message. Staged-file checks excluded private environments, credential
  files, dependencies/build output/caches, and generated plaintext test secrets;
  `git diff --cached --check` passed. A fresh isolated Codex `gpt-6.1-sol` reviewer
  then reviewed the exact checkpoint across quality, security, performance, and
  tests, returning `passed` with no confirmed findings. The builder validated
  target/base/spec hash and receipt fields before these status edits. The reviewer
  reran 121 database-free tests, pip check, frontend lint/build, and whitespace;
  it explicitly reused Step 5 native results and the user's browser report.
  No fixes or further commits are authorized. Step 5 is complete, pending final
  user approval; `$complete` remains prohibited. See
  `docs/verification/REGISTRATION_STATUS.md` for complete results and the exact
  proposed checkpoint candidate.

## Files / areas

| File or area | Planned responsibility |
| --- | --- |
| `backend/requirements.txt` | Add `pwdlib[argon2]`, `email-validator`, and an explicit Pydantic requirement compatible with FastAPI. Choose compatible pinned versions during implementation. |
| `backend/app/schemas.py` (new) | Request with two `SecretStr` fields, public response, and shared email processing. |
| `backend/app/security.py` (new) | Sole credential-unwrapping boundary, NFC validation/matching, and Argon2 hashing without returning plaintext. |
| `backend/app/database.py` | Small read-only/writable connection setup with finite waits; preserve health checks. |
| `backend/app/user_queries.py` (new) | Parameterized account lookup/INSERT and transaction-aware results. No generic repository framework. |
| `backend/app/routes/auth.py` (new), `backend/app/main.py` | Synchronous registration, router wiring, and safe error handling. |
| `backend/tests/conftest.py`, `database_support.py` (new in Step 2) | Test settings, once-per-connection database verification, schema preconditions, unique fixture ownership, unconditional cleanup, and stopping on cleanup failure. |
| `backend/tests/test_schemas.py`, `test_security.py` (Step 1); `test_database_access.py`, `test_user_queries_integration.py` (Step 2) | Existing schema/credential and query/transaction/guard/cleanup coverage, retained alongside the Step 3 API tests below. |
| `backend/tests/test_registration.py`, `test_registration_integration.py`, `registration_support.py` (new in Step 3) | HTTP status/serialization/redaction/transaction tests, guarded native API persistence and cleanup, and test input/output protection. |
| `backend/tests/manual_registration_server.py`, `test_manual_registration_server.py` (new in Step 4) | Manual browser backend restricted to the guarded test database and reserved synthetic emails, with verified cleanup on shutdown; database-free launcher safety tests. No application/backend behavior changes. |
| `frontend/package.json`, `frontend/package-lock.json` | Add and lock `react-router-dom` using npm. |
| `frontend/src/main.jsx`, `App.jsx`, `Register.jsx` (new), `api.js`, `styles.css` | Router, two pages, navigation, form state, requests, and accessibility. |
| `frontend/vite.config.js` | Verify existing SPA fallback and API proxy; no speculative configuration changes. |
| `blueprint/context/coding-standards.md`, `README.md` | Step 2 aligns older per-write guard wording with the approved per-connection policy and documents native-test instructions. |
| `docs/verification/BROWSER_CHECKS.md` | Add the registration walkthrough during implementation. |
| `docs/verification/REGISTRATION_STATUS.md` (created in Step 2) | Separate Step 2/3 results, Step 4 automated/user-browser evidence, and Step 5 checks, cleanup, checkpoint inventory, passing independent receipt, limitations, and post-review freshness. Existing records retain their provenance. |

`react-router-dom` is the approved new frontend runtime dependency. Select a
version compatible with existing React/Node; avoid unrelated upgrades. Pydantic
already exists through FastAPI, but new direct imports warrant an explicit
requirement. Keep pytest/httpx in the existing development requirements and tool
settings in `pyproject.toml`. No schema changes are planned. The registration
verification record contains separate observed query, API, and frontend automated
results. Step 4 added exactly `react-router-dom` 7.18.5 as a direct dependency;
its three transitive packages are locked without unrelated version changes.
The registration interface and Step 4 verification are complete. The user's
manual browser results are recorded separately from agent-run automated checks.
Step 4 is approved. Step 5's checks and independent checkpoint audit passed.
No findings or audit fixes were recorded. Final user approval remains pending;
the post-review status edits are intentionally uncommitted.

## Data / contracts

### Request and credential processing

- Accept JSON with required string fields `email`, `password`, and
  `password_confirmation`. Model both password fields as Pydantic `SecretStr`.
  Only accepted typed fields may supply insert values; client IDs, timestamps,
  or hashes cannot control stored account data. Server validation is authoritative.
- Process email in this exact order: trim surrounding whitespace; validate with
  Pydantic `EmailStr`; use the validator's normalized result; lowercase the final
  GarageGuide account identifier. Define one shared process and reuse it
  unchanged during future sign-in. Use the result for lookup, INSERT, and response.
  Do not rewrite provider-specific dots/aliases or perform mailbox delivery checks.
- Unwrap `password` and `password_confirmation` only inside the
  credential-validation helper. Routes, schema validators, query modules, and
  loggers must not unwrap them. Inside the helper, apply Unicode NFC to both
  values before length validation and comparison. Each normalized value must
  contain 15-128 Unicode code points inclusive; the normalized values must match.
  Reject malformed Unicode safely. Canonically equivalent values match.
- Preserve password case and leading/trailing/internal spaces. Do not trim,
  lowercase, truncate, or impose composition rules. The browser applies NFC and
  counts code points with `Array.from(value).length`; UTF-16 `.length` and native
  password `minlength`/`maxlength` must not define a different acceptance rule.
- Inside the credential-validation helper, hash only the normalized password
  using `pwdlib[argon2]` and library-generated salts. Return only its encoded
  Argon2 hash, never either plaintext value. Future sign-in must reuse NFC
  normalization before verification; sign-in is not implemented here.
- Passwords exist transiently only for entry, submission, validation, and hashing.
  Neither plaintext field may be returned, persisted, logged, exposed in debug
  representations, or included in test output. Store only `password_hash` in
  PostgreSQL; never store confirmation or plaintext in any database field.

### API and redaction

| Outcome | Status and body |
| --- | --- |
| Committed account | 201 with exactly `id` (integer), `email` (normalized string), and `created_at` (timezone-aware RFC 3339 string). PostgreSQL supplies ID and creation time. |
| Invalid/missing fields, mismatch, or malformed JSON | 422 with `detail` containing safe `loc`, `msg`, and `type` entries. Associate mismatch with `password_confirmation`. |
| Existing email, including a uniqueness race | 409 with `{ "detail": "An account with this email already exists." }`. The user approved account-existence disclosure. |
| Database availability failure or timeout | 503 with `{ "detail": "Registration unavailable. Please try again." }`. |
| Unexpected internal failure | Generic 500 without request content, SQL, driver details, passwords, or hashes. |

`SecretStr` masks model representations; it does not sanitize raw request
validation input. Independently sanitize failures before, during, and after model
construction. Build errors from fixed safe messages and whitelisted locations.
Never serialize raw error `input`, `ctx`, request bodies, or exception strings.
Missing-field errors can contain the entire request and require sanitization too.
Map unknown field names to a generic body location instead of reflecting input.

Preserve the `detail` envelope and existing health contracts. Log only safe
failure classes, never request/exception objects or credential values. The public
endpoint creates only the requested account and issues no session cookie/token.

### SQL, transactions, and connection lifetime

- Use existing `public.users` with database-generated ID/creation timestamp,
  unique normalized email, and `password_hash`. Numbered SQL remains authoritative;
  startup never creates or changes schema. Use synchronous handlers and psycopg.
- Normalize and hash before opening a short transaction. Use parameterized
  `SELECT id FROM public.users WHERE email = %s` for normal duplicate detection,
  followed by a parameterized INSERT of `email, password_hash` with
  `RETURNING id, email, created_at`. Never interpolate user values into SQL.
- The precheck cannot prevent races. Catch `psycopg.errors.UniqueViolation` for
  the `users.email` unique constraint and translate it to 409 after rollback.
  Verify its schema-derived constraint identity during native checks. Other
  integrity failures must not be mislabeled as duplicate email.
- Let failures leave the transaction/connection context to roll back and close
  before HTTP translation. Do not query an aborted transaction. Commit before
  returning 201; an insert or commit failure must never produce success.
- Retain the existing 3-second connect timeout and 3000-ms statement timeout.
  Keep health transactions read-only and registration writable. Use context-managed
  connections without global connections, pooling, or an ORM.
- Credentials remain in ignored backend environment files. Never send them to
  React, bundles, responses, logs, or verification artifacts.

### Native-test database guards and fixture cleanup

- Native tests require the `integration` marker, `RUN_DB_TESTS=1`, and effective
  database name exactly `garageguide_app_test`. Keep the settings-level rejection
  before connecting; tests load test configuration, never the development `.env`.
- Immediately after opening every writable native-test connection, execute
  `SELECT current_database()` once as its first database statement. Verify the
  exact name before exposing the connection or allowing its first write.
  This includes fixture, API-handler, and cleanup connections. Each new physical
  or replacement connection needs its own check. Wrong names or failed checks
  close the connection without writes.
- Reuse that verification for the connection's later statements/transactions.
  Do not query the database name before every write or every SQL statement.
  A small guarded connection fixture suffices; no write-interception framework
  is required. Read-only health checks remain read-only.
- Reserve unique synthetic addresses such as `gg-reg-<uuid>@example.com`, confirm
  initial absence, and register finalizers before the first possible insertion.
  Track exact test-owned IDs and reserved emails, including committed rows whose
  HTTP response failed. Recover missing IDs by exact reserved email when needed.
- Always run cleanup finalizers for setup, request, and assertion failures.
  Delete only exact test-owned ID/email pairs, then verify absence. Never delete
  by prefix, truncate tables, reset sequences/databases, or remove unrelated rows.
  Never write to `garageguide_app` or `postgres`; use doubles to test rejection.
- Cleanup connections need the same one-time guard. Guard failure prevents
  writes; cleanup failure fails the test and stops native testing until only
  tracked fixtures are resolved. A test cannot pass with unverified cleanup.
  Identity sequence gaps are expected and must not be reset.
- Do not provision or initialize a missing test database/schema. Stop and resolve
  that prerequisite separately. No fixture SQL scripts are required.
- This approved per-connection rule supersedes older per-write wording for this
  feature. Step 2 has aligned the README/coding-standards wording and executed
  only the separately authorized native checks against the guarded test database.

### Frontend routes and password lifetime

- Use `react-router-dom`: mount one `BrowserRouter` in `main.jsx`, define `/`
  and `/register` using `Routes`/`Route` in `App.jsx`, and navigate with `Link`.
  Keep `/` as the connection page. Add no login/protected routes or auth guards.
  Update both frontend package files during implementation. Verify Vite dev and
  preview SPA fallback for direct loads/refresh; production rewrites are Feature 15.
- Label email, password, and confirmation. Use password inputs with
  `autocomplete="new-password"` and email with `autocomplete="email"`. Explain
  requirements. Server email validation is authoritative; browser validation must
  not reject addresses accepted by the agreed email contract.
- Begin with an empty form. Associate errors with fields using `aria-describedby`
  and `aria-invalid`; announce results, focus the first invalid field, clear
  obsolete field errors on correction, and clear stale status on resubmission.
  Render user text using React escaping, never injected HTML.
- Announce submission and prevent duplicate submits. Send JSON to relative
  `/api/auth/register` with a bounded 10-second fetch timeout. Do not automatically
  replay a POST: a timeout can occur after a successful database commit.
- Handle 201, safe 422, 409, 503, network errors/timeouts, and unexpected/malformed
  responses. Validate the success fields before showing success. Retries require
  a deliberate user action.
- On success, announce `Account created successfully.`, clear both password
  fields, and remain on `/register`. Do not auto-sign-in or link to a missing
  sign-in route.
- Retain passwords only in temporary component React state after correctable
  validation failures, including an email correction after 409, or network
  failures/timeouts. Permit correction/retry without forcing re-entry in those
  cases. Clear both fields after other non-correctable/unexpected failures.
- Clear both password fields when leaving the page. Unmount/reset the form so
  links and browser Back/Forward cannot restore them. Keep no password state in
  shared context, persistent layouts, router navigation state, or caches. Ignore
  late request completions after departure; browser cancellation does not imply
  database rollback.
- Never put passwords in browser storage, URLs, logs, analytics, telemetry,
  screenshots, or evidence artifacts.

## Testing

These are the implementation gates. Step 3 passed the complete database-free
suite and guarded native suite, including HTTP registration, query regressions,
and database health. Step 1 passed its Python dependency check. Step 4 passed
lint/build and repeated both backend gates. The user reported passing manual
browser checks on November 4, 2026 in Google Chrome 156.0.8078.73, including
development/preview, responsive layouts, password lifetime, and verified cleanup.
These user observations are recorded separately from automated results.
Step 5 repeated the complete database-free/native suites, dependency consistency,
frontend lint/build, and whitespace checks. They passed. The independent audit
initially stopped at its immutable-checkpoint precondition. One local checkpoint
is now explicitly approved to enable that review; no receipt has yet been
produced at that point. The subsequent fresh reviewer passed the exact approved
checkpoint and reran 121 database-free tests, pip check, lint/build, and whitespace.
It reused the separately identified native and user-browser evidence. No new
application behavior invalidates the browser report.

### Independent audit receipt and post-review status

- Target: `ab831c9cea3c173804447cbecb0ae68cc3244dcc`; base ref `main`, merge base
  `bd763da52ba52c07f3fad3200cccade663dbe756`.
- Reviewed spec SHA-256:
  `a43ef1c401ea443209da8a55d8fdbc29785989c34f8d9161a62af921fcba258a`.
- Reviewer: Codex `gpt-6.1-sol`, automatic execution, fresh isolated subagent.
  Verdict: passed across all four lenses. Findings/severities/affected files:
  none. No repairs or finding acceptance was performed.
- Receipt: `blueprint/context/review.md`; evidence ledger:
  `blueprint/context/findings.md`. Both are uncommitted reviewer output.
- The receipt was validated while only its permitted evidence paths differed
  from HEAD. The user requested uncommitted Step 5 status updates after a pass;
  these edits change the spec hash and another tracked document. Under the
  installed strict contract, the receipt is therefore stale for this working
  tree while preserving the independent pass for the exact checkpoint. Do not
  call it a current completion receipt or silently change its recorded hash.
  Reconcile freshness under separately approved workflow actions before
  `$complete`; no second commit or re-review is authorized in this turn.

| Check | Command from repository root |
| --- | --- |
| Database-free Test | `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider` |
| Python dependency consistency | `backend/.venv/Scripts/python.exe -m pip check` |
| Frontend lint | `npm --prefix frontend run lint` |
| Frontend build | `npm --prefix frontend run build` |
| Native integration | With `RUN_DB_TESTS=1` and guarded `garageguide_app_test` only: `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider` |

- Required unit coverage: email order/shared helper; SecretStr types/masking;
  helper-only unwrapping; NFC/code-point boundaries; matching; preserved spaces
  and case; hashing/verification; bound SQL values; precheck duplicates;
  `UniqueViolation` email translation after rollback; unrelated constraint errors;
  commit/rollback/close failures; health regressions; and one actual-name check
  per writable native-test connection before its first write.
- Required native coverage: successful registration and stored hash, public
  response, persistence visible on another connection, and sequential normalized
  duplication returning 201 then 409 with one account. Verify rollback/recovery,
  test-connection guards, and cleanup after deliberately failed operations.
- Optional hardening: a real simultaneous duplicate-request test may be added
  only if simple and deterministic. It is not a completion gate. Database race
  protection and unit-tested unique-error translation remain mandatory.
- Required redaction coverage: missing email with both passwords present,
  malformed JSON, incorrect password types/lengths, mismatch, and database errors.
  Check absence of original/NFC plaintext in responses and captured logs. Use
  synthetic secrets, masked representations and test IDs, and safe boolean
  assertions. Failed tests must not dump bodies, error objects, request dictionaries,
  locals, or credential values into output or artifacts. SecretStr alone is insufficient.
- Manual browser coverage: guarded test backend/synthetic fixtures and verified
  cleanup; both routes and navigation/history; all form states; Unicode rules;
  keyboard/focus/live regions; dev/preview; responsive widths; retention after
  correctable failures; and clearing on success/departure/return. No frontend
  runner is installed incidentally.
- Add the walkthrough to `docs/verification/BROWSER_CHECKS.md` and new observed
  results to proposed `docs/verification/REGISTRATION_STATUS.md` during implementation.
  Link existing verification records without copying or relabeling historical results.

## Notes for the AI

- The user approved Steps 1-4 and authorized Step 5 final checks, guarded native
  tests only in `garageguide_app_test`, and independent review. All requested
  checks passed. The user subsequently approved one exact 30-file local review
  checkpoint with message `feat: add user account registration`. No audit fixes
  or further commits are approved. Do not waive or self-satisfy the independent
  gate. The approved checkpoint and independent audit are now complete; no
  findings were raised. The user-requested status edits remain uncommitted and
  make the receipt stale for the working tree, not for its historical checkpoint.
  Stop for approval before any further workflow action; do not run `$complete`,
  archive, initialize or alter schema, implement Feature 2, make audit fixes,
  create further commits, merge, push, or deploy.
- Preserve the frozen feature ID, first build attempt, branch, and archive path.
  Previous selection found no conflicting archive/history/branch. Recheck at
  implementation without silently renaming or allocating another attempt.
- No Django, ORM, migration framework, pooling, schema initialization, generic
  auth framework, or speculative repository abstraction. React Router is the
  explicitly approved routing dependency for multiple application pages.
- Direct-query persistence, transaction rollback/recovery, guards, and cleanup
  were verified in Step 2. HTTP registration, safe errors, committed persistence,
  session-free behavior, and guarded cleanup were verified in Step 3. The form
  is implemented; its manual browser evidence comes from the user's November 4,
  2026 report, separately from build/lint and mocked API checks. Preserve the
  provenance of prior evidence.
- No unresolved product choice prevents implementation after approval. Dependency
  compatibility and native test readiness are implementation checks, not permission
  to provision databases, change architecture, or proceed without required evidence.


<!-- blueprint:completion {"schemaVersion":2,"specBytes":34676,"specSha256":"ea868feef4fedccadf84ca54e81900c93b46d7cc3966f881485d7d75c828c85b","branch":"refs/heads/feature/register-a-user-account","head":"73f0b72801f903ce81ba7b8db7c69e7e68241919","baseRef":"refs/heads/main","baseCommit":"bd763da52ba52c07f3fad3200cccade663dbe756","sourceTree":"361260a1e9a557f94cd6334f0c2da69b30084039","landing":"local-merge","absentOptional":[]} -->

## Completion verification

Final completion checks were run November 6, 2026.

- Database-free backend suite: 121 passed, 12 integration cases deselected,
  1 existing Starlette/AnyIO deprecation warning; 6.53 seconds.
- Python dependency consistency: pip check reported no broken requirements.
- Frontend lint and production build passed; build transformed 43 modules.
  The sandbox denied the first configuration read; an approved retry passed.
- Whitespace and pre-archive safety checks passed. The current passing
  independent receipt was validated against its original target, base, raw
  spec hash, reviewer identity/execution, and permitted evidence differences.
- Native PostgreSQL results (12 tests with verified exact synthetic cleanup)
  are reused from the separately recorded November 4 Step 5 evidence. No
  database connection or write was performed during this completion pass.
- Browser evidence is the user-performed November 4, 2026 Chrome report,
  including the manual launcher cleanup marker; no browser run was repeated.
- No application code, schema, or dependencies changed during completion.
- Landing policy is local-merge. This archive preparation does not authorize
  a completion commit, merge, push, deployment, or Feature 2.

## Findings

No confirmed findings or finding IDs were recorded.

## Independent review

# Independent Review

**Status:** passed
**Target commit:** 73f0b72801f903ce81ba7b8db7c69e7e68241919
**Base commit:** bd763da52ba52c07f3fad3200cccade663dbe756
**Base ref:** main
**Spec hash:** ea868feef4fedccadf84ca54e81900c93b46d7cc3966f881485d7d75c828c85b
**Prepared by:** codex
**Builder model:** unknown (runtime did not expose exact model)
**Requested reviewer:** codex
**Requested model:** gpt-6.1-sol
**Requested execution:** automatic
**Requested at:** 2026-11-04T22:33:47.352Z
**Workflow:** regular
**Check required:** no
**Reviewer adapter:** codex
**Reviewer model:** gpt-6.1-sol
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-04T22:35:57.616280+00:00
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** passed
**Check result:** not-required

## Commands

- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider`: passed, 121 selected tests; 12 native cases deselected; one existing Starlette/AnyIO deprecation warning.
- `backend/.venv/Scripts/python.exe -m pip check`: passed, no broken requirements.
- `npm --prefix frontend run lint`: passed.
- `npm --prefix frontend run build`: passed on approved escalated retry after sandbox configuration-read denial; 43 modules, JS 234.62 kB (gzip 75.56 kB), CSS 2.46 kB (gzip 1.05 kB).
- `git diff main...HEAD --check` and `git diff --check`: passed.
- `git rev-parse HEAD`, `git merge-base main HEAD`, `git status --short`, tracked-spec and raw SHA-256 checks: passed checkpoint and freshness preconditions. Final freshness explicitly exempts only review.md and findings.md.
- Activity helper: initial invocation could not find Node; retried successfully with the existing fnm Node 22.23.4 on process-local PATH.

## Evidence

- Fresh isolated Codex reviewer with no builder or prior reviewer transcript reviewed the complete base-to-target feature delta from scratch across all four lenses, excluding review/findings as code inputs. Prior receipt notes were not a review checklist or evidence of a pass.
- Reviewed all 30 non-evidence changed paths: backend application registration/schema/security/database/query modules; all added/changed backend tests and native/manual support; frontend components/API/styles/entry point and both package manifests; README, coding standards, active spec, browser guide, and registration status record. Followed nearby settings, health, Vite, pytest, and authoritative users SQL contracts. Generated output, dependencies, caches, private environments, and unrelated project areas were excluded.
- Checked exact email/NFC/password contract, fixed-message error redaction, public response/session exclusion, SQL parameter binding, commit-before-success, rollback-before-translation, uniqueness protection, bounded waits, native guard and exact cleanup, routing, request cancellation, password lifetime, focus and live-region code against AGENTS.md and project coding standards.
- Reused evidence only: docs/verification/REGISTRATION_STATUS.md Step 5 records 12 native PostgreSQL tests passing and exact synthetic-record cleanup verified by all teardowns. No reviewer PostgreSQL connection, write, scan, or cleanup operation occurred.
- Reused evidence only: the user's November 4, 2026 Chrome 156.0.8078.73 report records dev/preview routing, registration states, keyboard/focus, registration validation, password lifetime, responsive widths 375/768/1440, and the manual launcher's verified-cleanup marker. Reviewer did not start servers or perform browser checks. Earlier 15 mocked API-helper smoke results are historical supporting evidence, not reviewer-run or browser evidence.
- All five build steps are checked and spec status is verified. main remains the permitted local base; current branch is feature/register-a-user-account. The tracked spec needs no ignored-spec snapshot.
- Frozen current-feature.md and REGISTRATION_STATUS.md bytes remained unchanged. Their historical receipt/staleness narrative remains historical; this new receipt binds the current checkpoint and exact frozen spec bytes.
- Test inspection found no focused, xfail, or placeholder tests. Native opt-in skips are intentional; the reviewer database-free selection deselected all 12 integration cases.

## Findings

- None. No confirmed P0, P1, P2, or P3 findings; no finding accepted, repaired, or closed. No repair order needed.

## Remaining risk

- Native integration command was not rerun under the explicit no-PostgreSQL boundary; native persistence and cleanup confidence reuses the separately recorded Step 5 results.
- No configured frontend unit-test runner, Browser tests command, typecheck, combined Verify command, or performance/load/profiling command exists. Browser evidence is user-reported, not independent runtime observation; additional browsers and assistive-technology-specific results are unavailable.
- `npm --prefix frontend audit` was not run because network-backed scans were prohibited; no current vulnerability scan is claimed. `pip check` proves dependency consistency only; no backend security scanner is configured.
- A real simultaneous duplicate-request native test remains optional and unrun; parameterized SQL, database uniqueness, unit error translation, and recorded forced-precheck-miss native evidence cover the required path.
- The existing Starlette/AnyIO deprecation warning remains. Production routing/HTTPS, sign-in, sessions, and private authorization are later feature scope.


## Try it now

Run or do:

With the frontend running using `npm --prefix frontend run dev`, open
`http://127.0.0.1:5173/register` and submit the empty form.

Expected:

Field errors appear and focus moves to the email field. No account is created.

This proves:

The registration page is reachable and provides local empty-form validation.
