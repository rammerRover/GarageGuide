# Feature: Record parts used during a service

**From build-plan:** feature 6
**Build attempt:** 1
**Branch:** feature/record-parts-used-during-a-service
**Archive:** blueprint/history/features/06-record-parts-used-during-a-service.md
**Status:** Steps 1-3 approved; Step 4 verified, including user browser evidence; awaiting final review/checkpoint approval

## Goal

Let an authenticated owner add, list, and deliberately remove historical part
snapshots on a service record. Support manual entry even when the catalog is
empty, and exact catalog lookup with a reviewed preview that is checked again
when saved. Preserve copied details after catalog changes or removal.

Keep Feature 6 as its single unchanged build-plan item. Use four implementation
steps, with a review and explicit approval stop after each.

Planning baseline: local main and HEAD are
`a55857122368529eba9481ff4613abdc94285716`, containing completed Feature 5.
The working tree and normal index were clean before this spec was written.
Feature 6 is the next unchecked item; the live feature file was the canonical
stub. Local main is ahead of the locally recorded origin/main; pushing is not a
prerequisite and is not authorized. First-build archive leaf and available Git
history were absent, and the exact branch had no ref or namespace collision.
No branch was created. Recheck this baseline before implementation; freeze build
attempt 1 and the branch/archive paths above.

## In scope

- Add and list snapshots under an owned service; confirm removal of one snapshot.
- Manual name, optional part number/manufacturer/notes, and positive quantity.
- Exact, case-sensitive catalog manufacturer/part-number lookup, preview, and
  server-side copy after the reviewed identity is rechecked in a transaction.
- Extend the existing protected service-record page, not a new product page.
- Owner-scoped parameterized queries, safe errors, existing session/CSRF policy,
  committed response deadlines, stale-response protection, and exact test cleanup.
- Guarded synthetic catalog entries for tests only; no real catalog seeding.

## Out of scope

- Snapshot editing: correct an entry by confirming removal and adding it again.
- Catalog browsing, fuzzy/partial search, suggestions, curation/admin interfaces,
  fitment lookup, compatibility claims, catalog imports, or production seed data.
- Saved-parts functionality or accepting a saved_parts reference as input.
- Part prices, line-item cost arithmetic, expense summaries, stock management,
  uploads, maintenance workflows, diagnosis, reports, or later build-plan items.
- Altering service date/readings/cost or vehicle current readings/timestamps.
- Schema changes, automatic schema creation, migrations, ORM, dependencies,
  server-side idempotency, polling, or automatic mutation retries.
- Repairing or accepting carried-forward F-04. Leave that existing P2 finding
  open and unchanged; this feature must not expand into the service-helper repair.

## Build loop

Use the configured Guided workflow: `workflow.stepReview: every` and
`workflow.checkpointCommits: enabled`. Implement only the explicitly authorized
step, run its checks, explain its files and behavior, then stop for approval.
Checkpoint offers never authorize staging or committing. Leave the build plan
and project-wide workflow settings unchanged during implementation.

Create only the frozen branch after specification and implementation approval.
Work never starts on main. Do not reinterpret earlier Step 1 authorization as
permission for native tests, routes, UI, or later steps.

Ownership, persisted private data, and removal make independent review required
before completion. After final verification, prepare exact files/hashes/diff for
checkpoint approval; only a separately approved immutable HEAD may enter
`$audit independent current`. `$check` observes behavior; `$check guide` provides
instructions only. `$complete` requires separate authorization. No automatic
commit, audit, completion, merge, push, deployment, or next-feature work.

## Build steps

- [x] 1. Define and test strict part snapshot models.

  Add `backend/app/service_part_schemas.py` and focused database-free tests in
  `backend/tests/test_service_part_schemas.py`. Define canonical snapshot ID
  validation, manual input, exact lookup input, reviewed preview, catalog-save
  input, discriminated create input, public snapshot/list, removal request,
  and removal response models. Reuse the installed Pydantic and current Unicode
  validation patterns; keep exact catalog comparison text distinct from manual
  trimming. Do not add queries, routes, fixtures that write, or frontend code.

  **Done when:** database-free tests prove quantity defaults to 1 only when
  omitted, accepts 1 and 2147483647, and rejects null, booleans, numeric strings,
  floats, fractions, zero, negatives, overflow, and nonnumeric values. Cover all
  required/optional fields, blank optional-to-null normalization, U+FEFF and
  interior whitespace, invalid Unicode/NUL, exact case-sensitive preview data,
  forbidden extra/ownership fields, strict IDs, exact public shapes and matching
  parent IDs, and confirmation accepting only JSON true. Public models preserve
  valid stored snapshot values rather than reapplying manual normalization.
  Run the focused schema file with the database-forbidding fixture. Report exact
  totals and the diff; stop for Step 2 approval. No PostgreSQL connection or
  native test is allowed in this step.

  **Step 1 evidence:** Added only service_part_schemas.py and
  test_service_part_schemas.py, on the frozen branch starting at completed
  Feature 5 commit a55857122368529eba9481ff4613abdc94285716. The focused command
  recorded below passed 264 tests in 0.48 seconds on Python 3.13.17, with one
  existing Starlette/AnyIO BlockingPortal deprecation warning. Every test uses
  forbid_database. No PostgreSQL connection or native suite ran. Required
  fields, quantity default/bounds, strict JSON types, exact preview text,
  manual trimming, Unicode/U+FEFF/interior preservation, public parent matching,
  forbidden fields, and explicit true-only removal are covered. Step 2 remains
  unstarted; no queries, routes, UI, schema or dependency changes were made.

- [x] 2. Add owner-scoped queries and guarded synthetic catalog fixtures.

  Add `backend/app/service_part_queries.py` using short explicit transactions
  and the existing connection layer. Implement owned-service list, exact lookup,
  manual/catalog insertion, and confirmed single-snapshot removal. Lock the
  parent service before attachment/removal; bind authenticated owner, vehicle,
  service, and applicable snapshot IDs. Re-resolve and lock the catalog row for
  catalog save, compare every reviewed field, then copy only server row fields.
  Prepare and serialize public results inside transactions, return only after
  successful exit/commit and connection closure, and translate known failures
  after rollback/closure. Preserve uncertain-commit behavior without retries.

  Extend `backend/tests/database_support.py`, `conftest.py`, and the manual test
  server only as necessary to reserve/track exact synthetic catalog and snapshot
  identities before writes, recover lost acknowledgments, and clean them safely.
  Add focused query/fixture-safety tests and native integration counterparts.

  **Done when:** database-free tests prove explicit SQL parameters and ownership,
  empty owned lists, ordering, manual operation with no catalog, matching/stale
  preview behavior, response preparation/commit/rollback/close ordering, and safe
  errors. After explicit native-test approval, guarded tests prove two-account
  isolation, null fields, quantity default/boundaries, manual/catalog inserts,
  repeated identical entries, exact removal, and no changes to service/vehicle
  values. Catalog edits leave snapshots unchanged; catalog deletion sets only
  part_id to null. Test lookup-then-change/delete/replacement conflicts, retaining
  all rows on failure. Coordinate real two-connection attachment versus service
  removal in both commit orderings, using PostgreSQL blocking evidence and
  synchronization, not sleep-only assertions. Exact cleanup must pass; stop on
  a guard or cleanup failure. Explain SQL and locking, then stop for Step 3.

  **Step 2 evidence:** Added service_part_queries.py and focused query,
  fixture-safety and native-query tests. Extended database_support.py and
  conftest.py for exact synthetic catalog/snapshot reservations, immutable-ID
  tracking, safe lost-acknowledgment recovery, reference-aware child-first
  cleanup and separate guarded absence checks. No manual-server change was
  needed before the interface/browser setup step. The focused database-free
  run passed 592 tests in 2.10 seconds, including the 264 Step 1 tests, new
  query/fixture tests and existing service/manual-server regressions.

  The explicitly approved native run used RUN_DB_TESTS=1, testing settings
  loaded only from backend/.env.test, effective/connected garageguide_app_test,
  and the existing first-statement physical-connection guard. It passed all
  95 tests in 202.55 seconds: 30 new snapshot-query cases, 17 existing service
  list/create cases and 48 existing service detail/update/removal cases. The
  tests proved stale-preview rejection, locked server-side catalog copying,
  exact case-sensitive lookup, preserved snapshot details after catalog
  edits/deletion, confirmed child-only removal, rollback and lost-acknowledgment
  behavior, and both service-removal race orderings using PostgreSQL blocking
  evidence. A concurrent catalog writer waited until the copied snapshot
  transaction committed. No schema was initialized or changed.

  All 95 native cases supplied successful exact-cleanup receipts. Aggregated
  tracked identities verified absent: 190 users, 190 sessions, 114 vehicles,
  108 services, 31 part snapshots, 12 maintenance completions, 13 schedules and
  20 synthetic catalog rows. These are identities verified absent, not DELETE
  affected-row counts or global table counts. Known IDs and reserved exact
  identities were removed child-first, with verification on separate guarded
  connections. No truncation, broad/prefix deletion, sequence reset, force
  cascade, or write outside garageguide_app_test occurred.

  Commands, JUnit output, cleanup receipts and exact totals are preserved under
  ignored blueprint/.state/staging/feature-6-step-2/. Both pytest runs reported
  the existing Starlette/AnyIO BlockingPortal deprecation. Tracked/untracked
  whitespace checks passed; Git reported line-ending conversion notices.
  No routes, frontend code, dependencies, F-04 changes, staging or commits were
  included. Step 3 remains unstarted and requires approval.

- [x] 3. Expose APIs and add tested frontend request/state logic.

  Add `backend/app/routes/service_parts.py`, register it through `main.py`, and
  add database-free/API/native tests for the contracts below. Reuse the existing
  authenticated-session dependency, mutation policy and response-deadline helper.
  Add a snapshot-specific sanitized boundary; do not broaden credential/service
  field whitelists or log request values.

  Extend `frontend/src/api.js` and add focused `servicePartValidation.js` and
  `servicePartState.js` modules where needed. Validate every ID before building
  URLs and keep list/lookup/create/removal parsing distinct. Track current
  vehicle/service, auth and request generations, saved snapshots, manual draft,
  lookup pair, reviewed preview, pending/confirmation state and uncertainty.
  No pages or controls are rendered yet. Add focused Node API/state/session
  regressions, preserving all existing service, vehicle and authentication tests.

  **Done when:** tests prove all response shapes, pre-body mutation policy,
  indistinguishable foreign/missing parents, safe errors, no-store on success
  and failure, and committed-deadline headers only on successful responses.
  State tests prove no duplicate writes, no automatic fallback or resubmission,
  catalog-pair changes invalidate the preview, stale conflicts require a fresh
  deliberate lookup, and cancellation cannot imply rollback. Cover uncertain
  creation/removal and independent required-refresh gating; a later correctable
  validation error must not recreate the old post-create refresh bug. Late
  results after navigation, logout, same-account relogin, account change, local
  expiration, hiding/departure or disposal cannot restore data or deadlines.
  Run applicable database-free backend tests, all frontend test files, lint and
  build; run native API tests only with explicit guarded-test authorization.
  Report results and stop for Step 4 approval.

  **Step 3 evidence:** Added and registered the four approved snapshot routes
  using the Step 2 queries and the existing authenticated-session, mutation
  policy and deadline helpers. The snapshot-specific error boundary sanitizes
  union/nested-preview/path errors, preserves fixed 404/409 and distinct 503
  responses, and returns no-store responses with deadlines only on success.
  No session algorithm or vehicle/service query behavior was changed.

  Added frontend request validation and state logic for manual/catalog entry,
  exact lookup/preview invalidation, explicit removal, independent required
  refresh, uncertainty inspection/acknowledgment, and request/auth/route
  generations. Reused the existing linear Python-compatible trim by exporting
  it; its behavior is unchanged. Existing service helpers containing F-04 and
  the finding status are unchanged. No visible component or React route changed.

  Focused database-free API tests: 184 passed in 4.52 seconds. Final focused
  frontend tests: 201 passed. Complete database-free backend suite: 2,638 passed,
  535 native cases deselected, one existing warning, in 31.00 seconds. Complete
  frontend suite: 978 passed across all thirteen files, zero failures/skips.
  pip check, lint and production build passed (66 modules; final build 1.42
  seconds). Final tracked/untracked whitespace checks passed.

  Guarded native API verification used RUN_DB_TESTS=1, only backend/.env.test,
  effective and connected garageguide_app_test, and first-statement physical
  connection guards. The final run passed 65 tests in 129.55 seconds: 64 new
  snapshot API cases and one existing full service GET/PATCH/DELETE regression.
  It verified actual commit/rollback/closure and lost-acknowledgment handling,
  source/parent isolation, stale catalog preview conflicts, catalog deletion
  snapshot preservation, mutation policy, safe validation, cookies and headers.
  The original Step 2 lock-query evidence remains separate and was not rerun.

  The initial native run stopped at 25 passes and one test-helper failure:
  TestClient json= synthesized Content-Type in a deliberately missing-header
  case. Sending raw JSON content corrected the helper without changing policy.
  The three affected missing-header cases then passed before the full rerun.
  The initial log/XML and focused recheck are preserved as separate evidence;
  they are not added to final passing-test totals. All 94 teardown receipts
  across the initial, focused and final runs verified exact cleanup.

  The final 65 cleanup receipts verified absence of 130 synthetic users,
  130 sessions, 73 vehicles, 73 services, eight snapshots and seven catalog
  rows; no schedules or completions were created in this run. These counts
  describe fixture identities verified absent through separate guarded
  connections, not global table state or DELETE affected-row counts.
  No cleanup/guard failure, schema setup, broad delete, sequence reset or
  write outside garageguide_app_test occurred. Real native persistence,
  synthetic fault injection, and Node mocks/fake clocks remain distinct.

  Detailed commands/results, final/initial native XML, and per-case cleanup
  evidence are under ignored blueprint/.state/staging/feature-6-step-3/.
  Warnings remain the existing Starlette/AnyIO deprecation, Node MockTimers
  experimental notices and Git line-ending conversion notices. No browser
  acceptance is claimed; the visible interface and browser checks are Step 4.
  No dependencies, schema, F-04 change, staging, commit or audit was included.

- [x] 4. Build the service-page snapshot interface and verify the feature.

  **Progress:** Parts used is implemented on the existing service detail page.
  The active contract and route both use POST prefix/lookup; no catalog-match
  discrepancy was found. Final database-free backend: 2660 passed; complete
  frontend command: 978 passed across all 13 files; native PostgreSQL: 537
  passed against guarded garageguide_app_test. Pip check, lint and production
  build passed. Exact cleanup receipts and command results are preserved in
  SERVICE_PARTS_STATUS.md and ignored Step 4 verification artifacts. The user
  confirmed the entire checklist passed in development AND production preview
  on November 20, 2026, browser version 157.0.8103.79, including the full visible
  idle-deadline check and the exact catalog-inclusive guarded cleanup message.
  User browser observations, real behavior, simulations and native evidence are
  recorded separately in SERVICE_PARTS_STATUS.md and BROWSER_CHECKS.md; no agent
  browser run is claimed. Application/test hashes are unchanged from the passing
  candidate, so runtime evidence is reused without rerunning suites for docs.
  Step 4 is complete and awaiting final review. The final file/hash/diff proposal
  is refreshed; no audit, staging, commit, feature completion or F-04 change was
  performed or authorized by this evidence update.

  Add a focused `ServiceParts.jsx` section to the existing service-record page,
  extending plain CSS. List saved snapshots; offer explicitly chosen manual
  entry or exact catalog lookup with reviewed preview; confirm single removal.
  Correct entries through remove/re-add. Preserve existing service edit/remove
  behavior and linked-data conflict rules. Extend the guarded manual server to
  provide synthetic catalog examples without inserting real entries.

  **Done when:** database-free/frontend tests, pip check, lint, production build,
  whitespace and complete diff review pass, and approved guarded native tests
  verify exact cleanup. Provide and record development and production-preview
  browser checks for empty-catalog manual entry, exact lookup/miss, explicit
  manual switch, preview/review/save, quantity, unknown optional fields, list,
  cancellation, confirmed removal, correction by re-add, ownership isolation,
  catalog change/delete conflict, surviving snapshots after catalog deletion,
  and service deletion blocking while attachments exist. Verify uncertainty,
  no retries/polling, stale work and local expiry, keyboard/focus/announcements,
  375/768/1440-pixel layouts, and 200% zoom. If no browser runtime is available,
  leave browser acceptance pending and give exact manual steps. Separate real,
  simulated, automated, native, and user-browser evidence. Stop with a complete
  file-purpose inventory, raw hashes, full diff, test results/limitations, and
  frozen checkpoint proposal; do not stage, commit, audit or complete it.

## Files / areas

- `backend/app/service_part_schemas.py`: strict request/public models only first.
- `backend/app/service_part_queries.py`: direct parameterized snapshot operations.
- `backend/app/routes/service_parts.py`, `backend/app/main.py`: API registration
  and safe boundary, only in Step 3.
- `backend/tests/test_service_part_schemas.py`, focused query/API and integration
  counterparts, fixture-safety tests, `database_support.py`, `conftest.py`, and
  `manual_registration_server.py`: exact guarded synthetic verification.
- `frontend/src/api.js`, `servicePartValidation.js`, `servicePartState.js`,
  `ServiceParts.jsx`, `ServiceRecordPage.jsx`, `styles.css`: existing-page flow.
- `frontend/tests/servicePartApi.test.js` and `servicePartState.test.js`: request,
  parsing, state, confirmation, session-generation and deadline coverage.
- `docs/verification/SERVICE_PARTS_STATUS.md` and `BROWSER_CHECKS.md`: commands,
  actual results, attributed browser evidence, cleanup, warnings and limitations.
- `database/01_schema.sql` is read-only source of truth; no SQL file, dependency,
  lockfile, prior archive, workflow setting, or unrelated change is planned.

## Data / contracts

### Existing SQL and historical behavior

`parts` stores id, manufacturer, part_number, name and category. Manufacturer
and part_number form a unique pair. Feature 6 performs an exact lookup only;
it neither reads fitment to claim compatibility nor seeds real catalog rows.

`service_parts` stores exactly id, service_record_id, nullable part_id, name,
nullable part_number/manufacturer/notes, and quantity INTEGER NOT NULL DEFAULT 1
CHECK (quantity > 0). There is no origin, category, price or created_at column.
Do not fabricate those fields or add a migration. Request source is not stored.
Category is displayed in the catalog preview and compared again on save, but
cannot be copied into a nonexistent snapshot column.

The service FK has ON DELETE CASCADE, but Feature 5 deliberately blocks service
removal while any snapshot or completion exists. Preserve that application
rule; do not use the cascade as deletion permission. The catalog FK has
ON DELETE SET NULL. Deleting a catalog row leaves copied snapshot details intact
and sets part_id to null. Other catalog FKs may independently block catalog
deletion; tests use exact synthetic catalog rows without unrelated links.

Never infer that a snapshot was originally manual solely because part_id is
null: its catalog reference might have been deleted. Removing a snapshot deletes
only that snapshot; it never deletes the catalog row, service, vehicle, or links.
After the final snapshot is deliberately removed, the normal Feature 5 service
removal rule applies, including any remaining maintenance-completion block.

### Strict types and input fields

All models use strict Pydantic types, forbidden extras, and hidden input in error
representations. Sanitize actual HTTP validation separately; model settings
alone do not remove raw request input from framework validation errors.

Path vehicle, service, and snapshot IDs accept canonical ASCII decimal text
1 through 2147483647, validated after framework decoding and before coercion.
Reject leading zeroes, signs, fractions, whitespace, non-ASCII digits, zero,
negatives, overflow and nonnumeric text with fixed sanitized 422 errors.
JSON IDs in previews/responses are strict positive integers within the same
range; booleans and coerced numeric strings are invalid.

Manual create input:

```json
{"source":"manual","name":"Oil filter","part_number":null,"manufacturer":null,"quantity":1,"notes":null}
```

- source must be exactly manual; name is required Unicode-safe nonblank text.
- Trim manual surrounding whitespace with Python-compatible semantics; preserve
  case, U+FEFF and all interior text. Reject NUL and unpaired surrogates.
- part_number, manufacturer and notes are optional, default null; trimmed blank
  becomes null. There is no required manual part number or catalog reference.
- quantity defaults to 1 when omitted, otherwise must be a strict integer
  1 through 2147483647. Explicit null is invalid. No invented lower maximum.
- Reject browser-supplied ownership, parent IDs, part_id, category, prices,
  timestamps and all other extras. Parent identity comes from the scoped path.
- Identical snapshots are allowed; do not add a uniqueness rule or silently
  merge quantities.

Exact lookup input:

```json
{"manufacturer":"Example Manufacturer","part_number":"EXAMPLE-123"}
```

Both fields are required, Unicode-safe nonblank strings. Preserve their exact
case and spelling, including valid surrounding characters; do not trim, casefold,
normalize Unicode, tokenize or substitute them for equality matching. The UI
must not silently normalize them either. Lookup names no real catalog seed.

Reviewed catalog preview has exactly these required fields:

```json
{"id":123,"manufacturer":"Example Manufacturer","part_number":"EXAMPLE-123","name":"Example filter","category":"Filters"}
```

Identity strings are Unicode-safe, nonblank, and preserved verbatim. A public
preview and a supplied comparison preview use the same exact identity fields.
Catalog save input is:

```json
{"source":"catalog","preview":{"id":123,"manufacturer":"Example Manufacturer","part_number":"EXAMPLE-123","name":"Example filter","category":"Filters"},"quantity":1,"notes":null}
```

The server re-resolves the exact pair from preview, verifies the catalog ID and
ALL four displayed identity strings against the current locked catalog row, and
uses only that row to supply part_id, name, manufacturer and part_number. Client
preview values serve only as comparison values. Disappearance, replacement by a
new ID, or any identity change returns the fixed conflict and inserts nothing.
Quantity and notes have the same rules as manual input. No signed preview,
new persistence field, automatic refreshed save or implicit manual fallback.

Do not reapply manual trimming to catalog rows or stored public values. Preserve
valid stored Unicode and exact snapshot text on reads; optional stored text is
a string or null without rewriting it. App-created manual blanks become null.
Required public name remains valid nonblank text. Do not use JavaScript trim
for Python's whitespace contract; preserve the prior Unicode repair behavior.

### API shapes and authorization

Let the prefix be `/api/vehicles/{vehicle_id}/services/{service_id}/parts`.

| Method/path | Input | Success |
| --- | --- | --- |
| GET prefix | No body or mutation headers | 200 list envelope below |
| POST prefix/lookup | Exact lookup pair | 200 exact reviewed preview above |
| POST prefix | Manual or catalog create union | 201 complete snapshot below |
| DELETE prefix/{snapshot_id} | Exactly {"confirm_removal":true} | 200 removal result below |

The read-only lookup uses POST to carry its explicit pair as JSON, not as a
browsing query. Apply the existing mutation policy to it, but perform only
read-only catalog queries. No public catalog/browse endpoint is added.

Every handler reuses require_authenticated_session. Authenticate and resolve the
owned vehicle/service before looking up catalog details or returning snapshots.
Scope service access through service ID, vehicle ID and the trusted actor's
user ID. Scope snapshot queries additionally by snapshot ID where applicable.
Never accept user_id/owner_id or perform an unscoped existence probe.

List success has exactly:

```json
{"vehicle_id":7,"service_record_id":8,"parts":[]}
```

An owned service with no snapshots returns an empty array. Order snapshots by
id ASC, because the table has no timestamp and stable insertion order is enough.
Every item must match the envelope's service_record_id.

Snapshot success has exactly:

```json
{"id":9,"service_record_id":8,"part_id":null,"name":"Oil filter","part_number":null,"manufacturer":null,"quantity":1,"notes":null}
```

All listed response keys, including nullable ones, must be present. Return no
owner identity, cost, category, origin or invented timestamp. Manual snapshots
have part_id null; catalog snapshots retain the reference until it is removed.

Confirmed removal success has exactly:

```json
{"id":9,"service_record_id":8,"deleted":true}
```

Confirmation requires the literal JSON boolean true, rejecting omitted/null,
false, 1, strings and extra fields. It is request-only and never stored.
Cancel sends no request. Repeated removal returns the ordinary snapshot 404;
do not claim a later 404 proves which earlier request removed it.

### Transactions and races

Use direct parameterized psycopg only, explicit columns and bound variable
values. Read-only list/lookup transactions must still validate the parent.
For attachment and removal, first select the owner-scoped service row
FOR UPDATE OF s, matching Feature 5's service-removal lock. No child or catalog
lock may replace that parent ownership/serialization step.

Catalog create then resolves the pair and takes a row lock that prevents its
identity fields changing or the row disappearing until snapshot copy commits
(FOR SHARE is sufficient). Compare the supplied ID/identity after this lock.
Keep the order parent service, then catalog row, then snapshot insert. Removal
locks the owned parent before finding/deleting its exact child; it does not
lock or delete the catalog entry.

If attachment commits first, a waiting service removal rechecks linked data and
returns Feature 5's conflict. If service removal commits first, a waiting
attachment finds no owned parent and cannot commit. A committed attachment must
never be silently removed by the service FK cascade. Prove both orderings using
native locks and PostgreSQL blocking evidence. Catalog row changes/deletion
after a completed copy affect only the optional reference, not snapshot text.

Build and validate public results and the JSON response inside the transaction,
commit and close, then return success. Roll back and close before translating
known failures. Failed preview comparison, missing parent, preparation failure
or known rollback writes nothing. Uncertain commit/connection acknowledgment
cannot promise rollback and must never cause an automatic retry.

Adding/removing snapshots never updates service_records values, maintenance
completion links, vehicles readings or readings_updated_at. Cost remains the
service total; no snapshot cost is added or recomputed.

### Safe errors, headers and privacy

| Condition | Response |
| --- | --- |
| Invalid IDs/body/fields/quantity/confirmation | Sanitized 422 detail entries, fixed approved locations/messages/types only |
| Missing or foreign-owned vehicle | 404 {"detail":"Vehicle not found."} |
| Missing, foreign-owned or wrong-parent service | 404 {"detail":"Service record not found."} |
| Missing, foreign-owned or wrong-parent snapshot under an owned service | 404 {"detail":"Part snapshot not found."} |
| Exact catalog lookup has no match | 404 {"detail":"Catalog part not found. Look it up again or enter the part manually."} |
| Reviewed catalog identity changed/disappeared/replaced | 409 {"detail":"Catalog part changed or is no longer available. Look it up again or enter the part manually."} |
| Invalid/missing session | Existing fixed 401 and unusable-cookie deletion |
| Mutation policy rejected | 403 {"detail":"Request not allowed."} |
| Authentication unavailable | 503 {"detail":"Authentication unavailable. Please try again."} |
| Snapshot/catalog business query unavailable | 503 {"detail":"Service parts unavailable. Please try again."} |
| Unexpected failure | 500 {"detail":"Internal server error"} |

Missing and foreign resources at the same ownership boundary must have identical
status and fixed body. Always authorize the parent before catalog miss/conflict
classification. Malformed JSON, unknown union tags, nested preview extras and
ownership fields must not echo raw input. Keep whitelist handling focused on
these fields; never broaden credential-specific validation logic.

Use exact trusted Origin, application/json with ordinary charset parameters,
and X-GarageGuide-CSRF: 1 for POST and DELETE, enforced before body parsing or
business writes. GET needs no mutation headers. Add no permissive CORS.
Cache-Control: no-store applies to all snapshot/lookup responses and errors,
including applicable routing responses. Attach
X-GarageGuide-Session-Expires-At only to successful 200/201 responses using the
already committed actor deadline and reusable helper. No extra session query,
deadline fabrication, token issuance, cookie creation or session-algorithm change.

Do not log or echo snapshot values, lookup pairs, previews, request bodies,
ownership data, SQL/driver details, credentials, hashes, cookies or tokens.
Render text through ordinary escaped React text nodes, never raw HTML.

### Frontend behavior and uncertain outcomes

Extend `/vehicles/:vehicleId/services/:serviceId`, already protected through the
shared route definitions and React Router matching. Add no new page or route.
Preserve encoded/case/trailing-slash handling and Back/Forward protection.

Provide loading, empty, populated, validation, unavailable/retry, denied/not-found,
lookup-miss, stale-preview conflict, success and unexpected-response states.
Users explicitly select manual entry or exact lookup; an empty catalog leaves
manual entry fully usable. No match offers an explicit switch; it never silently
turns a catalog attempt into manual save. Display the exact preview before save.
Changing the lookup pair invalidates it. A 409 invalidates the preview and asks
for a deliberate new lookup or explicit manual switch, with no automatic save.

Quantity begins at 1. Label all fields, errors and optional values; distinguish
unknown optional text from recorded values. Do not label catalog use as verified
vehicle compatibility. When part_id becomes null, show the preserved details
without inventing the snapshot's original source. Removal uses an inline,
keyboard-accessible confirmation panel with explicit confirm and cancel actions.
Explain remove-and-re-add correction and never send an update on cancel.

Keep saved snapshots, drafts, lookup inputs and preview separate. Preserve
correctable drafts while the session remains valid. Use a synchronous in-flight
guard and disabled pending controls for duplicate prevention. Every write uses
relative URLs, credentials: same-origin, JSON/CSRF headers, the existing
ten-second timeout and cancellation; no automatic mutation retries. Keep new
request validation independent so F-04's existing helpers are not repaired here.

After confirmed add/remove, deliberately reload the part list and retain an
explicit required-refresh flag until it succeeds. Do not conflate that flag
with form validation. A failed refresh blocks another write; a successful refresh
must not let a later corrected draft remain blocked by stale form state.

If add may have committed without a response, warn that the original request may
still finish and another add can duplicate it. Require deliberate list reload
and inspection of identity, quantity and notes before another submission; an
absent entry is not proof of failure. Unlocking requires explicit acknowledgment
and never itself submits. An uncertain removal similarly requires deliberate
reload/inspection; current absence proves only current absence. If still present,
require a new explicit confirmation before another DELETE. Cancellation and
timeout cannot claim rollback.

Use existing session and resource generations, not user-ID equality alone.
Cancel/ignore work for old vehicle/service, superseded lookup/list, changed
authentication generation, logout/relogin, account change, expired session,
route departure, hidden/departed page or disposal. Clear private snapshots,
drafts and previews on session loss; late results cannot restore them.
Accept a successful response deadline only for the current session/request
generation and only if valid and newer. Errors or absent/older/malformed
deadlines do not extend it. At local deadline equality clear identity and private
parts without a network request. Do not poll, auto-retry, or call the session
endpoint solely to synchronize deadlines; PostgreSQL remains authoritative.

Preserve accessible labels, visible keyboard focus, first-error focus and error
associations, live status announcements, focus restoration after confirmation
cancel/removal, responsive cards/forms, and 200% zoom behavior.

## Testing

Step 1 is strictly database-free. Use the existing forbid_database fixture and:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_part_schemas.py -p no:cacheprovider
```

Add logic tests alongside later query/API/state changes. The full database-free
backend gate remains:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pip check
```

The existing frontend command has eleven files. When the two new suites exist,
run all of them explicitly, not just the new ones:

```powershell
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js frontend/tests/servicePartApi.test.js frontend/tests/servicePartState.test.js
npm --prefix frontend run lint
npm --prefix frontend run build
```

Use the existing fnm Node and backend virtual environment; install nothing.
There is no combined Verify or configured browser-test command. Source inspection
and builds do not prove browser/persisted behavior. Record tests only after they
actually run, keeping current baseline counts separate from later feature totals.

Native tests require a separately approved step containing native verification,
RUN_DB_TESTS=1, only backend/.env.test, effective database exactly
garageguide_app_test, and SELECT current_database() as the first statement on
every new physical test connection before exposing it. Never connect to
garageguide_app, postgres, or another database. Do not initialize or alter schema.

Use unique synthetic owned users/vehicles/services and synthetic catalog rows
reserved before writes. Track immutable IDs and exact ownership independently
of mutable catalog text; reserve safe uncertain-commit recovery before writes.
No fixture may claim or edit an ordinary catalog row or ordinary service.
Delete exact snapshots/other fixture-owned linked children before their services,
vehicles and users; delete only exact fixture-owned catalog rows after reference
cleanup. Respect existing fixture child ordering and foreign keys. Verify exact
absence through separate guarded connections. No truncation, broad/prefix
deletion, forced cascade, sequence reset, or schema setup. A guard/cleanup failure
stops testing and implementation rather than switching databases.

Cover both users, wrong parents, each allowed model combination, case-sensitive
lookup, no match, stale/deleted/replaced previews, catalog mutation after save,
safe errors/headers, commit/rollback/closure, lost acknowledgments, and real
two-connection attachment/removal locking in both orders. Preserve Feature 1-5
registration/session/vehicle/service/health and F-01 through F-03 regressions.
Do not alter F-04's status or tests as an incidental cleanup.

Browser evidence must include development and production preview with the guarded
test backend, reserved synthetic accounts/catalog, and exact verified cleanup.
Record the browser version, date, performer, observed cases and limitations.
Distinguish real backend behavior from DevTools simulations. Do not claim an
agent browser run or a repeated native run when evidence is user-provided/reused.
When browser execution is unavailable, provide exact manual steps, mark pending,
and wait for observations before final acceptance. No token/password screenshots
or storage, logged cookies, ordinary-account fixture writes, or real catalog seed.

## Notes for the AI

- This is planning only. The single specification write activates the approved
  contract for final review, not implementation or branch creation.
- Preserve the four steps and explicit approval stop after each. The user must
  authorize Step 1 against this active file before code begins.
- Keep build-plan.md, existing evidence/archives, carried-forward F-04, and
  project-wide settings unchanged during feature implementation.
- Copy catalog fields from the rechecked server row only. Preview comparison is
  not ownership and is not permission to store client preview text.
- Manual entry must work without a catalog. No catalog browse, saved-parts,
  compatibility, expense, schedule, or other later-feature work is included.
- No schema, runtime, dependency, staging, commit, audit, completion, landing or
  push action follows from this planning command.
