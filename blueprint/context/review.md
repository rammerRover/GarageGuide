# Independent Review

**Status:** passed
**Target commit:** c3391f30d9139034f89550609274be2fe87bea48
**Base commit:** bd763da52ba52c07f3fad3200cccade663dbe756
**Base ref:** refs/remotes/origin/main
**Spec hash:** b65e2da5acc0e6dac2755f3e8657459bbbceabb05ca1b07c189bef64b030cf8a
**Prepared by:** codex
**Builder model:** unknown (runtime did not expose exact model)
**Requested reviewer:** codex
**Requested model:** gpt-6.1-sol
**Requested execution:** automatic
**Requested at:** 2026-11-08T02:33:43.636466+00:00
**Workflow:** regular
**Check required:** no

**Reviewer adapter:** codex
**Reviewer model:** gpt-6.1-sol
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-08T02:41:07.108464+00:00
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** passed
**Check result:** not-required

## Commands

- `git rev-parse HEAD`, `git symbolic-ref refs/remotes/origin/HEAD`, `git merge-base refs/remotes/origin/main HEAD`, branch/status/index/untracked checks, tracked-spec checks and raw SHA-256 validation: passed. HEAD, permitted remote-default base, exact spec and allowed differences match the request; all build steps are checked and status is verified.
- `node --test frontend/tests/sessionState.test.js`: passed, 108 tests, zero failures/cancellations/skips/todo cases.
- `node --test frontend/tests/*.test.js`: passed, 170 tests, zero failures/cancellations/skips/todo cases. The focused 108 are included in the full total.
- `node --input-type=module` with reviewer-authored stdin reproduction importing the installed router, shared accountRoute and actual session store, and applying RequireSession gate predicates: passed, 20 variant/failure combinations; every protected navigation revalidated and denied private rendering while pending or after guest/unavailable results.
- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider`: passed, 360 tests; 87 native cases deselected, one existing Starlette/AnyIO deprecation warning. No PostgreSQL connection occurred.
- `backend/.venv/Scripts/python.exe -m pip check`: passed, no broken requirements.
- `npm --prefix frontend run lint`: passed.
- `npm --prefix frontend run build`: passed on the prescribed require_escalated retry after the initial esbuild sandbox parent-directory access denial; Vite 6.4.5, 51 modules, JavaScript 247.98 kB (gzip 78.91 kB), CSS 2.48 kB (gzip 1.06 kB).
- `git diff --check bd763da52ba52c07f3fad3200cccade663dbe756 HEAD` and `git diff --check`: passed; expected LF-to-CRLF notice only.
- Targeted source/test searches and redacted environment-example validation: passed; no focused, xfail or placeholder test was found. Native opt-in skips are intentional and were deselected here. Examples contain explicit local auth configuration, distinct development/test database names and placeholder-only password values; private environment contents were not displayed.
- Native integration command: unavailable in this pass under the explicit no-PostgreSQL boundary; recorded results reused below.
- `npm --prefix frontend audit`: unavailable without separate network-backed scan authorization; no network scan was run.
- Prescribed activity helper: initial invocation could not find Node; it succeeded after adding the existing fnm Node 22.23.4 installation to process-local PATH.

## Evidence

- Fresh generic Codex reviewer, exact runtime-selected model gpt-6.1-sol, automatic isolated subagent without builder transcript, instructed solely from the installed project-local Audit skill and independent-review contract. Existing findings were context, never the review checklist. No source repair, acceptance, staging, commit or external action occurred.
- Reviewed the complete 63-path bd763da52ba52c07f3fad3200cccade663dbe756..c3391f30d9139034f89550609274be2fe87bea48 range across all four lenses. The two review-evidence files were excluded from code scope. Covered all changed backend app/routes/config/query/security/schema files, every changed or added backend test/support/manual-launcher file, frontend components/state/API/validation/styles/entry point and all three Node test files, both frontend manifests, requirements/examples, README, .gitignore, inherited backend/prepapp.txt notes, build-plan/standards/spec, Feature 1 archive and all changed verification records. Followed nearby health, pytest, Vite and authoritative users/user_sessions SQL contracts. Dependencies, virtual environments, build output, caches, private environments and generated ignored activity/staging artifacts were excluded from source review; installed router matching was exercised as runtime evidence.
- Applied AGENTS.md, project coding standards and the verified spec: shared email/NFC rules and bounded credentials; Argon2/dummy verification; token/public-data separation; parameterized SQL; row lock before database-time sample; strict idle/absolute expiry and capped extension; commit-before-response and rollback/close; current-session replacement/revocation; user-scoped housekeeping; cookie attributes and 401/503 distinction; exact Origin/JSON/custom-header policy before business writes; fixed-message redaction/no-store; fixture guards and exact owned-record cleanup; accessible pending/error/retry controls, cancellation and stale-identity gating. No new dependency, schema or speculative abstraction was introduced by the repair.
- F-01 is closed by this independent review. App.jsx renders accountRoute, and sessionState.js uses public matchRoutes with that same descriptor, aligning decoding, case and full-path semantics. Independent reproduction covered literal/encoded/fully encoded/case/trailing/multiple-slash variants with guest/unavailable outcomes. Current tests also cover direct loads/refresh, history with reused keys, unrelated and malformed paths, pending states and stale results. Private content remains gated until successful fresh validation.
- F-02 remains closed after fresh inspection. The unchanged deadline watcher calls only endSession, clears identity/deadline/busy state, aborts pending requests and discards deferred rechecks; no API call or idle-renewal loop is reachable from the timer. Normal/+5/-5-minute clocks, equality, no further calls for nine hours, deliberate post-expiry actions, pending session/login/logout and obsolete timers passed as fake-clock simulations.
- Reused historical native evidence only: AUTHENTICATION_STATUS.md Step 5 records 87 guarded native passes (57 authentication API, seven registration API, one health, 18 session-query/lifecycle/concurrency and four user-query), with exact synthetic user/session cleanup verified. Backend application/tests and authoritative schema were unchanged in the frontend repairs. No reviewer native test, PostgreSQL connection, cleanup or server startup occurred. Historical native expiry/locking evidence is separate from fake clocks.
- Reused user-provided browser evidence only: the November 6 Chrome 156.0.8078.73 development/preview report covers the original sign-in/restoration/logout/history, registration regressions, failures, password lifetime, accessibility and responsive cases; the first repair report separately covers literal route variants and local expiry behavior without inheriting an unsupplied date/version/duration. The November 7 Chrome 156.0.8078.73 development/preview encoded-path report covers all six listed account variants, direct loads/refresh/history, real valid 200 recovery, simulated rejection/unavailability, stale-work cancellation and unrelated paths, with the reported exact guarded cleanup marker. These are user observations, not reviewer browser execution. Direct malformed HTTP paths were rejected by Vite before React loaded: server-boundary evidence only; React malformed-path coverage is automated. No full real 30-minute idle observation was repeated, and deliberate history requests are user activity.
- The active tracked specification needs no ignored-spec snapshot. Frozen current-feature.md and AUTHENTICATION_STATUS.md bytes were preserved; their pre-checkpoint progress narratives remain historical. Current review status lives only in this receipt and findings.md. The request's Check-required field is no, consistent with the manual Check policy; Check result is truthfully not-required.

## Findings

- F-01 [P1]: closed at this target after independent source review, reproduction and regression tests. Original finding, reopening and builder evidence are preserved in the ledger.
- F-02 [P1]: remains closed after independent preservation review at this target.
- No new confirmed P0, P1, P2 or P3 finding; no open/fixed blocking finding, accepted finding or repair order remains.

## Remaining risk

- Native integration was not rerun under the explicit no-PostgreSQL boundary. Native persistence, concurrency, expiry and exact cleanup confidence reuses the separately recorded 87-case Step 5 results; those are historical results, not this review's execution.
- No server/browser startup or configured browser harness was authorized. Browser evidence is user-provided and was not independently repeated. Malformed direct HTTP evidence stops at Vite, and no full real 30-minute idle observation, browser clock-skew run or eight-hour browser observation is claimed. Fake-clock tests are simulations.
- `npm --prefix frontend audit` was not run under the network-authorization boundary. No fresh dependency vulnerability scan is claimed; pip check proves consistency only. No backend security scanner or performance/load/profiling command, frontend typecheck, combined Verify or browser-test command is configured.
- Existing Node MockTimers experimental and Starlette/AnyIO deprecation warnings remain. Production login rate limiting and deployed HTTPS/proxy/cookie delivery remain explicit later production-security/deployment work. Local production preview and HTTPS TestClient cookie checks do not prove deployed HTTPS.
