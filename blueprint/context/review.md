# Independent Review

**Status:** changes-requested
**Target commit:** 4250092b58e8a73048e879fe00e9f4025cfd5d9b
**Base commit:** bd763da52ba52c07f3fad3200cccade663dbe756
**Base ref:** refs/remotes/origin/main
**Spec hash:** e050b64b673f684f61709ad2365670ea4ca86c64e7a8c6d7bd976129e4127aad
**Prepared by:** codex
**Builder model:** unknown (runtime did not expose exact model)
**Requested reviewer:** codex
**Requested model:** gpt-6.1-sol
**Requested execution:** automatic
**Requested at:** 2026-11-07T05:13:30.701101+00:00
**Workflow:** regular
**Check required:** no
**Reviewer adapter:** codex
**Reviewer model:** gpt-6.1-sol
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-07T23:17:29.5423464+00:00
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** changes-requested
**Check result:** not-required

## Handoff

Review the active spec and the complete bd763da52ba52c07f3fad3200cccade663dbe756..4250092b58e8a73048e879fe00e9f4025cfd5d9b delta in a fresh
isolated subagent without the builder conversation. Run all four Audit lenses
from scratch using the installed project-local Audit skill and review contract.
The original changes-requested receipt is preserved in this checkpoint's
review.md blob; findings are context, never the review scope. Independently
re-examine F-01/F-02 and close them only if actual review evidence supports it.
Do not edit product code, tests, spec, verification records or configuration,
accept findings, stage, commit, complete, merge, push or deploy. Write only the
findings ledger and completed receipt, plus prescribed ignored activity.
Run the required database-free checks. No PostgreSQL connection or native rerun
is authorized for this frontend-only repair; reuse clearly identified recorded
native evidence and user-performed original/focused browser reports where
adequate. Do not start a server/browser or claim unperformed observations.

## Commands

- `git rev-parse HEAD`, `git symbolic-ref refs/remotes/origin/HEAD`, `git merge-base refs/remotes/origin/main HEAD`, `git branch --show-current`, `git status --short --untracked-files=all`, index/diff inspection and raw spec SHA-256: passed request bindings and permitted-difference checks; rechecked before recording the verdict.
- `git diff --stat bd763da52ba52c07f3fad3200cccade663dbe756..4250092b58e8a73048e879fe00e9f4025cfd5d9b` and full name/status inventory: inspected the complete 62-path delta, with review/findings treated as historical evidence rather than code scope.
- `node --test frontend/tests/sessionState.test.js`: passed, 63 tests, zero failures/cancellations/skips/todo.
- `node --test frontend/tests/*.test.js`: passed, all 125 frontend tests, zero failures/cancellations/skips/todo. Existing fnm Node 22.23.4 was prepended to process-local PATH; MockTimers emits its experimental warning.
- `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider`: passed, 360 tests, 87 native cases deselected, one existing Starlette/AnyIO deprecation warning; Python 3.13.17, pytest 8.3.5.
- `backend/.venv/Scripts/python.exe -m pip check`: passed, no broken requirements.
- `npm --prefix frontend run lint`: passed.
- `npm --prefix frontend run build`: first sandbox attempt failed because esbuild could not read parent directories; prescribed approved escalated retry passed with Vite 6.4.5, 50 modules, JS 247.95 kB (gzip 78.89 kB), CSS 2.48 kB (gzip 1.06 kB).
- Reviewer Node stdin reproduction with installed `matchRoutes`, `matchPath`, actual `createSessionStore` and private-gate predicates: confirmed F-01 remains reachable for /%61ccount, /acc%6Funt and /%41CCOUNT. Each matched Account, was classified public, made no second session request and allowed cached identity despite the next simulated result being guest. This is simulated API logic evidence, not browser evidence.
- `git diff --name-only fefa4b242047a0a18c02228963db3344ef2ce4fa..HEAD -- backend`: empty; backend product/tests are unchanged from the original independently reviewed implementation.
- `git diff --check bd763da52ba52c07f3fad3200cccade663dbe756..4250092b58e8a73048e879fe00e9f4025cfd5d9b` and `git diff --check`: passed; expected LF-to-CRLF notice only. Rechecked after receipt/ledger edits.
- Targeted skipped/focused/placeholder-test search: only intentional native opt-in skips found; no focused, xfail or placeholder tests. No installed typecheck, combined Verify, Browser tests, security-scanner or performance/profiling command exists.
- Activity helper: initial Node lookup failed before inspection; retry with supplied fnm PATH succeeded. Only prescribed ignored activity was written beyond the two evidence files.

## Evidence

- This generic Codex gpt-6.1-sol child began with only the project-local fresh-review handoff, without the builder conversation. Requested/actual execution is automatic with fresh subagent context. Existing findings and original receipt were historical context, not the review checklist.
- Independently verified exact target 4250092b58e8a73048e879fe00e9f4025cfd5d9b, permitted locally recorded remote-default base refs/remotes/origin/main, and re-derived merge base bd763da52ba52c07f3fad3200cccade663dbe756. Work branch is feature/sign-in-sign-out-and-protect-private-sessions. The tracked active spec's raw hash is e050b64b673f684f61709ad2365670ea4ca86c64e7a8c6d7bd976129e4127aad; status is verified and all six steps are checked. No ignored-spec snapshot applies. Initial and final differences are restricted to review.md/findings.md.
- All four lenses covered the full 62-path merge-base-to-target inventory, including inherited Feature 1 and existing local notes. Reviewed all changed backend application modules, public environment examples, requirements, backend tests and native/manual fixture support; all changed frontend components, helpers, styles, entry point, tests and package manifests; README, build plan, coding standards, frozen active spec, archived Feature 1 record and verification documents. Review/findings were excluded as product code. Followed nearby health/settings, Vite/pytest and authoritative users/session SQL contracts. Dependencies, generated bundles/state, caches, virtual environments and private environment files were excluded; only the installed router matching implementation was followed as necessary to confirm F-01.
- Quality/security review checked shared email/NFC/password handling, typed/redacted credentials, one real/dummy Argon2 verification, token secrecy/hash-only storage, whitelisted public identity, fixed errors/logging, exact Origin/JSON/CSRF enforcement, matching cookie scope, fail-closed configuration, no-store, parameter binding, commit-before-success and rollback/close. Session validation locks before sampling database time, retains strict validity predicates and absolute cap, and derives actor identity from the database. Replacement/logout affect the presented session; cleanup is scoped to the authenticated user. No additional confirmed backend defect arose.
- Performance/tests review covered bounded connection/query/request waits, short transactions, row-lock serialization, indexed session lookup, bounded frontend timer/work ownership, no automatic POST replay/polling, cancellation and stale-result rejection. Frontend route/UI review covered secret lifetime, loading/unavailable/guest gates, logout failures, visibility/document behavior, labels, field associations, focus/live feedback and responsive styles. The encoded-path reproduction confirms a coverage gap despite the passing route/history suite. No load or profiling measurement is claimed.
- F-01 independently re-examined: literal trailing-slash/case handling is repaired, but raw matchPath omits the decoding performed by the actual router. Installed matchRoutesImpl calls decodePath before matching; the reviewed store does not. The same protected-navigation defect remains for encoded paths and stays P1 open. Backend authorization remains enforced.
- F-02 independently re-examined and closed: watchExpiry now invokes only local endSession, which clears identity/deadline, cancels active work and discards deferred checks. It cannot renew server activity. Reviewer-run 63 focused cases include normal/ahead/behind clocks, equality, long idle periods without extra requests, explicit later navigation/visibility/retry, stale mutation/session results and obsolete deadlines. These fake-clock/API cases are automated simulations, not live expiration observations. No new defect in the expiry repair was confirmed.
- Native-reused evidence only: AUTHENTICATION_STATUS.md Step 5 records 87 guarded native passes and exact cleanup, and the original receipt preserved in this target's committed review.md records the prior independent reviewer's separate 87-pass native rerun with verified cleanup. Native evidence covers real hashing/commits, isolation, rollback, expiry/cap and bounded two-connection lock tests. Fixture source review confirms test-only settings, first-statement current_database() guards on each physical connection, initially absent reserved users, finalizers before writes, exact owned-record deletion/recovery and separate absence verification. Backend bytes are unchanged by these frontend repairs. This reviewer opened no PostgreSQL connection and reran no native test or cleanup.
- User-browser reused evidence only: the November 6 Chrome 156.0.8078.73 development/preview report in AUTHENTICATION_STATUS.md covers authentication/history, independent sessions, registration/CSRF, safe failures/password lifetime, accessibility, 375/768/1440 layouts, 200% zoom and manual cleanup. The later focused repair report separately covers /account, /account/, /ACCOUNT, unrelated /accounting, rejected/unavailable gates, local clearing without expiry requests, deliberate revalidation, late responses, logout/isolation, focus/layout and exact cleanup. No follow-up date/browser version/exact sizes or timing were supplied. Neither report supplies encoded-path evidence. These are user-performed observations; this reviewer did not start servers/browser or repeat them. Original November 4 registration evidence remains historical.
- Original findings, builder repair notes and committed original receipt remain preserved. Only review.md/findings.md were changed, plus prescribed ignored activity. Source, tests, spec, AUTHENTICATION_STATUS.md and configuration were frozen. No repairs, acceptance, staging, commit, completion, archive, merge, push, deployment, installation or external communication occurred.

## Findings

- F-01 [P1] open, frontend/src/sessionState.js:134: encoded account paths bypass protected navigation revalidation. Reopened the existing finding with independently reproduced evidence while preserving its original explanation and builder notes. Use actual router decoding/matching or matched-route revalidation; add encoded-route rejection/unavailable/history cases and affected browser checks. This blocks a passing receipt and completion.
- F-02 [P1] closed, frontend/src/sessionState.js:121: reviewed non-renewing local expiry clearing and stale-work cancellation, reran its fake-clock regressions and inspected separately attributed user observations. Original renewal-loop defect is gone; closure is specific to F-02.
- No new finding ID, accepted finding or repair. Suggested repair order: remaining F-01, applicable regression/browser checks, then a newly approved checkpoint and full fresh independent review. Verdict is changes-requested despite all reviewer-run automated gates passing.

## Remaining risk

- Native integration command was not rerun under the explicit no-PostgreSQL boundary. Native confidence reuses the separately recorded 87-pass implementation/original-review results and cleanup; no new native pass is claimed.
- No reviewer dev-server/browser startup was authorized, and no Browser tests or React component harness is configured. Browser/assistive-technology confidence reuses user observations. The remaining encoded-route defect is reproduced with actual router/store logic and a simulated API, not a live browser.
- Actual timed 30-minute/eight-hour browser expiration, live clock-skew behavior, individually labeled live versus simulated failures, additional browsers and assistive-technology-specific observations are unavailable. Automated/native boundary and simulation categories above do not imply those observations.
- `npm --prefix frontend audit` was not run because network-backed scans are outside scope. No current dependency-vulnerability scan is claimed; pip check establishes consistency only. No configured backend security scanner, typecheck, combined Verify, load/profiling or Browser tests command exists.
- Initial sandbox build failed on the known esbuild parent-directory restriction; escalated retry passed. Existing Starlette/AnyIO deprecation and Node MockTimers experimental warnings remain.
- Production login rate limiting and deployed HTTPS/proxy/cookie delivery remain explicitly deferred. No backend authorization bypass is established by F-01. Check was not required and was not run.
