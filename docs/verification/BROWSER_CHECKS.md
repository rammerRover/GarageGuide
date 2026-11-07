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
