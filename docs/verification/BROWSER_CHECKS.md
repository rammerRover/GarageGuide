# Manual browser verification

## Feature 5 Step 7: user-performed browser verification complete

The user reported manually running the Feature 5 browser checklist on November
18, 2026, with all checks run passing, using browser version 157.0.8103.79.
In a follow-up clarification, the user explicitly confirmed completing the
entire checklist in BOTH Vite development and production preview.

These are user-performed observations, not agent/reviewer browser execution.
Real service behavior and the checklist's simulated failure cases remain
separate; simulations do not prove a PostgreSQL outage or server revocation.
No additional per-case outcome or numeric idle duration is inferred from the
general pass report. Automated/native PostgreSQL evidence remains separately
recorded in SERVICE_HISTORY_STATUS.md; no tests or PostgreSQL connections were
rerun to record these observations.

The user reported this exact guarded-backend cleanup confirmation:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.
```

Both required browser modes and exact cleanup are confirmed. Step 7 was approved;
Step 8 final automated/native results are recorded separately in
SERVICE_HISTORY_STATUS.md and add no browser observations. The procedure below is retained for
repeatability and is not additional execution evidence. Historical Feature 1-4
records remain unchanged.

### Feature 5 F-03 focused repair: user-performed observations

The user confirmed completing all four focused Unicode repair steps in BOTH
Vite development and production preview after the inward-scanning trim change:

1. Long interior whitespace and U+FEFF were preserved in a synthetic record.
2. The affected record and an ordinary record appeared in history and opened
   correctly.
3. A cost-only edit sent only the changed cost in PATCH; description and notes
   were omitted.
4. Exact guarded cleanup was confirmed with the message recorded above.

This is focused user-browser evidence for the repair based on
`113b36db8be3a2bcc05a432559d383af069df0af`, not agent/reviewer execution, a full
checklist rerun, native-test execution, or a new simulated-failure run. No new
browser version or test date was supplied. Automated evidence remains separate.
F-01 stays closed; F-02/F-03 await fresh independent review. The original audit
receipt and findings remain unchanged. See SERVICE_HISTORY_STATUS.md for the
attributed report and cleanup text.

### Feature 5 guarded setup

Stop ordinary backend servers on port 8000. Use only the existing initialized
garageguide_app_test. Do not run SQL schema scripts, fixture SQL by hand,
ordinary production/development backends, or database reset commands. The
launcher loads only backend/.env.test, requires explicit RUN_DB_TESTS=1 and the
effective test database, and checks SELECT current_database() as the first
statement on every physical connection before exposing it. Remove conflicting
database environment overrides privately; never print credentials.

In terminal 1, from repository root:

```powershell
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe backend/tests/manual_registration_server.py --service-links
```

The launcher prints three reserved synthetic **email addresses**, not precreated
accounts or passwords. At /register, create A and B with the first two addresses
and C with the third. Choose your own temporary 15-128-character passwords and
use those same passwords at /login. Use two independent browser profiles or
normal/incognito for A and B (two incognito windows may share cookies). Do not
use ordinary accounts/data, copy cookie values, log passwords, or export request
bodies/screenshots containing secrets. Access logging is disabled in this
test-only backend. Keep the backend running through dev and preview.

Create distinct synthetic vehicles under A and B. Their histories start empty.
With --service-links, only C's newly created vehicles receive two synthetic
records: "Synthetic part-linked service" and "Synthetic completion-linked
service". These are test fixtures, not parts/schedule product functionality.
All service creations are reserved before writes. Edits/removal use immutable
tracked service/vehicle/owner IDs; missing/foreign/wrong-parent records still
reach the normal safe 404. No fixture may adopt an ordinary existing record.

Terminal 2:

```powershell
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
npm --prefix frontend run dev
```

Use http://127.0.0.1:5173. In another terminal with the same Node PATH, build
and start preview when ready; keep the same guarded backend:

```powershell
npm --prefix frontend run build
npm --prefix frontend run preview
```

Use http://127.0.0.1:4173. Sign in separately for preview; use new synthetic
vehicle/description suffixes so dev and preview evidence can be distinguished.
Do not start an ordinary uvicorn backend. If setup/guard/cleanup fails, stop;
do not switch to another database or broadly delete records to continue.

### Feature 5 real browser checklist — repeat in dev and preview

1. **Routes and gates:** From Account, open the garage, an owned profile, then
   Service history. Direct-load/refresh /vehicles/V/services and
   /vehicles/V/services/S (substitute your exact synthetic IDs). Repeat with
   trailing slashes, uppercase static segments, and percent-encoded static
   segments/ASCII ID digits. Leave via a Link and use Back/Forward as well as
   refresh. Authentication and business-loading gates must precede private
   history/identity. /vehicles/new must still open vehicle creation.
   Invalid IDs (01, 0, +1, 1.0, overflow, non-ASCII digits) and unrelated suffixes
   must show no cached service records. If Vite rejects a malformed direct HTTP
   path before React loads, record it as a server-boundary result only.
2. **Empty/list/create:** A's new vehicle has no services. Open its history and
   create maintenance, repair, inspection, and diagnostic records with dates and
   descriptions. Check newest service date first, then creation/id for ties.
   Create with neither reading/cost, mileage only, hours only, both readings,
   and confirmed zero readings/cost. Unknown values show Not recorded; zero
   readings show 0.0 and confirmed-free cost shows USD 0.00. Use exact decimal
   controls (for example 12345.6, 45.7, USD 42.50). Successful creation clears
   the form, then GET reloads history. Repeated clicks/Enter while pending must
   produce one POST. Identical deliberate records remain allowed.
3. **Fields/validation:** Required date/type/description must be labeled. Only
   four types are offered. Invalid/blank required text, impossible date, a
   future date (9999-12-31), negative/exponent/comma/excess-precision decimals,
   and overflow must give safe field errors, first-error focus, and corrected
   field-error clearing. The backend decides today; do not infer its day from
   the browser time zone. Optional blank notes become null. No raw error/input
   or driver information appears. There is no file upload or parts editor.
4. **Detail/edit/cancel:** Open a saved entry from history. Enter Edit, change
   values, then Cancel edit. It must send no PATCH and show the saved values.
   Save text/date/type changes and reload to confirm persistence. Save reading
   decreases and clear known mileage/hours/cost/notes to blank; no odometer
   confirmation is required for these historical snapshots. Inspect PATCH
   field names only: unchanged business fields are omitted; cleared optional
   values are null; zero stays an exact decimal string. No empty PATCH is sent.
   Save stays on detail and shows the committed response. Returning to the
   vehicle profile proves current mileage/hours/readings_updated_at unchanged.
5. **Removal:** Remove opens an inline confirmation explaining permanence and
   possible newer concurrent edits. Cancel removal sends no DELETE and retains
   the record/draft. Confirm once: one DELETE with literal confirm_removal true,
   then return to history and GET reload; the entry is absent. The old detail
   URL/repeated removal request returns the same safe 404. No automatic replay,
   force option, child-data disclosure, or undo promise is offered.
6. **Linked records, real backend:** Sign in as C and create a synthetic vehicle.
   Its two seeded service descriptions identify the test cases. Part-linked
   service edits succeed but removal returns the fixed linked-data conflict.
   Completion-linked actual edits return the fixed completion conflict;
   removal is also blocked. Cancel/unchanged saves perform no mutation in the
   UI; no-op API success is separately covered by native tests. Reload after
   each blocked operation: the saved service and vehicle readings are unchanged.
   Do not inspect child data or delete links to bypass protection. Native tests
   separately prove child-row integrity and real locking; browser UI alone
   cannot establish those database assertions.
7. **Ownership:** In independent A/B browsers, create records under each one's
   vehicles. Neither history includes the other's data. Try B's parent/history
   and service URLs while signed in as A and vice versa. Also put A's service
   ID under another vehicle A owns. Missing/foreign/wrong-parent individual
   cases show the same fixed Service record not found; collection parent cases
   show Vehicle not found. Neither can create under the other's vehicle, edit,
   or remove the other's service. Use only these synthetic IDs. Preserve safe
   status/body observations; no unscoped existence information should appear.
8. **Sessions/headers:** Inspect safe Network response metadata: no-store on
   service success/errors and Session-Expires-At only on successful 200/201.
   Current successful service responses update the local deadline without an
   extra /api/auth/session request solely for synchronization. Errors do not
   extend it. Protected navigation, refresh, visibility return, and deliberate
   retry may revalidate. Leave the page visible and inactive until the actual
   last returned local deadline: identity, records, drafts, and confirmation
   clear without an expiry-triggered request, polling, or automatic retry.
   Report the real waiting duration; fake-clock tests are not this observation.
9. **Stale work/isolation:** Throttle/delay a service GET or write, then navigate
   between vehicles/records, Back/Forward, log out, switch accounts, relogin as
   the same account, hide/return, or reach expiry. Old successes/errors must
   never restore old records/drafts, claim current success, or extend a newer
   deadline. A rejected session hides all private content. An unavailable
   session gates it and offers deliberate retry. Logout one independent browser;
   the other remains independent. Restore all network controls before real retry.
10. **Accessibility/layout:** Keyboard-only navigation, labels, field-error
    associations, first-error focus, status announcements, confirmation focus,
    Cancel returning focus, and explained disabled/pending controls work. Check
    long descriptions/notes and Not recorded/zero at 375, 768, and 1440 pixels
    and 200% zoom without horizontal scrolling or clipped controls.

### Feature 5 simulated failures and uncertain writes

These simulations are not evidence of a PostgreSQL outage, actual session
revocation, or the backend's transaction/failure ordering. Run them only against
the guarded backend. The following optional DevTools shim keeps no request
bodies, passwords, cookies, or record values and logs nothing. Install once;
do not layer it with other fetch shims. Select a method and mode, exercise one
case, then restore real fetch before real inspection.

```javascript
(() => {
  const original = window.fetch.bind(window)
  const check = { method: 'GET', mode: 'off', calls: 0 }
  check.restore = () => { window.fetch = original; delete window.serviceCheck }
  window.serviceCheck = check
  window.fetch = async (url, options = {}) => {
    const method = options.method || 'GET'
    if (typeof url !== 'string' || !/^\/api\/vehicles\/[1-9][0-9]*\/services(?:\/[1-9][0-9]*)?$/.test(url) ||
        method !== check.method || check.mode === 'off') return original(url, options)
    check.calls += 1
    if (check.mode === 'network') throw new TypeError('Simulated network failure')
    if (check.mode === 'timeout') return new Promise((resolve, reject) => {
      const abort = () => reject(new DOMException('Aborted', 'AbortError'))
      if (options.signal?.aborted) abort()
      else options.signal?.addEventListener('abort', abort, { once: true })
    })
    if (check.mode === 'commit-lost') {
      // Only use with POST/PATCH/DELETE: the real guarded mutation runs once.
      if (method === 'GET') throw new TypeError('Select a mutation method first')
      const response = await original(url, options)
      if (!response.ok) return response
      await response.body?.cancel()
      return new Response('invalid JSON', { status: method === 'POST' ? 201 : 200 })
    }
    if (check.mode === 'malformed') return new Response('invalid JSON', { status: method === 'POST' ? 201 : 200 })
    const cases = {
      unavailable: [503, 'Service history unavailable. Please try again.'],
      authentication: [503, 'Authentication unavailable. Please try again.'],
      rejected: [401, 'Not authenticated.'], forbidden: [403, 'Request not allowed.'],
      unexpected: [500, 'Internal server error'],
      conflict: [409, method === 'PATCH' ?
        'Service record is linked to maintenance completion and cannot be changed.' :
        'Service record has linked data and cannot be removed.'],
    }
    const [status, detail] = cases[check.mode] || cases.unexpected
    return new Response(JSON.stringify({ detail }), { status, headers: { 'Content-Type': 'application/json' } })
  }
})()
```

- For GET, try unavailable/network/timeout/malformed/unexpected. Private history
  must not be confused with an empty successful history. Restore fetch and use
  Try again or Reload history. Also simulate rejected/authentication on a
  service request: rejection clears private state, authentication availability
  gates it. The existing auth-session shim below can test the navigation gate.
- For POST/PATCH/DELETE, test unavailable/network/timeout/malformed/unexpected
  and forbidden. There must be one request per deliberate submit/confirmation,
  a ten-second timeout, no automatic retry, and no idle polling. Known validation
  and linked conflicts keep correctable drafts; service-only availability keeps
  drafts but applies mutation uncertainty. Clear all failure modes afterward.
- For a valid POST with mode commit-lost, the real create runs but its success
  body is deliberately lost. The form retains its draft, blocks submission, and
  explains how to inspect date/type/description/readings/cost. Set mode off,
  deliberately reload history, inspect, and verify the duplicate-risk warning.
  Even an absent entry must not be described as proof of failure. Acknowledging
  that risk only unlocks the form; it must not send another POST automatically.
- For PATCH commit-lost, use a known unlinked record. The edit may have committed.
  Resubmission is blocked. Reload explains draft discard and requires agreement;
  restore real fetch and inspect saved values before editing again.
- For DELETE commit-lost, use a disposable unlinked record and explicit removal
  confirmation. No automatic replay occurs. Restore real fetch; deliberately
  reload the record/history. A later 404 states only current absence, not which
  request removed it. Real backend commit/rollback behavior is native evidence,
  not inferred from the shim.
- To test confirmed creation followed by failed history reload, first load a
  normal history, then set method GET and mode unavailable, and submit a real
  valid creation. POST must succeed but its follow-up GET fails. Feedback must
  still say the record was created and block accidental reposting. Restore
  mode off and reload history. Record this as a simulated GET failure.
- Finish with serviceCheck.restore(); restore auth shims/throttling/blocking too.

### Feature 5 exact cleanup and report

Sign out all synthetic browsers, then Ctrl+C the guarded backend and wait for:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.
```

Cleanup recovers exact reserved creations if an acknowledgment was lost, removes
only tracked/reserved child fixtures before services, then vehicles/sessions/users,
and verifies absence through separate guarded connections. Unexpected children
or any failed guard/cleanup stop verification; never truncate, broadly delete,
reset sequences, run schema initialization, or declare a browser pass without
the verified marker. The marker above is expected output, not an observation.

Report date, exact browser/version, dev/preview results, real create/list/edit/
remove/linked checks, two-account observations, actual idle duration, focus and
viewport results, simulated failure modes and restoration, exact cleanup output,
and anything unverified. Do not claim native test reruns or reviewer/browser
execution from these instructions. The November 18 user report above satisfies
Step 7's mode/cleanup acceptance. Separately authorized Step 8 verification is
recorded in SERVICE_HISTORY_STATUS.md; this guide is not new execution evidence.

## Feature 4 Step 5: complete and awaiting final review

The user reported completing the complete Feature 4 checklist on November 14,
2026 using Google Chrome 156.0.8078.73 in both Vite development and production
preview, with everything working as specified. The full attributed report is in
[vehicle profile verification](VEHICLE_PROFILE_STATUS.md). It covers routing and
gating, view/edit/save/cancel/reload, persistence, null versus zero, confirmation
and stale acknowledgment, two-account isolation, safe feedback, headers/deadline
synchronization, no polling/retry, visible local expiry without network work,
keyboard/focus/announcements, all three viewport widths and 200% zoom.

The user reported that simulated failure cases were restored afterward; those
are browser simulation evidence, not genuine PostgreSQL-outage or server
revocation evidence. Legacy response simulation remains separate from persisted
legacy-row behavior. No unreported malformed-path server behavior is inferred.
Automated tests and earlier native PostgreSQL results remain separate. No agent
browser run, new test execution or database connection is claimed by this update.

The user reported this exact guarded-backend cleanup confirmation:

```text
Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.
```

Step 5 and this browser record were subsequently approved. Step 6 final automated/
native verification and checkpoint preparation are recorded separately in
VEHICLE_PROFILE_STATUS.md; they add no browser observations or reviewer claims.
The following procedure is retained for repeatability. Its instructions and example
scripts do not add unreported execution details to the user's observations.
Historical Feature 1-3 evidence below remains unchanged.

### Guarded setup and commands

Use repository-root PowerShell terminals. Stop ordinary backends on port 8000.
Use only the existing initialized `garageguide_app_test`; do not run schema SQL.
Remove unintended database overrides privately without printing credentials.
The launcher requires `RUN_DB_TESTS=1`, loads only `backend/.env.test`, verifies
the effective database and `SELECT current_database()` as the first statement
on every physical connection, and registers exact cleanup before writes.

Terminal 1 (guarded backend; leave running until both environments finish):

```powershell
$env:RUN_DB_TESTS = "1"
backend/.venv/Scripts/python.exe backend/tests/manual_registration_server.py
```

It prints three **reserved email addresses**, not accounts or passwords.
Register accounts A and B at `/register` using two of these addresses and your
own temporary passwords (15-128 Unicode characters, matching confirmation).
Use those same passwords at `/login`. Do not use real users/vehicles, print
passwords, inspect/copy cookie values, or export requests/screenshots with secrets.
Use two independent Chrome profiles, or normal plus incognito; two incognito
windows can share cookies. Give every synthetic vehicle a recognizable unique
model, for example `GG-F4-DEV-A-<suffix>`. Both accounts must use only this launcher.

Terminal 2 (set the existing Node PATH in each terminal that uses npm):

```powershell
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173`. Repeat the checklist in preview, rebuilding first:

```powershell
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
npm --prefix frontend run build
npm --prefix frontend run preview
```

Open `http://127.0.0.1:4173`. Cookies are shared across ports on this host;
check the signed-in account when changing environments. Do not start the ordinary
uvicorn command, which uses development settings. The user starts these servers;
the agent has not connected to PostgreSQL for Step 5.

### Real routing, editing, confirmation and isolation

1. Signed out, direct-load a known `/vehicles/ID` URL. No identity or profile may
   flash before the session gate/login flow. Sign in as A, open the garage, and
   use a heading Link. Test direct load, refresh, Back/Forward and switching
   between two A-owned IDs. Repeat `/vehicles/ID/`, `/VEHICLES/ID`,
   `/%76ehicles/ID` and an encoded digit (ID `7` would use `%37`; substitute your
   actual ID). Every protected navigation validates the session before the
   vehicle loads. `/vehicles/new` and encoded/case variants must open creation,
   not a profile. `/vehicles/ID/other` must not display the profile.
2. Invalid IDs (`01`, `0`, `-1`, `+1`, `1.0`, `2147483648`, letters, encoded
   whitespace or non-ASCII digits) show a safe ID error and never old data.
   Direct malformed percent paths may be rejected by Vite before React loads;
   record that as a server-boundary result, not React browser coverage.
3. Create A-owned vehicles with both readings, neither, confirmed zero and no
   engine. Open each heading. Check ID, year/make/model/type/engine, readings,
   creation time and reading-update time. Unknown is `Not recorded`; zero is
   `0.0`. Edit text, preserve case/trim behavior, clear optional engine, Cancel
   and verify no PATCH and no retained draft. Save must remain on the profile,
   announce success and show committed data. Refresh to prove persistence.
   Empty/unchanged edits must not send PATCH. Exercise blank required fields,
   changed year boundaries, invalid decimal precision and field-error clearing.
4. Exercise each reading: unknown to zero/positive, increase, equal value,
   known to lower, known to null, zero to null, and both readings lowered or
   cleared in one save. Lower/clear shows an inline focused confirmation with
   exact current/proposed values (`Not recorded` for clearing). Cancel sends
   nothing and preserves the draft. Editing any business field removes the
   acknowledgment. Only Confirm and save changes sends the second PATCH.
   Repeated click/Enter attempts during pending work produce one request.
   No partial business update may appear after the first 409.
5. For a real stale snapshot, keep two independent windows visibly open and
   sign both into A. In window 1 propose a lower reading and stop at confirmation.
   In window 2 change that same vehicle's reading, then confirm in window 1.
   Expect another 409, no update, and required reload/review; no automatic replay.
   Repeat with window 2 lowering below window 1's proposed value, so the stale
   acknowledgment yields empty `fields`. Window 1 must require reload/review,
   not an empty confirm panel. If a visibility recheck clears the draft first,
   record that privacy behavior and repeat with both windows visible, or use
   the explicitly labeled 409 simulations below for that branch.
6. Reload vehicle first explains that the draft and confirmation will be
   discarded. Keep current draft sends nothing. Discard draft and reload sends
   GET only and shows the current row. A no-op/text-only save preserves reading
   time; an actual reading change, including clearing the final known value,
   updates it. Readings must never become floating-point artifacts.
7. Sign B into the independent profile, create a B vehicle, and use B's ID in
   A's address bar. Repeat A's ID as B. Missing and foreign-owned IDs show the
   same safe 404; no foreign fields appear. For PATCH isolation, leave A's edit
   page visible, sign into B in another tab of the **same** profile, return and
   verify session revalidation clears A's draft before B can view/update it.
   Real two-user API PATCH isolation is separately covered by guarded native
   tests; do not claim this UI check sends a foreign PATCH it does not send.
8. Test logout, same-account relogin, switching accounts, rejected sessions,
   hidden tabs, page departure and Back/Forward with pending GET/PATCH. Delayed
   responses must never restore old identity, vehicle, draft or confirmation.
   A vehicle-only outage may retain a correctable draft; authentication
   unavailability must hide/clear all private content behind the session gate.
9. Inspect only safe Network metadata: successful detail GET/PATCH are 200 with
   `Cache-Control: no-store` and `X-GarageGuide-Session-Expires-At`. Errors have
   no-store and no deadline. PATCH has JSON, CSRF marker and trusted browser
   Origin. No session request is made solely to synchronize a successful
   vehicle response's deadline. No periodic vehicle/session polling or mutation
   retry occurs. Keep the detail/edit page visible and truly idle until its
   full current local deadline: identity, profile, draft and confirmation must
   clear without any expiry-triggered request. Deliberate later navigation,
   refresh, visibility return or Retry may validate again. Record real duration.
10. Verify keyboard-only Edit/Save/Cancel/confirm/reload/navigation, visible
    focus, associated labels/errors, first-error focus, confirmation heading
    focus, success/status announcements and unavailable/not-found focus. Check
    375/768/1440-pixel widths and 200% zoom without horizontal scrolling.
    Repeat registration, login/logout, account, garage and create smoke checks.

### Browser simulations - separate from real persistence/native evidence

Use only the guarded backend. Install the following optional shim in DevTools
on a canonical synthetic profile URL. Set `profileCheck.path` to the exact
relative `/api/vehicles/ID` for that fixture and select `method` GET or PATCH.
It reads no request body, password or cookie and logs nothing. Restore it before
real tests and do not layer it over older shims. Counts are safe request totals.

```javascript
(() => {
  const original = window.fetch.bind(window)
  const check = { path: '/api/vehicles/REPLACE_WITH_SYNTHETIC_ID', method: 'PATCH', mode: 'off', calls: 0 }
  check.restore = () => { window.fetch = original; delete window.profileCheck }
  window.profileCheck = check
  window.fetch = async (resource, options = {}) => {
    if (resource !== check.path || (options.method ?? 'GET') !== check.method || check.mode === 'off') {
      return original(resource, options)
    }
    check.calls += 1
    if (check.mode === 'network') throw new TypeError('Simulated network failure')
    if (check.mode === 'timeout') return new Promise((resolve, reject) => {
      const abort = () => reject(new DOMException('Aborted', 'AbortError'))
      if (options.signal?.aborted) abort()
      else options.signal?.addEventListener('abort', abort, { once: true })
    })
    // Real guarded PATCH may commit; deliberately lose only its browser response.
    if (check.mode === 'lost-response') { await original(resource, options); throw new TypeError('Simulated lost response') }
    if (check.mode === 'late') {
      const response = await original(resource, options)
      await new Promise((resolve) => setTimeout(resolve, 5000))
      return response
    }
    if (check.mode === 'legacy' && check.method === 'GET') {
      const response = await original(resource, options)
      if (!response.ok) return response
      const body = await response.json()
      return new Response(JSON.stringify({ ...body, year: 1800 }), { status: response.status, headers: response.headers })
    }
    if (check.mode === 'malformed') return new Response('invalid JSON', { status: 200 })
    const outcomes = {
      missing: [404, { detail: 'Vehicle not found.' }],
      rejected: [401, { detail: 'Not authenticated.' }],
      forbidden: [403, { detail: 'Request not allowed.' }],
      authentication: [503, { detail: 'Authentication unavailable. Please try again.' }],
      unavailable: [503, { detail: 'Vehicles unavailable. Please try again.' }],
      unexpected: [500, { detail: 'Internal server error' }],
      confirmation: [409, { detail: 'Reading changes require confirmation.', fields: ['mileage'], current_readings: { mileage: '1000.0' } }],
      stale: [409, { detail: 'Reading changes require confirmation.', fields: [], current_readings: {} }],
    }
    const [status, body] = outcomes[check.mode] ?? outcomes.unexpected
    return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } })
  }
})()
```

- For GET, simulate missing/rejected/authentication/unavailable/network/timeout/
  malformed/unexpected. Restore real fetch before deliberate Retry/reload.
  No private vehicle may appear before a current valid response. GET 403 is
  safe feedback, not a claim the normal GET requires mutation headers.
- For PATCH, simulate forbidden, authentication, unavailable, network, timeout,
  malformed and unexpected. Authentication rejection/unavailability gates private
  content. Correctable vehicle failures retain draft; uncertain changes show
  exactly: `The update may have completed. Reload this vehicle and check its
  current values before submitting again.` No replay occurs. Use lost-response
  once for an ordinary text edit, restore, then deliberately reload to inspect
  the actual committed result. This is response-loss simulation, not DB outage.
- For confirmation simulation, begin with fixture mileage `1000.0` and propose
  `900.0`; mode confirmation returns the restricted 409. Confirming again in
  that mode must require reload/review. For the empty-fields branch, first get
  the initial confirmation, switch mode to stale, then explicitly confirm.
  No matched simulated 409 writes reach PostgreSQL.
- For late mode, start a GET or ordinary text PATCH then navigate to another
  ID/logout/change account within five seconds. A forwarded PATCH may commit;
  its late response must not restore stale page state. Restore and deliberately
  inspect the exact fixture afterward. Do not infer rollback from cancellation.
- Legacy-year UI coverage: select method GET and mode legacy for the fixture.
  This forwards the guarded GET and changes only its returned year to `1800`,
  preserving the public shape and headers. Reload, open Edit, change only model,
  restore the shim before Save, and inspect that PATCH omits year. The genuine PATCH
  returns the actual stored year. Separately test changing year to an invalid
  new value. Label this synthetic response coverage; real persisted legacy-year
  behavior is covered by native/API tests, not this browser response simulation.
- Finish with `profileCheck.restore()`. A shim
  401 does not itself revoke the server session or clear an HttpOnly cookie.
  Reconcile with real logout/login afterward. Simulated statuses do not prove
  a genuine PostgreSQL outage, server cookie deletion or real expiration.

### Cleanup and report

Restore shims/blocking, sign out both users, and stop the guarded backend with
Ctrl+C. Wait for this exact message before claiming cleanup or Step 5 acceptance:

```text
Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.
```

The launcher deletes only exact tracked synthetic vehicles (ID plus fixture
owner) before fixture sessions/users and verifies absence through separate
guarded connections. Do not force-kill, truncate, broadly delete, reset sequences
or manually clean ordinary data. If cleanup is not confirmed, stop and report it.
Report execution date, exact browser version, development/preview cases, real
observations, simulated cases, actual full idle observation, limitations and
exact cleanup output. The November 14 report above supplies the user-observed
acceptance and exact cleanup; Step 5 was subsequently approved.

## Feature 3 Step 4: complete for review with user-reported cleanup

The user reported browser observations on November 13, 2026 in Chrome
156.0.8078.73, in both Vite development and production preview. Reported real
behavior covers protected routes/history, Account navigation, empty/create/cancel
flows, all reading combinations and zero versus null, GET reload after POST,
repeat-submission protection, validation/focus/announcements, two-account
isolation, response headers, deadline synchronization, no idle polling, full
visible idle expiration without an API request, keyboard use, responsive layouts,
and 200% zoom. Unavailable/retry, rejected-session, uncertain-POST, and stale
responses were reported as simulations, not real PostgreSQL outages.

The user later confirmed all manual checks complete, specifically idle timeout,
GET/POST session behavior, adding vehicles, and comparison between two accounts.
This follow-up is user-provided evidence; it does not claim agent browser
execution or change the classification of simulated failures.

The full attributed record is in [vehicle verification](VEHICLES_STATUS.md).
The user subsequently confirmed this exact guarded-backend cleanup message:

```text
Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.
```

Step 4 and its user-provided evidence were subsequently approved. Step 5 final
automated/native verification was executed separately and is recorded in
VEHICLES_STATUS.md; no additional browser run was performed. The exact checkpoint
proposal awaits staging/commit approval before independent review.
The agent did not execute browser checks. The original browser observations
were recorded without a test rerun; fresh Step 5 automated/native results are
separate. The instructions below remain a repeatable procedure, with the
original enumerated observations and later all-checks confirmation attributed
to the user. No additional detailed test trace is invented. Existing
November 4, 6, and 7 observations remain earlier-feature evidence. Step 3 native
PostgreSQL and Step 4 automated evidence remain separate.

### Start the guarded environment

1. Stop any ordinary backend on port 8000. Use the existing initialized
   `garageguide_app_test` and private `backend/.env.test` configuration described
   below. Do not run schema scripts, initialize anything, display credentials,
   or use `garageguide_app`. Remove unintended database environment overrides
   privately; the effective database and physical connections must pass guards.
2. In a repository-root PowerShell terminal, start only:

   ```powershell
   $env:RUN_DB_TESTS = "1"
   backend/.venv/Scripts/python.exe backend/tests/manual_registration_server.py
   ```

   The launcher verifies the test database and prints three reserved synthetic
   email addresses. These are reservations, not pre-created accounts. Register
   two through `/register`, choosing your own temporary passwords that satisfy
   the existing registration policy. Keep passwords only in memory/the password
   controls; do not paste them into scripts, logs, screenshots, or this document.
   Use the same credentials on `/login`. No password is printed by the launcher.
3. Start development in a second root terminal:

   ```powershell
   npm --prefix frontend run dev
   ```

   Open `http://127.0.0.1:5173`. Use two independent browser profiles, or a normal
   and an incognito profile, for users A and B. Two incognito windows can share
   one cookie jar and are not reliable independent profiles. Never inspect,
   copy, print, or screenshot the HttpOnly cookie value.
4. Repeat this entire checklist in production preview after building, using the
   same guarded backend and `http://127.0.0.1:4173`:

   ```powershell
   npm --prefix frontend run build
   npm --prefix frontend run preview
   ```

   Ports share cookies for the same host, so sign out deliberately and check the
   active account when changing environment. Keep vehicle model names unique
   and synthetic, for example `GG-DEV-A-MILES-<your-unique-suffix>` and
   `GG-PREVIEW-B-HOURS-<your-unique-suffix>`. Record which environment each
   observation covers. Do not use real account or vehicle data.

### Routes, owned lists, and reading values

1. While signed out, directly load and refresh `/vehicles` and `/vehicles/new`.
   Both must gate private content and reach the sign-in flow. Check that `/`,
   `/register`, `/login`, and `/account` still work, including connection retry,
   generic invalid login, refresh restoration, registration validation/duplicate
   handling, and logout.
2. Sign in as A, use Account's Open your garage link, and confirm the empty list.
   Open Add vehicle. Cancel before saving must return without a POST or new row.
   Submit four unique vehicles: miles only, hours only, both, and neither.
   Include confirmed zero for each reading across these cases, a decimal such
   as `12.3`, optional engine blank/known, free-text type, mixed case, Unicode,
   and surrounding whitespace. A null reading must display `Not recorded`;
   confirmed zero must display `0.0`. No reading is inferred from vehicle type.
3. Confirm one POST per submission, with a relative `/api/vehicles` URL and no
   ownership fields. After 201 the form clears, navigation loads the garage
   through GET, and success is announced. No assumed local card is inserted.
   Identical deliberate submissions are allowed as distinct vehicles. Cards
   have no detail/edit/delete controls or future maintenance summaries.
4. In profile B, confirm A's vehicles are absent; add a unique B vehicle. A must
   not see B's vehicle. In one profile, also sign out of A and sign in as B,
   then test Back/Forward. A's list and unfinished form must not reappear.
5. Test direct loads, refresh, Links, and Back/Forward for `/vehicles`,
   `/vehicles/`, `/VEHICLES`, `/%76ehicles`, `/veh%69cles`, `/vehicles/new`,
   `/vehicles/new/`, `/VEHICLES/NEW`, and `/%76ehicles/%6Eew`. Each actual
   protected route must require current session validation before private UI.
   `/vehicles/1`, `/vehicles/new/other`, `/vehiclesx`, `/vehicle`, and encoded
   unrelated paths must not show a vehicle page. If Vite rejects a malformed
   direct HTTP path before React loads, record that as Vite-boundary evidence,
   not React coverage. Malformed route classification also has Node tests.

### Validation, accessibility, and pending work

1. Submit blank required fields. Check associated labels, hints, errors, first
   invalid-field focus, and announcements. Correct one field: only its obsolete
   error clears, and typing must not repeatedly steal focus.
2. Check year 1885, a year above the server's current year plus one, fractional
   year, blank make/model/type, and readings `-1`, `1.00`, `1e3`, and
   `100000000000.0`. These must fail safely. Leave readings blank to mean null,
   then enter zero explicitly. The browser must not silently round readings.
3. Throttle a real create request. While pending, inputs and Save are disabled.
   Repeated click/Enter must not produce extra POSTs. Correctable validation,
   network, timeout, and vehicle-unavailable failures retain transient values.
   Success, navigation away, logout, account change, and session end discard
   the private form. Leaving during a POST cannot undo a server commit; check
   the garage before any deliberate resubmission.
4. Complete all operations using the keyboard. Check visible focus, page-heading
   focus, readable error/status announcements, and meaningful unit labels. Check
   375, 768, and 1440-pixel widths and 200% zoom without horizontal scrolling or
   obscured controls. Record browser name/version, date, and environment.

### Failure simulations, separate from real PostgreSQL evidence

Use DevTools only on the guarded synthetic environment. Do not inspect or log
request bodies, cookies, tokens, passwords, or full request headers. The following
temporary console wrapper can simulate responses without logging private data.
Paste it once per document, change `garageSimulation.mode` deliberately, and
restore it before continuing normal checks. It is test instrumentation, not
application behavior, and none of its results prove a real database outage.

```javascript
window.garageSimulation = { mode: 'real', releases: [] }
const realGarageFetch = window.fetch
window.fetch = async (input, options = {}) => {
  const url = new URL(typeof input === 'string' ? input : input.url, location.origin)
  if (url.pathname !== '/api/vehicles') return realGarageFetch(input, options)
  const mode = garageSimulation.mode
  if (mode === 'network') throw new TypeError('Synthetic network failure')
  if (mode === 'timeout') return new Promise((resolve, reject) => {
    const stop = () => reject(new DOMException('Synthetic cancellation', 'AbortError'))
    if (options.signal?.aborted) stop()
    else options.signal?.addEventListener('abort', stop, { once: true })
  })
  const failures = {
    rejected: [401, 'Not authenticated.'], forbidden: [403, 'Request not allowed.'],
    authUnavailable: [503, 'Authentication unavailable. Please try again.'],
    unavailable: [503, 'Vehicles unavailable. Please try again.'],
    unexpected: [500, 'Internal server error'],
  }
  if (failures[mode]) {
    const [status, detail] = failures[mode]
    return new Response(JSON.stringify({ detail }), { status, headers: { 'Content-Type': 'application/json' } })
  }
  if (mode === 'malformedSuccess') return new Response('{', { status: options.method === 'POST' ? 201 : 200 })
  const original = await realGarageFetch(input, options)
  if (mode === 'lostAcknowledgment' && options.method === 'POST' && original.status === 201) {
    throw new TypeError('Synthetic loss after real committed creation')
  }
  if (['delayGet', 'missingDeadline', 'badDeadline', 'expiredDeadline'].includes(mode) && options.method === 'GET' && original.status === 200) {
    const bytes = await original.arrayBuffer()
    const headers = new Headers(original.headers)
    if (mode === 'missingDeadline') headers.delete('X-GarageGuide-Session-Expires-At')
    if (mode === 'badDeadline') headers.set('X-GarageGuide-Session-Expires-At', 'invalid')
    if (mode === 'expiredDeadline') headers.set('X-GarageGuide-Session-Expires-At', '2000-01-01T00:00:00Z')
    if (mode === 'delayGet') await new Promise((resolve) => garageSimulation.releases.push(resolve))
    return new Response(bytes, { status: 200, headers })
  }
  return original
}
garageSimulation.restore = () => {
  window.fetch = realGarageFetch
  for (const release of garageSimulation.releases.splice(0)) release()
  delete window.garageSimulation
}
```

- Set mode to `network`, `timeout`, `unavailable`, `unexpected`, or
  `malformedSuccess` and deliberately load/retry the garage or submit the form.
  Check distinct safe feedback, the ten-second bound, and no automatic retries.
  An uncertain POST must say the vehicle may have been created and direct you
  to check the garage. Simulated responses do not create records.
- `lostAcknowledgment` does send the real guarded POST and waits for its 201
  before simulating loss. Submit once, switch mode to `real`, and follow the
  check-garage link: the actual committed vehicle must be present once. Do not
  resubmit first. This is a simulated lost acknowledgment around a real write.
- First create successfully, then simulate a failing garage GET. The confirmation
  must still say the vehicle was created; only the reload is unavailable.
  To select a GET-only failure, add `&& options.method === 'GET'` to the failure
  branch in a temporary wrapper, or enable Network blocking for the collection
  GET after observing its POST 201. Do not claim creation itself failed.
- `forbidden` must show safe 403 feedback. `rejected` must clear/gate private
  identity and enter the login/session-ended flow. `authUnavailable` must gate
  private content and offer deliberate session retry; it must not claim logout
  or delete a potentially valid server cookie. Restore `real` before retry.
- `missingDeadline` and `badDeadline` must reject the response without accepting
  vehicles or inventing an extension. `expiredDeadline` simulates unusable public
  metadata and must enter the safe local session-ended flow. It does not prove
  that the database session expired or was revoked.
- For late work, set `delayGet`, enter the garage, and wait until the real request
  has completed but the page is still loading. Navigate away or through history,
  logout, or switch accounts. Set mode to `real`, then run
  `garageSimulation.releases.splice(0).forEach((release) => release())`.
  Old data/deadlines must not appear or restore identity. Repeat with rapid
  encoded-route navigation and unavailable/rejected session responses. This
  wrapper intentionally holds a buffered synthetic-test response to exercise
  stale-response handling even after browser request cancellation.
- Run `garageSimulation.restore()` before ordinary checks, or reload the page.
  Never persist this wrapper in application files, storage, or telemetry.

### Session deadlines and final cleanup

1. Observe only the public `X-GarageGuide-Session-Expires-At` response header on
   successful vehicle GET/POST. It must come from the server; successful vehicle
   activity must update the local deadline without an additional session GET.
   Navigation/startup/visibility return may separately request session validation.
   Do not screenshot request-cookie headers or private content.
2. To observe real idle behavior, leave a valid garage tab in the foreground
   without further protected actions through its latest known deadline. At the
   deadline private identity/list/form must clear or gate, with no expiry-driven
   session request, polling, retry, or idle renewal. This full observation can
   take 30 minutes. Keep it pending until actually observed; fake-clock Node
   tests and simulated deadline headers do not prove a real browser idle wait.
3. Separately test visibility return, deliberate navigation/refresh, and explicit
   retry. These are user-driven validation paths, not prohibited timer polling.
   A late response must not restore identity after expiration or logout.
4. Stop the guarded backend with Ctrl+C and wait for exactly:

   ```text
   Verified cleanup: all reserved synthetic accounts, sessions, and vehicles are absent.
   ```

   The launcher removes only its reserved synthetic records, vehicles before
   users, then verifies absence through separate guarded connections. If cleanup
   fails, stop all further database testing and resolve only fixture-owned
   records; never truncate, broadly delete, reset sequences, or initialize schema.
5. Report date, browser/version, development/preview coverage, real observed
   passes/failures, simulations performed, full-idle observation status, and the
   exact cleanup message. Do not include credentials or screenshots of secrets.

---

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
