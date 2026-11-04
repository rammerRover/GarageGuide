# Manual browser verification

Feature 1 Step 4 browser checks were completed by the user on November 4, 2026
in Google Chrome 156.0.8078.73, in development and production preview, with
verified synthetic-record cleanup. The reported observations are recorded in
[registration verification](REGISTRATION_STATUS.md), separately from automated
and native backend tests. No browser-control tool or configured browser harness
was available to the agent. The instructions below remain the repeatable manual
guide; unreported individual checks are not additional observed evidence. Keep
historical scaffold evidence separate.

## Guarded test backend and Vite

Run from the repository root. Stop any ordinary backend on port 8000 first.
Use the existing initialized `garageguide_app_test` and private
`backend/.env.test`; do not edit or display credentials. Exported PostgreSQL
variables override that file, so remove unintended overrides privately.
Do not initialize databases or run schema scripts for these checks.

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
   passwords. Only `/` and `/register` are application pages.

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
   Verified cleanup: all reserved synthetic accounts are absent.
   ```

Cleanup recovers IDs by exact reserved email, deletes only those exact ID/email
pairs, commits, then verifies absence on a separate guarded connection. Never
force-kill the launcher during cleanup. If the marker is missing, do not record
a pass or continue native testing. Retain only the printed fixture-email list
and resolve those exact fixtures; never use broad deletion, truncate/reset, or
write to `garageguide_app`. Sequence gaps are expected. Record safe outcomes
and the verified-cleanup marker in `REGISTRATION_STATUS.md`.
