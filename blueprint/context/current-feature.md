# Feature: Create and update maintenance schedules

**From build-plan:** feature 7
**Build attempt:** 1
**Branch:** feature/create-and-update-maintenance-schedules
**Archive:** blueprint/history/features/07-create-and-update-maintenance-schedules.md
**Status:** verified

## Goal

An owner can list, create, and update recurring maintenance tasks for a vehicle.
The build plan calls for positive day, mileage, and operating-hour intervals
with matching baselines, source notes, validation, and duplicate-task review
without inventing manufacturer recommendations.

## In scope

- List schedules on a protected page linked from the owned vehicle profile.
- Create and edit a named schedule with one or more enabled interval and
  baseline pairs, and optional owner-entered source notes.
- Enter a baseline explicitly or deliberately copy a known current mileage or
  operating-hours reading into the schedule draft.
- Review all other matching tasks on the same vehicle before saving a duplicate.
  Open a match for editing or explicitly save the draft as a separate task.

## Out of scope

- Deleting schedules, adding presets, or supplying manufacturer intervals or
  recommendations.
- Due status and reminders (Feature 8) and completion links or advancing
  baselines from service records (Feature 9).
- Schema or build-plan changes, dependencies, updates to vehicle readings or
  service history, and repairs for the carried-forward F-04 and F-08.

## Build loop

The starting point is local `main` containing Feature 6 completion commit
`1ef3b104812b04efe6705711d9a9f6a736578b7b`. Create the named feature branch
only after specification approval. Work through the five steps in order. Run
each step's focused checks, present the changes and evidence, and stop once for
approval before starting the next step. Make a checkpoint commit only with
explicit approval. Reserve full applicable suites for final verification.
Use the required independent review of the approved checkpoint before completion.

## Build steps

- [x] 1. Define schedule validation and response contracts. Add request and
  stored-response models and focused database-free tests for single or combined
  intervals, date and numeric boundaries, zero versus null, pair clearing,
  partial edits, and malformed input. **Done when:** valid cases round-trip
  through the models, invalid cases produce field-level validation, and the
  focused model tests pass.
- [x] 2. Implement owned persistence and guarded fixtures. List, insert, and
  update schedules through parameterized, vehicle-scoped queries. Serialize
  duplicate review with writes on the parent vehicle and preserve exact
  fixture ownership through cleanup. **Done when:** focused query and guarded
  native tests prove isolation, atomic duplicate review, rollback, unchanged
  vehicle readings, and exact cleanup. The concurrency test shows that two
  saves for the same new name cannot both succeed without review.
- [x] 3. Expose the authenticated schedule API. Register the list, create,
  and update routes using the existing authentication, request protection,
  and response conventions. **Done when:** focused API tests cover success,
  missing and foreign IDs, sanitized invalid requests, stale duplicate review,
  and a confirmed save. The API returns a conflict before an unreviewed write.
- [x] 4. Add the owned schedule page. Wire the vehicle profile link, list,
  inline create/edit form, explicit baseline copy, and duplicate review.
  **Done when:** focused frontend tests and a targeted guarded browser
  walkthrough demonstrate create, edit, combined pairs, unknown and zero
  readings, source notes, and opening a match or confirming a separate task.
  Check keyboard and narrow-screen use and record the actual browser evidence.
- [x] 5. Verify the complete feature and present the checkpoint. Run the full
  applicable suites once, check whitespace and the scoped diff, and review
  the manual evidence. **Done when:** the review packet names the exact
  checkpoint contents, commands, results, native cleanup, and browser evidence
  or gaps. Pause for checkpoint approval before independent review.

## Files / areas

- `database/01_schema.sql` is the existing schema reference. Reuse
  `maintenance_schedules`, its vehicle FK, existing checks, and vehicle index.
- Backend additions in `backend/app/maintenance_schedule_schemas.py`,
  `backend/app/maintenance_schedule_queries.py`, and
  `backend/app/routes/maintenance_schedules.py`. Register the router in
  `backend/app/main.py`. Follow the existing vehicle and service modules.
- Frontend additions are a protected schedule page and focused API, validation,
  and state logic. Extend `frontend/src/api.js`, `frontend/src/vehicleRoutes.js`,
  `frontend/src/App.jsx`, and `frontend/src/VehicleDetailPage.jsx` as needed.
- Add feature tests in `backend/tests/` and `frontend/tests/`. Reuse the
  database guard and test framework. Adapt schedule fixture handling where
  the new writers and editable names require exact ID tracking. Record
  browser and test evidence in `docs/verification/`.

## Data / contracts

### Schedule values

- `name` is required, trimmed, nonblank text. Preserve its display case.
  `source_notes` is optional plain text supplied by the owner. Trim surrounding
  whitespace and store blank or cleared notes as null. Reuse the existing
  safe text handling and render names and notes as text.
- `interval_days` is an integer from 1 through 2147483647. Its baseline is
  `baseline_date` in `YYYY-MM-DD` format. Accept a valid historical date or
  today using the existing server date convention. Leave the field blank
  initially and reject a future date for this starting baseline.
- `interval_miles` and `interval_hours` are positive exact decimal strings.
  Their matching `baseline_mileage` and `baseline_hours` are nonnegative
  exact decimal strings. Use the existing reading format and precision of
  `NUMERIC(12,1)` (at most one decimal place, maximum `99999999999.9`).
  Return numeric readings and decimal intervals as strings with one fractional
  digit. Reject booleans, JSON floats, nonfinite values, and silent rounding.
- At least one pair is required. A pair is either fully supplied or both
  fields are null. Disable a pair by clearing both values explicitly.
  An omitted PATCH field keeps its stored value. Validate the complete merged
  row so clearing a baseline alone or disabling the final pair fails. Existing
  rows with an inactive baseline allowed by the database remain readable and
  can be corrected on edit. Preserve stored values in the read representation.
- Copying a known reading fills the draft only when the owner chooses it.
  Unknown readings stay blank. A recorded zero is valid. A manual historical
  reading remains allowed when a current reading is unavailable. Saving a
  schedule leaves the vehicle and its reading timestamps intact.

### Owned API and duplicate review

- Use `GET` and `POST /api/vehicles/{vehicle_id}/maintenance-schedules` and
  `PATCH /api/vehicles/{vehicle_id}/maintenance-schedules/{schedule_id}`.
  A successful list returns `{vehicle_id, schedules}` ordered by schedule ID.
  An owned vehicle with no schedules returns an empty list. Create returns
  the saved schedule with HTTP 201 and update with HTTP 200.
- A stored schedule contains `id`, `vehicle_id`, `name`, all six interval
  and baseline fields, `source_notes`, and `created_at` in the existing
  timestamp format. Accept only editable fields and the optional duplicate
  review field on writes. Reject an empty or review-only PATCH. Use canonical
  positive path IDs and derive the actor from the validated session.
- Compare the proposed name against other schedules on the same owned vehicle
  using trimmed, case-folded names. Exclude the edited row. Keep the duplicate
  rule in the backend and return all matches in stable ID order. When a review
  is needed, return HTTP 409 with `code: "duplicate_schedule_name"`, a safe
  `detail`, and `matches` containing the owner's saved matching schedules.
- An explicit Save as separate task action resubmits the same draft with
  `reviewed_duplicate_ids`, a nonempty list of distinct positive IDs from
  the conflict response. This request-only field is never stored. Accept it
  only when its set equals the current matches. If matches change, show a fresh
  conflict and require another choice. If no matches remain, allow a fresh
  ordinary save after the empty conflict response. The client clears the
  reviewed set after changing the draft or opening a match. It never confirms
  or retries a write automatically.
- In each mutation, lock the scoped parent vehicle row before reading the
  target schedule or its matches. Use separate statements in the same
  transaction to reread current data after acquiring the lock. Then validate
  the merged data, recheck duplicate review, and write. Both create and update
  take the same lock in the same order. A later concurrent save must see the
  earlier committed change. The lock does not update the vehicle row.
  Prepare the success payload before commit and return it after commit.
- Scope reads and writes through the authenticated owner, vehicle, and schedule
  IDs as applicable. Respond with the same safe 404 for missing and foreign
  records. Reuse authentication, CSRF and origin checks, sanitized 422 errors,
  private no-store responses, session deadlines, and safe unavailable or
  unexpected errors. Exclude raw SQL, request data, and session secrets from
  error output and logs.

### Protected page

Use `/vehicles/:vehicleId/maintenance-schedules`. Show the saved list and an
inline editor. Include loading, empty, missing or unavailable, invalid,
duplicate-review, saving, and success states. Reuse existing protected-route
and session-generation handling so late responses cannot restore old private
state. Preserve a useful draft during validation and duplicate review. Help
the owner inspect the current list after an uncertain write before trying again.
Associate errors with labeled inputs, announce status accessibly, and keep save
and duplicate actions keyboard accessible. No manufacturer claims or default
intervals appear in the form.

## Testing

- Step 4 browser evidence: the user reported passing checks in Vite
  development and production preview on November 21, 2026, using Chrome
  157.0.8103.79. See `docs/verification/BROWSER_CHECKS.md` for the scope of the
  report and exact guarded cleanup message.
- Use focused pytest and Node `--test` selections for the changed logic at
  each step. In Step 5, run the complete applicable backend and frontend
  suites, lint, build, and whitespace checks using the documented commands.
  Record each outcome and distinguish browser observations from simulation.
- For native cases, use only explicit `RUN_DB_TESTS=1` against
  `garageguide_app_test` under the existing environment and first-statement
  connection checks. Capture schedule IDs from fixture inserts before commit
  where available. Use exact IDs and tracked parent ownership for cleanup, even
  after a rename or lost acknowledgment. Never adopt an ID from a name match.
  Verify absence on a separate guarded connection and stop on unexpected
  matches or cleanup failure.
- Keep existing owner isolation, schema checks, and Feature 6 regression
  coverage. A guarded browser walkthrough should use synthetic records and
  confirm fixture cleanup. Record observations when performed.

### Step 5 verification results

- The complete database-free backend suite passed 2,833 tests, and the
  frontend suite passed 1,005 tests across 14 files. Backend dependency
  checks, frontend lint, production build, and whitespace checks passed.
  The production build used Vite's runner config loader for the Windows
  sandbox. The runs reported the existing Starlette/AnyIO deprecation and
  Node's experimental MockTimers warnings.
- The complete guarded native suite passed 547 tests against
  `garageguide_app_test`. Separate guarded connections verified exact
  fixture absence for 545 cases with reserved fixtures. All six native
  schedule cases recorded exact cleanup, including both lock-wait cases.
- The November 21 browser evidence is user-reported and was reused for this
  verification. The exact browser cleanup message is in
  `docs/verification/BROWSER_CHECKS.md`.
- The 24-file checkpoint proposal is awaiting approval. Independent review
  follows approval of the checkpoint. The carried findings F-04 and F-08
  remain open and nonblocking.

## Notes for the AI

- The schema has no uniqueness requirement for task names. Duplicate review is
  a transactional application rule, and a confirmed duplicate is permitted.
- Reuse the existing connection, session, protected-route, view, and validation
  patterns. Keep later maintenance work and the two carried findings separate.
- This spec is for review. Branch creation and implementation wait for approval.
