# Feature: Calculate maintenance status and in-app reminders

**From build-plan:** feature 8
**Build attempt:** 1
**Branch:** feature/calculate-maintenance-status-and-in-app-reminders
**Archive:** blueprint/history/features/08-calculate-maintenance-status-and-in-app-reminders.md
**Status:** Verified. Awaiting approval of the 14-file checkpoint.

## Goal

On an owned vehicle's Maintenance schedules page, show whether each saved
task is Upcoming, Due, Overdue, or Needs information. Explain the result using
the saved baseline, exact due date or reading, the last saved vehicle readings,
and any relevant input warnings. Show in-app reminders for tasks that are
Overdue, Due, or need information.

## In scope

- Compute date, mileage, and operating-hours limits using saved schedules and
  the owned vehicle's readings. Apply the first reached limit for a combined
  schedule and show every due or overdue limit.
- Calculate status on demand in one authenticated, read-only API. The existing
  protected Maintenance schedules page consumes the calculated results.
- Show exact due values, signed remaining amounts in their original units,
  unavailable inputs, and the advisory **Readings last changed** warning.
- Cover loading, empty, success, invalid address, missing or foreign vehicle,
  rejected session, unavailable, unexpected error, and deliberate retry.

## Out of scope

- A separate Due soon window, manufacturer intervals, and service advice.
- Feature 9 completion links, service-based completion inference, and baseline
  advancement. The saved schedule baselines supply Feature 8's starting values.
- Feature 14 garage-wide dashboard and cross-vehicle reminders.
- Persisted statuses, notification records or preferences, background polling,
  scheduled jobs, and email, push, or external notifications.
- Schema migrations, dependencies, and standalone repairs for earlier findings.

## Build loop

Start from local `main` containing the Feature 7 landing commit
`f160e47a50d5dafda14f1b8d3ebf7a49d96a2f7d`. Verify the baseline and create the
named branch after specification approval. Work through the four steps in
order. Run focused checks and stop once for user approval after each step.
With checkpoint commits enabled, obtain separate approval for an exact local
checkpoint. Run the full applicable suites once in Step 4, reuse unchanged
evidence, and obtain the required independent review before `$complete`.

## Build steps

- [x] 1. Implement pure status calculation and public result models. Cover
  exact thresholds, combination rules, zero, unusable readings, timestamp
  warnings, and supported calendar boundaries. **Done when:** focused
  database-free tests prove threshold equality, combined precedence, exact
  values, and that a timestamp warning alone leaves the result unchanged.
- [x] 2. Expose the owner-scoped read-only status API. Read the vehicle and
  schedules together, calculate the response, and use the existing route
  protections and error conventions. **Done when:** focused database-free
  API/query tests and authorized guarded native tests prove the response
  contract, no business writes, owned empty results, and identical missing
  and foreign-denial behavior with exact fixture cleanup.
- [x] 3. Show status and reminders on the existing schedule page. Reuse the
  protected page and editor, render the snapshot and advice, and refresh
  results after an acknowledged save. **Done when:** focused frontend
  tests cover presentation, refresh, retry, stale responses, and unchanged
  mutation rules. Guarded development and production-preview walkthroughs
  show due values, combined triggers, reading warnings, and accessible
  keyboard and narrow-screen states. Record actual browser observations and
  cleanup before the step review.
- [x] 4. Verify the feature and prepare the checkpoint. Run all applicable
  database-free backend, guarded native PostgreSQL, and frontend suites,
  dependency check, lint, production build, and whitespace checks.
  **Done when:** the review packet records commands, totals, cleanup,
  browser evidence by source, the exact diff and file hashes, and any
  blockers. Stop for checkpoint approval before independent review.

## Files / areas

- Add the calculation and result models in
  `backend/app/maintenance_status.py` using existing public schedule and
  vehicle models. Add the scoped read in
  `backend/app/maintenance_schedule_queries.py` and the route in
  `backend/app/routes/maintenance_schedules.py`.
- Extend `frontend/src/api.js`, `frontend/src/scheduleState.js`, and
  `frontend/src/MaintenanceSchedulesPage.jsx`. Keep response validation in
  `frontend/src/scheduleValidation.js` or a focused companion module if
  needed. Reuse the existing protected route and styling patterns.
- Add focused backend and frontend tests alongside Feature 7 coverage.
  Reuse the existing guarded fixture and browser launcher patterns.
  Record the guarded walkthrough and observed results in
  `docs/verification/BROWSER_CHECKS.md`.
- Use `database/01_schema.sql` as the existing data contract. The vehicle
  reading columns, shared timestamp, and schedule baselines supply all inputs.

## Data / contracts

### Calculation and aggregation

- Evaluate enabled intervals only. Calculate the due date from the baseline
  date plus the day interval. Use the backend's existing calendar convention
  for today and an injectable calendar and aware clock in tests. Capture the
  date and clock once per calculation so all schedules in a response share
  the same evaluation inputs.
- Add each baseline reading and interval using exact decimal arithmetic.
  Represent mileage and hours as strings with one decimal place in the API.
  Calculate signed remaining amount as target minus observed value. For days
  return an integer. A positive amount remains, zero is due, and a negative
  amount is overdue. A computed reading target may exceed the storage bound
  of either input because it is a sum. Keep the exact result.
- Compare each usable observation to its target. Below is `upcoming`, equal
  is `due`, and above is `overdue`. Zero is a known reading. A missing
  reading or one below its baseline yields `needs_information` for that
  limit. Show its due target when calculable and leave its remaining amount
  unset. A missing or unusable baseline for an enabled limit also yields
  `needs_information`. A legacy future calendar baseline requires review.
  A baseline attached to a disabled interval has no effect.
- Guard date arithmetic at the existing four-digit calendar boundary.
  Compare using integer day ordinals so an unusually large stored interval
  still has an exact threshold and days remaining. When the due date lies
  beyond the displayable calendar, show the exact baseline date plus the
  saved interval in days instead of a rounded or truncated date.
- Aggregate enabled limits in the following order. Any Overdue limit makes
  the task Overdue. Otherwise any Due limit makes it Due. Otherwise any
  unevaluable limit makes it Needs information. Otherwise it is Upcoming.
  Every due or overdue entry is a trigger. A trigger from one limit can
  coexist with warnings on another. Compare each limit in its own units.

### Saved readings and timestamp warning

- Mileage and hours use the last values saved on the vehicle profile. Label
  them as **Last saved mileage** and **Last saved operating hours**, and
  identify reading-based Due or Overdue as based on the last saved reading.
- Label `readings_updated_at` **Readings last changed**. This is one shared
  timestamp for changes to either saved reading. Use it solely as an
  advisory. Show a warning when it is missing, later than the captured
  current time, or at least 30 elapsed days old. Measure elapsed time with
  aware instants. The warning never changes per-limit or overall status,
  including Upcoming. The timestamp does not establish when either reading
  was taken.

### API and authorization

- Add `GET /api/vehicles/{vehicle_id}/maintenance-schedules/status` with the
  existing canonical path ID and session dependency. Read the owned vehicle
  and schedules in one scoped snapshot. Bind the vehicle ID and the user ID
  from the validated actor and use a left join to distinguish an owned
  empty list from a missing or foreign vehicle. Use the existing direct
  parameterized database access and stable ascending schedule ID order.
- Success is HTTP 200 with `vehicle` in the existing public vehicle format,
  `as_of_date` as `YYYY-MM-DD`, `readings_timestamp_warning` as
  `null`, `missing`, `future`, or `at_least_30_days_old`, and
  `schedules` as an array. Each entry contains the existing public
  `schedule`, its overall `status`, and `limits` in day, mileage, and
  hours order, including only enabled limits.
- A limit has `kind` of `days`, `mileage`, or `hours`, its `status`,
  `due_value`, `remaining`, and `issue`. The day target is an ISO date.
  Reading targets are exact strings with one decimal place. A null target
  indicates an unusable baseline or an exact calendar threshold outside the
  displayable range. The latter still supplies signed remaining days and
  uses the saved baseline and interval for display. The issue is `null`,
  `missing_reading`, `below_baseline`, or `invalid_baseline`.
- Return the existing safe 401 for an invalid session, the identical fixed
  404 for missing and foreign vehicles, a sanitized 422 for an invalid
  path, and the existing safe 503 and unexpected 500 conventions. Set
  `Cache-Control: no-store` and include the session deadline header only
  on successful status responses. The read endpoint uses the existing
  session path and makes no maintenance or vehicle writes. Feature 7's
  existing list, create, update, and duplicate 409 shapes stay compatible.

### Schedule page

- Load the saved list and statuses from the status snapshot on the existing
  protected route. Render a reminder list ordered Overdue, Due, then Needs
  information, and then by schedule ID within each group. Use one reminder
  per schedule. Link or focus the matching task in the same page. Show the
  overall status and per-limit evidence on each saved task, including
  Upcoming. Explain missing readings or readings below baseline, and show
  the shared timestamp and warning where mileage or hours are relevant.
- Treat status as a dated snapshot of saved data. Refresh on entry,
  deliberate reload, and an acknowledged schedule save. A failed
  read refresh after a confirmed save preserves that success and offers
  retry for the status read. Withhold affected results until a fresh
  snapshot is available. Preserve the existing draft, duplicate review,
  and uncertain-save behavior, including deliberate inspection before
  resubmitting and no automatic mutation retry.
- Use the existing auth generation, request cancellation, and deadline
  protections. Reject results from a previous vehicle, session, or request.
  Clear private data when the existing session guard invalidates it.
  Render task names and notes as text. Use visible status labels alongside
  any color, show which limits triggered a reminder, and announce loading
  and errors with accessible retry and keyboard focus.

## Testing

- Step 3 browser evidence: the user reported that all Feature 8 checks
  passed in Vite development and production preview on November 24, 2026,
  using Chrome 157.0.8103.79. They identified the blocked status GET as a
  DevTools simulation and observed a GET-only retry. The exact guarded
  cleanup message is in `docs/verification/BROWSER_CHECKS.md`.
- Focus calculation tests on equality and just-before/after boundaries,
  competing triggers, missing or below-baseline observations, all-zero known
  readings, decimal sums beyond the input range, day overflow, and exact
  30-day, missing, and future timestamp cases. Demonstrate that fresh and
  warned copies of the same saved readings produce the same status.
- Test the owned snapshot with an empty schedule list, multiple schedules,
  canonical IDs, session errors, and identical missing and foreign outcomes.
  Test no business writes and exact decimal/date serialization. For native
  cases require explicit `RUN_DB_TESTS=1`, `garageguide_app_test`, a guarded
  first statement for each physical connection, and exact fixture ownership
  and absence verification through separate guarded connections.
- Test mixed statuses, labels, reminders, stale replies, reload after save,
  refresh failure feedback, and the existing duplicate confirmation and
  uncertain-save paths. In guarded browser development and preview verify
  copy and reading labels, calendar equality, a combined trigger, warning
  text, ownership, retry and empty states, and keyboard and narrow layout
  behavior with synthetic accounts. Record the browser, date, observed
  cases, and exact final cleanup. Keep mocked warnings or errors identified
  as simulations when used.

### Step 4 verification results

- Database-free backend suite: 2,885 passed and 549 deselected. Backend
  dependency check passed.
- Frontend suite: 1,013 passed across 14 test files. Lint and production
  build passed. The build used Vite's runner config loader in the Windows
  sandbox.
- Guarded PostgreSQL suite: 549 passed and 2,885 deselected against
  `garageguide_app_test` with `RUN_DB_TESTS=1`. The run recorded 547 exact
  fixture cleanup confirmations, including both Feature 8 native cases.
- Scoped tracked and untracked whitespace checks passed. The backend
  suites reported the existing Starlette/AnyIO deprecation warning. The
  frontend suite reported Node's experimental MockTimers warnings.
- Browser verification reuses the user's November 24 observations in
  `docs/verification/BROWSER_CHECKS.md`. The blocked status GET was a
  DevTools simulation. Retry sent only a GET. The user's exact guarded
  cleanup message is preserved there.
- The reviewed checkpoint excludes the unrelated local `backend/prepapp.txt`
  edit. Independent review is pending checkpoint approval.

## Notes for the AI

- Keep calculations server-side and deterministic. Existing vehicle, schedule,
  route, session, and guarded fixture code provide the supporting contracts.
- Keep date and measurement inputs separate from the shared reading timestamp.
  In particular, an advisory warning cannot turn Upcoming into Needs
  information.
- This specification is for review. Branch creation and Step 1 follow the
  user's implementation approval.
