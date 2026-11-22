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


<!-- blueprint:completion {"schemaVersion":2,"specBytes":12985,"specSha256":"26bf0413f07cecfd8f2c384bfd249d972951dad8379efdcda7c5d350534f12e4","branch":"refs/heads/feature/create-and-update-maintenance-schedules","head":"e13e4a2a75429051d09ed793666967969b2220d0","baseRef":"refs/heads/main","baseCommit":"1ef3b104812b04efe6705711d9a9f6a736578b7b","sourceTree":"cd70c47bbb8d86de1da5feb6adcd0224b76a222c","landing":"local-merge","absentOptional":[]} -->

## Independent review

```markdown
# Independent Review

**Status:** passed
**Target commit:** e13e4a2a75429051d09ed793666967969b2220d0
**Base commit:** 1ef3b104812b04efe6705711d9a9f6a736578b7b
**Base ref:** main
**Spec hash:** 26bf0413f07cecfd8f2c384bfd249d972951dad8379efdcda7c5d350534f12e4
**Prepared by:** codex
**Builder model:** unknown (runtime did not expose exact model)
**Requested reviewer:** codex
**Requested model:** gpt-6.2-sol
**Requested execution:** automatic
**Requested at:** 2026-11-21T21:21:31.5558008-06:00
**Workflow:** regular
**Check required:** no
**Reviewer adapter:** codex
**Reviewer model:** gpt-6.2-sol
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-21T21:24:43.7144662-06:00
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** passed
**Check result:** not-required

## Commands

- `git rev-parse HEAD`, `git merge-base main HEAD`, `git branch --show-current`, `git status --porcelain=v1 --untracked-files=all`, `git ls-files --stage blueprint/context/current-feature.md`, and `Get-FileHash` against the spec and all proposed files: pass. Target, base, tracked spec, allowed worktree paths, and all 24 raw file hashes matched.
- `git diff --check main...HEAD`: pass.
- `git diff main...HEAD` and targeted source and test reads: pass. Reviewed the complete 24-file delta across all four lenses.
- fnm Node v22.23.4 `--input-type=module` with an inline store fixture: pass. Confirmed F-09 via assertions after conflict, confirmed save, and reload.
- PowerShell XML inspection of the saved native JUnit results: pass. Counted 547 cases, 545 exact cleanup records, and cleanup in all six schedule cases.

## Evidence

- Verified the complete product and fixture delta against the active spec, project coding standards, existing SQL schema, and session entry points. Both writers lock the scoped parent before rereading rows, validate the complete row, and check the exact current duplicate ID set before writing.
- Reused approved builder evidence in `blueprint/.state/staging/feature-7-checkpoint-review.md`, `feature-7-checkpoint-proposal.json`, and `feature-7-final-checks/`. Database-free backend 2,833 passed, frontend 1,005 passed, guarded PostgreSQL 547 passed against `garageguide_app_test`, with successful lint, dependency consistency check, and Vite runner-loader build. The six schedule-native cases include two lock-wait cases and separately guarded exact cleanup.
- Reused the November 21 user report in `docs/verification/BROWSER_CHECKS.md`, which states successful Chrome development and preview checks and provides the exact guarded launcher cleanup message.

## Findings

- F-09 [P2] open. A newly discovered concurrent match can disappear from the saved list after successful confirmation until the owner reloads.
- F-04 and F-08 remain open and unchanged from earlier work.

## Remaining risk

- Browser results are user-reported at the mode level. Individual checklist observations and simulated failures were unreported. The F-09 probe used mocked responses offline.
- No current dependency vulnerability scan or performance benchmark was run. The existing `npm --prefix frontend audit` requires network access and was outside the offline review. No performance command is configured.

```

## Verification evidence

Completion reused the recorded verification for the reviewed checkpoint. The archived receipt identifies the reviewer's own commands.

- Database-free backend: 2,833 passed.
- Frontend: 1,005 passed across 14 test files.
- Guarded native PostgreSQL: 547 passed against `garageguide_app_test`.
- Backend dependency check, frontend lint, and production build passed. The build used Vite's runner config loader.
- Native cleanup was verified through separate guarded connections in 545 cases with reserved data. All six schedule cases recorded exact cleanup, including both lock-wait cases.

On November 21, 2026, the user reported passing checks using Chrome 157.0.8103.79 in Vite development and production preview. Individual checklist observations and simulated failures were unreported. The user supplied this exact guarded cleanup message.

> Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent.

The recorded checkpoint evidence includes the exact native cleanup totals.

```json
{
  "databaseFreeBackendPassed": 2833,
  "frontendPassed": 1005,
  "nativePostgreSQLPassed": 547,
  "nativeDatabase": "garageguide_app_test",
  "nativeScheduleCases": [
    "test_owned_empty_list_and_two_account_isolation",
    "test_write_and_rename_preserve_vehicle_readings_and_exact_values",
    "test_confirm_only_the_current_matching_ids_and_exclude_edited_schedule",
    "test_failed_response_preparation_rolls_back_insert_and_update",
    "test_waiting_save_rechecks_matches_after_lock_holder_commits[create]",
    "test_waiting_save_rechecks_matches_after_lock_holder_commits[update]"
  ],
  "nativeFixtureAbsence": {
    "cases": 545,
    "users": 998,
    "sessions": 964,
    "vehicles": 471,
    "services": 292,
    "partSnapshots": 61,
    "completions": 19,
    "schedules": 29,
    "catalogEntries": 33
  },
  "lint": "passed",
  "productionBuild": "passed with Vite configLoader runner",
  "pipCheck": "passed",
  "whitespace": "passed",
  "reverseDiffCheck": "passed",
  "browser": {
    "date": "2026-11-21",
    "by": "user",
    "version": "Chrome 157.0.8103.79",
    "modes": [
      "Vite development",
      "production preview"
    ],
    "result": "All checks the user performed passed",
    "cleanupMessage": "Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, and schedules are absent."
  }
}
```

The source logs and JUnit results are retained locally under `blueprint/.state/staging/feature-7-final-checks/`.

| Evidence file | Raw SHA-256 |
| --- | --- |
| `backend.xml` | `2edb222b36fdceb1171cce5c7b2f95790079f01358c2c69352d9632d1287b8ee` |
| `native.xml` | `d0902a88a8768c68bcddc990bffd5ed6401701891df81175f0577a58eb4c44db` |
| `backend.log` | `e1b7e8844626f569dc05bc81785d18ce3d4f5f3c8852d71590f6e4b67f536cf8` |
| `native.log` | `59d0dd7943d9bdfa680ecd0899f33c4800b4c8787f8fd7db9f6901f00a90c49e` |
| `frontend.log` | `3c94c31fdbad7fc945940dc32375bb162657eb196f07f9eee9436d25431498c7` |
| `lint.log` | `3aee3900766951425bc0f22e040020d1a4ca51271636336c8230da3ab66fba66` |
| `build.log` | `c3cda311cbeeedde2af3448b66348543ba643e9574be060013afbb3b401f552f` |
| `pip.log` | `6326999b2d47daff6338070efad9139a62dd802f33019eab621859ade33fc907` |

## Carried findings

F-04, F-08, and F-09 are open at P2 and remain in the live ledger. The receipt records the F-09 duplicate-review display issue.

## Try it now

Run or do:

With the guarded test app already running, sign in with a reserved synthetic
account and open the Maintenance schedules page for an owned vehicle with
current mileage recorded as zero. In the schedule form, select
**Copy current mileage**.

Expected:

The Baseline mileage field displays `0.0`.

This proves:

The schedule draft can use a known zero reading as its baseline.
