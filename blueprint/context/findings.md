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
