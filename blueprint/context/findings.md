# Findings

> **Generated file.** The findings ledger: review findings raised by `/audit`
> against the work in progress, each with a durable ID, severity (P0-P3), and
> status. `/implement` marks repaired findings `fixed`, a later `/audit` pass
> moves them to `closed`, and `/complete` refuses to land while any P0 or P1
> finding is `open` or `fixed`, then archives resolved findings with the work
> and resets this file.

### F-04 [P2] open - Null service IDs reach the collection in direct detail and removal requests

**File:** frontend/src/api.js:427
**Found:** 2026-11-19 by /audit independent current (quality, tests)
**Why it matters:** The shared request helper treats `null` as the collection sentinel even for individual operations. A reviewer-run mock transport recorded `getService('7', null)` sending GET and `removeService('7', null, true)` sending DELETE to `/api/vehicles/7/services`. The protected service store rejects the same invalid ID before dispatch, and the collection has no DELETE route. The test at `frontend/tests/serviceApi.test.js:93` expects no dispatch, but uses `assert.fail` inside `fetch`. The request catch converts the thrown assertion into a result the test accepts.
**Suggested fix:** Require a canonical service ID when the operation targets an individual record and assert the mock fetch call count outside the request. Verify the collection GET and POST still operate without a service ID.
**Resolution:**

### F-08 [P2] open - Canceling a parts reload leaves its question in the live status

**File:** frontend/src/servicePartState.js:205
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** Opening the reload confirmation overwrites the current status. Choosing Keep current view closes the panel but leaves its question in the live status. A reviewer-run Node check started with a confirmed Add whose automatic refresh failed. After opening and canceling reload, refresh was still required but the committed-write explanation had been replaced by the question about discarding the preview. One Add and two list calls occurred, including the initial list and failed refresh. Cancel sent no request.
**Suggested fix:** Keep the prompt copy in the confirmation panel and preserve the prior result when the user cancels. Test cancellation after a confirmed write with a failed refresh.
**Resolution:**

Fresh gpt-6.1-sol review independently retains P2/open on November 20. A reviewer-run inline Node probe acknowledged one Add, failed its immediate list refresh, opened and canceled reload, then verified reloadPrompt false while message still equaled the reload question rather than the prior committed-write/failed-refresh feedback. refreshRequired remained true; request counts stayed one Add and two lists (initial plus failed refresh). No request occurred on cancel and write gating remained intact, so this is a nonblocking feedback-restoration issue rather than another uncertain-write or data-integrity failure.

### F-09 [P2] open - Confirmed duplicate save omits a newly discovered match from the saved list

**File:** frontend/src/scheduleState.js:84
**Found:** 2026-11-21 by /audit independent current (quality, tests)
**Why it matters:** A refreshed duplicate conflict can display a schedule added in another window. The store keeps matches only in the review state. On a successful confirmation, the success handler adds the new saved record to the older list and clears the review. An offline store probe confirmed that a review showing IDs 12 and 13 led to a success message and a saved list with IDs 12 and 15. ID 13 reappeared after manual reload. The database write and duplicate confirmation remain correct, but the screen hides a saved task it just asked the owner to review.
**Suggested fix:** Reconcile the already validated matching schedules into the displayed list by ID when a conflict arrives. Add a saved-list assertion to the existing refreshed-conflict test.
**Resolution:**

Feature 8 review rechecked this path. Automatic status refresh reconciles the saved list when it succeeds. An offline store probe confirmed that a failed automatic GET still leaves IDs 12 and 15 visible after a reviewed conflict showed 12 and 13. A deliberate GET restores 13. Retained P2/open for the failed-refresh path.

### F-10 [P2] open - An uncertain schedule edit leaves the old maintenance reminder visible

**File:** frontend/src/scheduleState.js:94
**Found:** 2026-11-25 by /audit independent current (quality, tests)
**Why it matters:** The uncertain-save branch keeps the previous status snapshot, and the page renders its reminders and per-limit results while prompting the owner to inspect the saved schedules. An offline probe used the real frontend request helper and session and schedule stores. It started with a Due task, simulated a PATCH that persisted a longer interval and returned HTTP 500, and observed that Due remained visible in the store snapshot. The next deliberate GET returned Upcoming. The stale reminder can show an obsolete due target while the owner is resolving the write outcome. The existing inspection and resubmission guard still works.
**Suggested fix:** Invalidate the affected status in the uncertain-save branch and keep the prior saved values and draft for inspection. Extend the uncertain-save test to assert that affected status is absent until a successful GET.
**Resolution:**
