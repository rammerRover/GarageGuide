# Independent Review

**Status:** changes-requested
**Target commit:** fefa4b242047a0a18c02228963db3344ef2ce4fa
**Base commit:** bd763da52ba52c07f3fad3200cccade663dbe756
**Base ref:** refs/remotes/origin/main
**Spec hash:** 993c246ddf15d9c85b53b0d451dc630ebf89b6279862f88d3c1e37fd01cb22b4
**Prepared by:** codex
**Builder model:** unknown (runtime did not expose exact model)
**Requested reviewer:** codex
**Requested model:** gpt-6.1-sol
**Requested execution:** automatic
**Requested at:** 2026-11-07T04:34:22.357061+00:00
**Workflow:** regular
**Check required:** no
**Reviewer adapter:** codex
**Reviewer model:** gpt-6.1-sol
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-07T04:41:29.5092054+00:00
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** changes-requested
**Check result:** not-required

## Handoff

Review the active spec and the complete bd763da52ba52c07f3fad3200cccade663dbe756..fefa4b242047a0a18c02228963db3344ef2ce4fa delta in a fresh
isolated subagent without the builder conversation. Run all Audit lenses from scratch:
quality, security, performance, tests, including correctness, transactions,
concurrency, privacy, frontend session state, accessibility and test coverage.
Check is configured manual and is not separately required. Reuse recorded native
PostgreSQL and user-performed browser evidence only where the local workflow permits,
explicitly distinguishing reviewer-run checks, reused observations and simulations.
Do not edit product code or the frozen specification/verification record, accept
findings, commit, stage, merge, push, deploy, install dependencies, or change schema.
Do not use the existing findings or builder conclusions as the review scope.

## Commands

- `git rev-parse HEAD`, `git symbolic-ref refs/remotes/origin/HEAD`, `git merge-base refs/remotes/origin/main HEAD`, `git branch --show-current`, `git status --short`, tracked-spec lookup and raw SHA-256 checks: passed the request bindings and allowed-differences checks before review. Rechecked at completion.
- `git diff --stat bd763da52ba52c07f3fad3200cccade663dbe756 HEAD` and complete range file inventory: inspected all 60 changed paths, including inherited registration history and local notes.
- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider`: passed, 360 tests, 87 native cases deselected; one existing Starlette/AnyIO deprecation warning.
- `backend/.venv/Scripts/python.exe -m pip check`: passed, no broken requirements.
- `node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js`: passed, 85 tests; no failures, skips, cancellations or todo cases. Used existing fnm Node 22.23.4.
- `npm --prefix frontend run lint`: passed.
- `npm --prefix frontend run build`: initial sandbox attempt failed because esbuild could not read parent directories; approved escalated retry passed, 50 modules transformed, JavaScript 247.81 kB (gzip 78.87 kB), CSS 2.48 kB (gzip 1.06 kB).
- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -p no:cacheprovider --capture=tee-sys --maxfail=1`, with explicit `RUN_DB_TESTS=1`: passed, 87 tests, 360 database-free cases deselected, one existing warning, 123.63 seconds. Flag removed afterward. Output was buffered and filtered to expose only the exit code, counts and safe exact-cleanup marker.
- Reviewer Node stdin route reproduction: installed router `matchRoutes` accepted `/account/` and `/ACCOUNT`; actual session-store navigation performed no second session request and left the private gate open for cached identity. API rejection was simulated. Confirmed F-01.
- Reviewer Node stdin clock-skew reproduction: actual session store plus the provider's exact delay expression and simulated server lifetime rules remained authenticated after 75 server minutes without user activity, with idle expiry advanced to minute 105. Confirmed F-02; this is simulated timing evidence.
- `git diff bd763da52ba52c07f3fad3200cccade663dbe756 HEAD --check` and `git diff --check`: passed; expected LF-to-CRLF notice only.
- Targeted skipped/focused/placeholder-test search: found only intentional native opt-in skips. Native suite ran with no skipped cases; no focused, xfail or placeholder cases were found.

## Evidence

- This generic Codex child began with the project-local review handoff, without the builder transcript. Runtime-selected identity is Codex `gpt-6.1-sol`; execution is automatic in a fresh subagent. Prior findings and historical receipts did not define the review scope.
- Independently verified exact target `fefa4b242047a0a18c02228963db3344ef2ce4fa`, permitted locally recorded remote-default base ref `refs/remotes/origin/main`, and re-derived merge base `bd763da52ba52c07f3fad3200cccade663dbe756`. The work branch is `feature/sign-in-sign-out-and-protect-private-sessions`. The tracked active spec's exact raw SHA-256 matches the request; all five steps are checked and status is verified. No ignored-spec snapshot is needed.
- Reviewed the complete 60-file merge-base-to-target delta across all four lenses, including inherited Feature 1 work and local `.gitignore`/`backend/prepapp.txt` notes. Covered all changed backend application modules, environment examples, requirements, all added/changed tests and native/manual fixtures; all changed frontend components, API/credential/session helpers, styles, entry point, tests and both package manifests; README, build plan, coding standards, active spec, archived Feature 1 record and all changed verification documents. Review/findings were excluded as code inputs. Followed nearby health/settings/Vite/pytest and authoritative users/session SQL contracts. Dependencies, virtual environments, generated bundles/state, caches and private environment files were excluded from source review.
- Checked shared email/NFC/code-point/password handling, one real/dummy Argon2 verification, token hashing and masked representations, fixed-message redaction, public-field whitelists, origin/JSON/CSRF gates, matching cookie attributes, loopback/production configuration, no-store, commit-before-success, rollback/close, parameter binding, post-lock database time, strict idle/absolute expiry, replacement/revocation, independent sessions and user-scoped cleanup. No additional confirmed backend finding arose.
- Reviewer-run native checks used only test configuration through `load_settings(testing=True)`, effective name `garageguide_app_test`, and the verified existing `SELECT current_database()` guard as the first statement of each physical connection. Schema inspection was read-only. Fixtures reserved unique initially absent synthetic identities, registered finalizers before writes, recovered committed sessions by owned users, deleted only exact owned session/user identities, and checked absence on separate guarded connections. All 87 native cases and cleanup teardowns passed; a safe exact-cleanup marker was observed. No schema change, initialization, broad deletion, sequence reset or other-database write occurred.
- Native tests independently exercised real hashing, committed session visibility, credential and identity isolation, both expiration limits/cap, rollback/recovery, current-browser replacement/logout, registration/health regressions, and two bounded row-lock tests using `pg_blocking_pids` to confirm waiting before revocation/expiry release. Deliberate exception injection, frozen boundary instants and lost-response tests remain simulated aspects of real native transactions.
- Frontend review covered response validation, request bounds/cancellation/no replay, transient credentials/public state, stale-response ownership, navigation/visibility/document gates, logout failures, expiry timers, route matching, labels/error associations/focus/live feedback, keyboard controls and responsive styles. F-01 and F-02 violate protected-navigation and idle-lifetime requirements despite passing existing tests. Recommendations include missing route-integration and clock-skew regression coverage.
- Reused browser evidence only: `docs/verification/AUTHENTICATION_STATUS.md` records the user's November 6, 2026 Chrome 156.0.8078.73 development/preview report covering authentication, history, independent browser sessions, registration/CSRF, failure feedback, password lifetime, accessibility, widths 375/768/1440, 200% zoom and the exact manual cleanup marker. This reviewer did not start a server/browser or independently observe these UI behaviors. Historical November 4 registration evidence remains historical. Unreported timed browser expiration/account switching and individually live versus simulated failure cases are not inferred.
- Preserved current-feature.md and AUTHENTICATION_STATUS.md bytes. Only findings.md and review.md were edited, plus prescribed ignored activity. No repairs, finding acceptance, staging, commits, completion, landing, dependency installation, deployment or external communication occurred.

## Findings

- F-01 [P1] open, `frontend/src/SessionContext.jsx:12`: account URL variants bypass navigation revalidation and can expose stale cached account identity. Match protected-route classification to the actual router and add regression coverage.
- F-02 [P1] open, `frontend/src/SessionContext.jsx:36`: an ahead-of-server device clock makes automatic expiry requests repeatedly extend an idle session. Make deadline handling unable to renew idle activity indefinitely and add clock-skew regression coverage.
- Both findings were added this pass. No findings were accepted, repaired, closed or invalidated. Suggested repair order: F-01, then F-02, followed by the full applicable checks and a newly approved checkpoint/full independent review. The current receipt cannot pass with these open P1 findings.

## Remaining risk

- No reviewer browser/dev-server startup was authorized and no Browser tests command/component harness is configured. Reused user observations support UI behavior, but route-variant and clock-skew findings were reproduced through logic simulations, not live browser checks. Repair validation should include the affected protected navigation and idle-expiry browser flows.
- Actual 30-minute/eight-hour browser expiration and individually labeled live outage evidence were not supplied; native strict-boundary/concurrency checks and simulated timing/failure checks are identified separately above. Additional browsers and assistive-technology-specific results are unavailable.
- `npm --prefix frontend audit` was not run because network-backed auditing is outside the authorized scope. No current dependency-vulnerability scan is claimed; pip check validates dependency consistency only. No backend security scanner, typecheck, combined Verify, load test or profiling command is configured.
- The initial sandbox build was unavailable due the known esbuild parent-directory restriction; the approved escalated retry succeeded. The existing Starlette/AnyIO deprecation warning remains.
- Login rate limiting and deployed production HTTPS/proxy/cookie verification remain explicitly deferred requirements. The backend still enforces its absolute cap; neither finding establishes a backend authorization bypass.
