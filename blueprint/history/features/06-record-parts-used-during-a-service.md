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


<!-- blueprint:completion {"schemaVersion":2,"specBytes":40483,"specSha256":"93562657bd53ebef916aed04e95f7b84ce461f833f3363df83481ac8a14943c9","branch":"refs/heads/feature/record-parts-used-during-a-service","head":"4e18b1bf75c122bb4913418ebce6612eaee09968","baseRef":"refs/heads/main","baseCommit":"a55857122368529eba9481ff4613abdc94285716","sourceTree":"7a71c3d4416324d0632a416164d2f1edc0a55e78","landing":"local-merge","absentOptional":[]} -->

## Findings

### 6/F-05 [P1] closed - Fixture cleanup can adopt a second snapshot with the same name

**File:** backend/tests/database_support.py:411
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** Browser fixtures reserve a user-entered snapshot name under a synthetic service. Once that tuple is reserved, any additional row with the same parent and name passes the guard, even after the original write succeeded and its sole returned ID was tracked. Teardown independently recovers every matching row at line 532 and targets each ID for deletion at line 575. In a database-free check using the existing mocked connections, one write registered ID 22. A subsequent read also returned ID 23 from a separate writer under the same parent/name. The guard added 23 to the tracked set, and the mock cleanup issued DELETE for both IDs. The guard therefore permits deleting another writer's row in the guarded test database. No actual database deletion was performed or observed.
**Suggested fix:** For caller-named snapshot fixtures, record the ID from the insert result during response preparation, before commit, with its exact parent/owner. Use that identity for lookup and recovery even if the acknowledgment is lost. Make the guard and teardown stop on an unexpected same-name ID. Keep support for two genuinely fixture-created identical snapshots by tracking each returned ID. Add a database-free regression covering an unrelated same-name row, acknowledged duplicates, and uncertain commit recovery.
**Resolution:** The November 20 repair stops both browser inspection and teardown from adopting unknown same-name IDs. Browser inserts, the native query helper and direct linked-fixture SQL capture returned IDs before commit. Distinct acknowledged duplicates, rollback and lost acknowledgment are covered by focused tests and the 12-case native evidence. One writer still needs the repair. In backend/tests/test_service_part_api_integration.py:55 and :65, the positive API test checks headers (including a separate database read) before its first capture of either returned ID. A reviewer-run database-free invocation of that test body simulated a committed response and a failed header assertion. The reservation existed, the ID map was empty and the guarded finalizer stopped without issuing any DELETE. The previous name-based recovery masked this gap. Exact cleanup of the test-owned snapshot and parents is now unavailable when the response or intervening assertion fails. Keep this finding open for that recovery regression. Capture the ID in the endpoint query preparation callback for both positive API writes, as the failure-injection API cases already do, and cover a post-commit assertion/response failure. Keep the unknown-ID refusal in place.

Fresh gpt-6.1-sol review on November 20 independently retains P1/open at checkpoint 8eb3b63cad61649ea702f0f98d9c3cba65ef66d4. The reviewer invoked the real positive native API test body with mocked responses and database access forbidden. Its initial list passed, the simulated committed POST returned, and the next header assertion failed before track_part_snapshot ran. One reservation remained with an empty ID map. Calling the real linked finalizer with that committed ID raised Unexpected snapshot ID with zero mock DELETEs. The repaired unknown-ID refusal is correct and was not bypassed, but assertion/response failure can still strand the test's own data and prevent the required exact cleanup. This is an explicit failure-recovery contract gap, not a production persistence bug. The separate failure-injection API cases already capture the ID before commit; the ordinary positive test must do the same for both inserts.

Independently closed at 4e18b1bf75c122bb4913418ebce6612eaee09968 on 2026-11-21 UTC (November 20 local) by fresh Codex gpt-6.1-sol review. Both positive native API POSTs now call remember_part_snapshot immediately on receipt, before assert_headers, database verification or later assertions. The reviewer executed both database-free real-test-body regressions: later manual/catalog header failures leave exactly IDs 22 / 22 and 23 available to the real mocked linked finalizer, which deletes only those IDs. The unchanged browser/query/direct-SQL and API fault-injection writers retain pre-commit callback capture. Discovery still rejects unknown same-name IDs; separately acknowledged duplicates, rollback and lost acknowledgment retain exact identities. Reused the approved seven-case native result, including both later-assertion paths with separate exact absence verification, and prior unchanged 12-case refusal/duplicate/uncertain-commit evidence. A response lacking a usable returned ID still cannot prove ownership and must stop safely instead of guessing. This closes the original adoption defect and its later-assertion recovery regression; no new ownership bypass was found.


### 6/F-06 [P1] closed - Reload feedback can claim a mutation committed after a removal returned 404

**File:** frontend/src/servicePartState.js:145
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** If a snapshot disappears after the list is displayed, DELETE returns the fixed snapshot 404. The store sets the same refresh flag used after confirmed writes. When the user reloads and the list request fails, the live status says "The change committed". A reviewer-run Node fixture observed exactly one DELETE, a snapshot-missing result and an unavailable list result followed by this claim. In a second check, a successful earlier addition followed by a snapshot 404 and successful manual reload reported "Part snapshot added" again. The current removal received no success acknowledgment. Both paths misattribute an outcome while the user is inspecting history.
**Suggested fix:** Use neutral reload feedback when the snapshot was already absent. Associate commit feedback with the specific confirmed mutation and consume it on its own refresh. Cover both failed and successful reloads following a snapshot 404, including after an earlier successful mutation.
**Resolution:** Independently verified on November 20 at 8eb3b63cad61649ea702f0f98d9c3cba65ef66d4. A confirmed mutation sets the feedback marker, its first successful refresh consumes it, and a snapshot 404 clears it. Reviewer-run Node cases covered 404 followed by successful and failed reads, with and without a prior Add, confirmed writes with failed refresh, uncertain writes and single-dispatch guards. User-reported focused checks in development and production preview observed one write per scenario and no replay on ordinary reload. F-08 describes separate prompt cancellation behavior that existed before this repair.

Fresh gpt-6.1-sol review independently reconfirmed closed on November 20 at the same checkpoint. A reviewer-run inline Node probe exercised all four combinations of prior Add present/absent and post-404 reload success/failure using the existing store fixture. Each result used neutral list feedback, retained refreshRequired only for a failed reload, dispatched exactly one DELETE and no replay, and dispatched an Add only when deliberately requested. Full state/API inspection confirms the refresh marker is set by acknowledged writes, consumed by successful refresh and cleared by snapshot 404. Existing confirmed/uncertain regression results are reused separately from this probe.


### 6/F-07 [P1] closed - Catalog teardown can delete an unrelated replacement at a reserved pair

**File:** backend/tests/database_support.py:478
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** The fixture creates a UUID-tagged manufacturer/part-number pair and exposes it during the browser workflow. Once its row is deleted or its pair edited, another writer can reuse that known pair. Uniqueness applies only to rows that currently exist. Teardown adds every ID found at the pair to its owned set, then deletes an unreferenced row by ID. In a database-free finalizer probe, fixture ID 22 was absent and the same pair returned replacement ID 23. Cleanup added 23 to the tracked IDs and issued a mock DELETE for 23. This requires reuse of the exact known pair in the guarded test database. No real row was touched.
**Suggested fix:** Capture catalog INSERT RETURNING IDs before commit at fixture create/replace call sites. Keep those IDs through acknowledgment loss and catalog edits. Treat an unknown ID found at a reserved pair as grounds to stop cleanup, preserving the foreign row. Cover the replacement and genuine fixture-created replacements with database-free tests.
**Resolution:**

Fresh gpt-6.1-sol review independently retains P1/open on November 20 at checkpoint 8eb3b63cad61649ea702f0f98d9c3cba65ef66d4. A reviewer-run database-free probe invoked _delete_catalog_fixtures with tracked ID 22 absent and another writer's ID 23 at the exact reserved pair. The real finalizer added 23 and issued the mock DELETE for 23 after finding no references. P1 is based on the explicit rule to delete only test-created immutable identities, not a claimed random UUID collision, production threat model or observed real deletion. This requires deliberate reuse of the exposed exact pair after the fixture row moves/disappears. The reservation can detect an unexpected row but cannot establish its ownership. Pre-commit capture plus refusal of unknown IDs is the bounded repair and preserves genuine fixture replacements and acknowledgment-loss recovery.

Independently closed at 4e18b1bf75c122bb4913418ebce6612eaee09968 on 2026-11-21 UTC (November 20 local) by fresh Codex gpt-6.1-sol review. All five fixture catalog INSERT call sites capture their own RETURNING ID through remember_catalog_part before transaction exit: terminal create/replace, create_catalog, native API replacement and native query replacement. The registry requires a reserved exact pair and a strict returned integer ID, refuses reassignment, and survives rollback/lost acknowledgment. The pair discovery scan only checks already-known identities and raises on an unknown replacement; it never adds or deletes that unknown ID. Known rows are cleaned by immutable ID after edits, with reference checks and separate guarded absence verification. Reviewer-run focused database-free cases independently passed unknown replacements with/without an original, exact known replacements, mutable-identity cleanup, lost acknowledgment and terminal capture ordering. Reused approved native unknown-replacement preservation, catalog lifecycle, both raw replacements and edited-identity cleanup cases, all passing with exact receipts. The expected native refusal restores only its own deliberately hidden ID in finally before final cleanup. No unrelated-row deletion or new defect was found.



## Independent review

# Independent Review

**Status:** passed
**Target commit:** 4e18b1bf75c122bb4913418ebce6612eaee09968
**Base commit:** a55857122368529eba9481ff4613abdc94285716
**Base ref:** main
**Spec hash:** 93562657bd53ebef916aed04e95f7b84ce461f833f3363df83481ac8a14943c9
**Prepared by:** codex
**Builder model:** gpt-6.2-sol
**Requested reviewer:** codex
**Requested model:** gpt-6.1-sol
**Requested execution:** automatic
**Requested at:** 2026-11-21T02:54:51.789583+00:00
**Workflow:** regular
**Check required:** no

**Reviewer adapter:** codex
**Reviewer model:** gpt-6.1-sol
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-21T02:59:43+00:00
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** passed
**Check result:** not-required

## Commands

- Reviewer ran `git status --short --untracked-files=all`, `git rev-parse HEAD`, `git merge-base main HEAD`, `git branch --show-current`, `git ls-tree HEAD -- blueprint/context/current-feature.md`, `git ls-files --stage -- blueprint/context/current-feature.md`, `Get-FileHash blueprint/context/current-feature.md -Algorithm SHA256`, `git diff --stat a55857122368529eba9481ff4613abdc94285716..HEAD`, `git diff --name-only a55857122368529eba9481ff4613abdc94285716..HEAD` and `git diff --check main...HEAD`: passed. HEAD/base/spec bindings match; only findings.md and review.md differ from target.
- Reviewer ran `backend/.venv/Scripts/python.exe -B -m pytest -q -c backend/pyproject.toml backend/tests/test_service_part_api_fixture_safety.py backend/tests/test_service_part_fixture_safety.py::test_unknown_catalog_replacement_stops_cleanup_without_adoption_or_deletion backend/tests/test_service_part_fixture_safety.py::test_fixture_created_catalog_replacement_is_known_before_ack_and_cleaned_by_exact_ids backend/tests/test_service_part_fixture_safety.py::test_catalog_only_cleanup_keeps_precommit_id_after_lost_ack_and_uses_separate_verification backend/tests/test_service_part_fixture_safety.py::test_catalog_cleanup_uses_tracked_id_after_identity_edits backend/tests/test_manual_service_parts.py::test_browser_catalog_insert_captures_exact_id_before_commit_or_lost_ack -m 'not integration' -p no:cacheprovider --tb=short`: 12 passed in 0.19 seconds, one existing Starlette/AnyIO deprecation warning. The selected files use forbid_database; no database connection was made.
- Reviewer ran `backend/.venv/Scripts/python.exe -B -` with inline pathlib/hashlib/JSON/ElementTree/subprocess validation: all nine repair raw hashes, five preserved native artifact hashes, final-results hash and exact Git repair patch matched the checkpoint proposal. Exactly seven approved JUnit nodes matched the executed command and seven cleanup receipts, with no failures/errors/skips and totals 14 users, 14 sessions, 7 vehicles, 7 services, 6 snapshots and 10 catalog IDs absent. The earlier original and repair XML also parsed as 537 and 12 cases with zero failures/errors/skips. These were artifact reads, not native reruns.
- Reviewer used `Get-Content`, targeted `rg` and `git diff` reads for the complete delta, affected writers/callers and contracts. The corrected `rg -g` search found no skip/xfail/only/todo/placeholder declarations in Feature 6 tests. An initial Windows wildcard-path rg invocation failed and was replaced with directory roots and -g filters; no verification remained blocked by that invocation.
- Reused, not run by this reviewer: exact-repair focused command recorded in docs/verification/SERVICE_PARTS_STATUS.md and blueprint/.state/staging/feature-6-f05-f07-repair/repair-review.md, selecting test_service_part_api_fixture_safety.py, test_service_part_fixture_safety.py, test_manual_service_parts.py and test_manual_registration_server.py with `-m "not integration" -p no:cacheprovider --tb=short`: 110 passed in 2.11 seconds. Its code is unchanged and all repair hashes match. The reviewer's 12 selected passes are independent corroboration, not an additive suite total.
- Reused, not run by this reviewer: the seven approved native nodes in blueprint/.state/staging/feature-6-f05-f07-repair/native-executed-command.json, 7 passed in 17.69 seconds, and prior 12-case native repair, 12 passed in 51.31 seconds. No full suites, PostgreSQL, server, browser, install or network command was run in this review.
- Reused unchanged product evidence recorded in docs/verification/SERVICE_PARTS_STATUS.md and the historical independent receipt: Step 4 backend 2660 passes, all 13 Node files 978 passes, pip check, lint and build passes; original native 537 passes; earlier fresh-reviewer focused backend 393 passes and frontend API/state 210 passes; repair lint/build passes. These were run before this test-only checkpoint, not during this review.

## Evidence

- Fresh generic isolated Codex subagent without the builder transcript, explicitly selected gpt-6.1-sol with high reasoning. Reviewed all 32 changed paths in a55857122368529eba9481ff4613abdc94285716..4e18b1bf75c122bb4913418ebce6612eaee09968 across quality, security, performance and tests, including the complete active spec, product models/queries/routes, guarded fixtures/server, all new and affected tests, React components, API/state/validation, styles and both verification documents. Nearby service-removal locks, authoritative SQL constraints/indexes, database context, authentication/CSRF/deadlines and session generations were inspected. Audit records were excluded from application scope; dependencies, generated/build/cache files and unrelated source were excluded. Applied AGENTS.md, coding standards, project overview, config, active spec and installed Audit/independent-review contract.
- Quality/security: strict input/public shapes and Unicode behavior match the contract; parent ownership precedes catalog classification; parameterized SQL binds owner and parents, locks the owned service before mutation and the catalog before preview comparison/copy, and copies only locked server values. Response preparation/serialization occurs before transaction exit; success is returned only after commit/closure, safe errors omit private data, and uncertain writes are not retried. Routes reuse pre-body policy, authentication, no-store and committed successful deadlines. No schema/dependency/session-algorithm change was added. React escapes stored text and preserves explicit manual selection, preview review and confirmation.
- Performance: owner/service lookup uses existing indexes and bounded query count, one ordered snapshot read and linear parse/render work. No N+1, polling, automatic retry, extra deadline-only session request or new dependency was introduced. No unsupported scale or pagination requirement was inferred. Runtime performance profiling was not available or required.
- Tests: source review covers strict models, scoped SQL/transactions, safe HTTP boundaries, lifecycle races with PostgreSQL blocking evidence, snapshot history, stale previews, confirmation, uncertainty/refresh, duplicate prevention, auth/resource/request generations, local expiry and private-state clearing. Current F-05/F-07 regression tests assert real finalizer calls and ownership registries independently of swallowed request assertions. All five catalog INSERT sites now remember returned IDs before commit; both positive API response IDs are remembered before later assertions. Unknown matching IDs cause refusal without adoption/deletion; own replacements, identity edits, rollback/lost acknowledgment and exact separate cleanup verification remain supported. Missing usable response IDs fail safely instead of claiming ownership.
- Preserved seven-case native evidence has exactly the approved nodes, 7 passes in 17.69 seconds and seven exact receipts. It covers both later API assertion failures, unknown catalog replacement preservation/refusal, known catalog lifecycle, both raw replacement call sites and mutable-pair cleanup. Totals 14/14/7/7/6/0/0/10 are tracked identities verified absent through separate guarded connections, including removed/rolled-back IDs, not global deletion counts. Effective/physical garageguide_app_test, .env.test, RUN_DB_TESTS and first-statement guards are recorded and remain enforced in source. Earlier 12-case repair evidence covers same-name refusal, duplicates and uncertain-commit recovery; original 537 native passes remain historical product/regression evidence.
- Reused user-performed November 20 browser evidence separately: the complete original development/production-preview checklist included the full visible idle-deadline observation; the focused F-05/F-06 repair recheck in both modes used Chrome 157.0.8103.79 and reported one write per scenario, honest ordinary/404/confirmed/uncertain feedback and exact catalog-inclusive cleanup. Real guarded writes/reloads are distinguished from simulated 404/503/lost acknowledgments. No reviewer browser execution or repeated full idle check is claimed. The current checkpoint changes only fixture/test code and its record, so unchanged product evidence is reused under the user's instruction.

## Findings

- F-05 [P1] closed. Both ordinary native API response IDs are recorded before header/database assertions; reviewer-run real-test-body failure regressions retain and clean only the exact acknowledged IDs. Unknown same-name IDs remain rejected. Resolution records the new review and reused native evidence.
- F-07 [P1] closed. All catalog fixture INSERTs capture exact IDs before commit, pair scans reject unknown replacements without adoption/deletion, and known replacement/edit/lost-ack cleanup remains exact. Resolution records the new review and corroborating evidence.
- F-06 [P1] remains closed, byte-for-byte unchanged. Source and unchanged tests preserve mutation-specific feedback and neutral snapshot-404 reloads; prior independent and user evidence is reused.
- F-04 and F-08 [P2] remain open, byte-for-byte unchanged and nonblocking. No finding was accepted or reclassified; no new finding was confirmed across the complete four-lens delta. The remaining P2 repairs require separate scope.

## Remaining risk

- No fresh PostgreSQL/native integration, guarded backend/dev/preview server or browser command was available within this review's explicit no-database/no-server/no-browser boundary. Recorded native/browser evidence was reused as attributed above; no repeat is claimed. No configured Browser tests command exists. UI accessibility/layout relies on source inspection and user observations, not reviewer runtime exercise.
- No typecheck, combined Verify or performance command is configured. No full backend/frontend suite rerun, pip-check rerun, lint/build rerun, network-backed `npm --prefix frontend audit`, install or performance benchmark ran for this fixture-only repair. Existing unaffected evidence remains separately dated/scoped; no current vulnerability scan is claimed.
- A response lacking a usable returned snapshot ID cannot establish fixture ownership. Cleanup deliberately stops rather than adopting a same-name row; recovery must resolve that exact uncertain fixture before testing continues. Unknown-row native tests temporarily hide only their own IDs and restore them in finally; they do not touch an unrelated writer's real data.
- F-04/F-08 remain known nonblocking P2 limitations. No open/fixed P0 or P1 remains. Check was not required by the request/configuration. The passing independent receipt does not authorize completion, commit, merge, push or deployment.

## Carried-forward findings (open P2)

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

## Implementation commit history

- f84e348cd8c88b181b69da0bfb7148cabb51a665 feat: record parts used during a service
- 8eb3b63cad61649ea702f0f98d9c3cba65ef66d4 fix: track exact snapshot IDs and correct reload feedback
- 4e18b1bf75c122bb4913418ebce6612eaee09968 fix: preserve exact fixture ownership during cleanup

## Original changes-requested receipt (historical)

# Independent Review

**Status:** changes-requested
**Target commit:** f84e348cd8c88b181b69da0bfb7148cabb51a665
**Base commit:** a55857122368529eba9481ff4613abdc94285716
**Base ref:** main
**Spec hash:** 93562657bd53ebef916aed04e95f7b84ce461f833f3363df83481ac8a14943c9
**Prepared by:** codex
**Builder model:** unknown (runtime did not expose exact model)
**Requested reviewer:** codex
**Requested model:** gpt-6.2-astra
**Requested execution:** automatic
**Requested at:** 2026-11-20T21:36:17.287127+00:00
**Workflow:** regular
**Check required:** no
**Reviewer adapter:** codex
**Reviewer model:** gpt-6.2-astra
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-20T21:40:19.746803+00:00
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** changes-requested
**Check result:** not-required

## Commands

- `git rev-parse HEAD main`, `git merge-base HEAD main`, `git ls-files --stage -- blueprint/context/current-feature.md`, `Get-FileHash -Algorithm SHA256 blueprint/context/current-feature.md` and `git status --short --branch --untracked-files=all` passed the checkpoint, tracked-spec and allowed-path checks.
- `git diff --check main...HEAD` passed. The full range includes 28 files. Local Python SHA-256 comparison against the archived passing candidate matched all 25 backend and frontend source/test files.
- `backend/.venv/Scripts/python.exe -m pytest -q -c backend/pyproject.toml backend/tests/test_service_part_queries.py backend/tests/test_service_part_api.py backend/tests/test_service_part_fixture_safety.py backend/tests/test_manual_service_parts.py -m "not integration" -p no:cacheprovider --tb=short` passed all 319 cases. One existing Starlette/AnyIO deprecation warning.
- `node --test --test-reporter=spec frontend/tests/servicePartApi.test.js frontend/tests/servicePartState.test.js` passed all 201 cases, with zero failures, skips or cancellations, using the installed Node 22.23.4.
- `backend/.venv/Scripts/python.exe -B -` with repository fixture doubles reproduced F-05. Only one returned ID had been tracked. The scan adopted a second same-name ID and mock cleanup targeted both.
- `node --input-type=module` with the repository service-parts fixture reproduced F-06. After a snapshot 404, failed reload announced a commit. Successful reload following an earlier add repeated the earlier add announcement.

## Evidence

- Fresh review covered the complete Feature 6 delta, the existing service-delete and database/session boundaries it reuses, the SQL constraints and indexes, visible page and store integration, and the guarded fixture lifecycle. Project React, FastAPI, data-fetching, database and testing standards were checked. New tests contain no skip, only or placeholder declarations.
- Parameterized SQL scopes reads and writes by actor, vehicle and service, and by snapshot ID on removal. Writes lock the service before touching children. Catalog save locks the exact pair, compares the ID and all displayed fields, and copies server-row identity. Lists read the historical snapshot and use the service index and stable ID order. No additional request per listed part. Response preparation happens inside the transaction. API routing and tests cover fixed errors, origin/CSRF/JSON handling, privacy, no-store and success-only deadline headers.
- Client review covered exact public shapes, session and route generations, cancellation, deadline monotonicity, required refresh, uncertainty, explicit confirmations and existing-page controls. Accessible labels and focus associations were inspected alongside the user-reported browser evidence.
- Reused automated evidence from `docs/verification/SERVICE_PARTS_STATUS.md` and `blueprint/.state/staging/feature-6-step-4/verified-results.json` records 2,660 database-free backend and 978 Node passes, successful lint/build and pip check. The reviewer executed only the focused suites and probes above.
- Reused November 19 native JUnit and cleanup JSON record 537 passes, zero failures/errors/skips, both service deletion/attachment lock orderings, the catalog lock across copy and commit, history after catalog changes/deletion, and transaction faults. The 535 exact cleanup receipts cover 978 users, 944 sessions, 460 vehicles, 288 services, 50 snapshots, 19 completions, 20 schedules and 30 catalog entries. The other two cases performed read-only checks.
- Reused user-performed November 20 browser checklist in `docs/verification/BROWSER_CHECKS.md` and the status document covers development and production preview, browser version 157.0.8103.79, the full visible idle-deadline check and catalog-inclusive exact cleanup. Browser-simulated outages and lost acknowledgments are distinct from real backend operations.

## Findings

- F-05 [P1] open at `backend/tests/database_support.py:411`. Same-name snapshot adoption can target an unrelated test-database row for deletion. Address this fixture issue before using affected cleanup for repair verification.
- F-06 [P1] open at `frontend/src/servicePartState.js:145`. Snapshot-missing recovery can falsely attribute a commit or repeat a prior mutation message.
- F-04 [P2] open at `frontend/src/api.js:427`. Existing direct service-helper finding carried forward verbatim, nonblocking.

## Remaining risk

- F-05 and F-06 block completion. The fixture probe exercised mocked connections. The frontend probe exercised the page's store with simulated results.
- The reviewer did not execute PostgreSQL or a browser. Prior native evidence and the user's confirmed browser checklist apply to the matching checkpoint. No additional per-case browser traces, real lost acknowledgments, or runtime performance measurements were available. No fresh network dependency scan was requested.

## Original findings snapshot (historical)

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

### F-05 [P1] open - Fixture cleanup can adopt a second snapshot with the same name

**File:** backend/tests/database_support.py:411
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** Browser fixtures reserve a user-entered snapshot name under a synthetic service. Once that tuple is reserved, any additional row with the same parent and name passes the guard, even after the original write succeeded and its sole returned ID was tracked. Teardown independently recovers every matching row at line 532 and targets each ID for deletion at line 575. In a database-free check using the existing mocked connections, one write registered ID 22. A subsequent read also returned ID 23 from a separate writer under the same parent/name. The guard added 23 to the tracked set, and the mock cleanup issued DELETE for both IDs. The guard therefore permits deleting another writer's row in the guarded test database. No actual database deletion was performed or observed.
**Suggested fix:** For caller-named snapshot fixtures, record the ID from the insert result during response preparation, before commit, with its exact parent/owner. Use that identity for lookup and recovery even if the acknowledgment is lost. Make the guard and teardown stop on an unexpected same-name ID. Keep support for two genuinely fixture-created identical snapshots by tracking each returned ID. Add a database-free regression covering an unrelated same-name row, acknowledged duplicates, and uncertain commit recovery.
**Resolution:**

### F-06 [P1] open - Reload feedback can claim a mutation committed after a removal returned 404

**File:** frontend/src/servicePartState.js:145
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** If a snapshot disappears after the list is displayed, DELETE returns the fixed snapshot 404. The store sets the same refresh flag used after confirmed writes. When the user reloads and the list request fails, the live status says "The change committed". A reviewer-run Node fixture observed exactly one DELETE, a snapshot-missing result and an unavailable list result followed by this claim. In a second check, a successful earlier addition followed by a snapshot 404 and successful manual reload reported "Part snapshot added" again. The current removal received no success acknowledgment. Both paths misattribute an outcome while the user is inspecting history.
**Suggested fix:** Use neutral reload feedback when the snapshot was already absent. Associate commit feedback with the specific confirmed mutation and consume it on its own refresh. Cover both failed and successful reloads following a snapshot 404, including after an earlier successful mutation.
**Resolution:**

## First repair review by gpt-6.2-astra (historical)

# Independent Review

**Status:** changes-requested
**Target commit:** 8eb3b63cad61649ea702f0f98d9c3cba65ef66d4
**Base commit:** a55857122368529eba9481ff4613abdc94285716
**Base ref:** main
**Spec hash:** 93562657bd53ebef916aed04e95f7b84ce461f833f3363df83481ac8a14943c9
**Prepared by:** codex
**Builder model:** unknown (runtime did not expose exact model)
**Requested reviewer:** codex
**Requested model:** gpt-6.2-astra
**Requested execution:** automatic
**Requested at:** 2026-11-20T23:13:24.170532+00:00
**Workflow:** regular
**Check required:** no
**Reviewer adapter:** codex
**Reviewer model:** gpt-6.2-astra
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-20T23:19:54+00:00
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** changes-requested
**Check result:** not-required

## Commands

- Reviewer ran `git rev-parse HEAD`, `git merge-base main HEAD`, `git ls-tree HEAD -- blueprint/context/current-feature.md`, `git ls-files --stage blueprint/context/current-feature.md`, raw SHA-256, full untracked status and the committed diff. All checkpoint checks passed. The only working tree differences were the two permitted audit records. `git diff --check main...HEAD` passed.
- Reviewer ran `backend/.venv/Scripts/python.exe -B -m pytest -q -c backend/pyproject.toml backend/tests/test_service_part_fixture_safety.py backend/tests/test_service_link_fixture_safety.py backend/tests/test_manual_service_parts.py backend/tests/test_manual_registration_server.py backend/tests/test_service_part_queries.py backend/tests/test_service_part_api.py -m "not integration" -p no:cacheprovider --tb=short`. All 393 cases passed in 14.02 seconds with one existing Starlette/AnyIO deprecation warning. A two-file subset also passed all 53 cases and is included in the 393.
- Reviewer ran `node --test --test-reporter=spec frontend/tests/servicePartApi.test.js frontend/tests/servicePartState.test.js` with the installed Node 22.23.4. All 210 cases passed in 0.62 seconds with zero skipped, canceled or failed.
- Reviewer ran two database-free Python probes using the real native test body or finalizer with mock connections. They confirmed the post-assertion snapshot ID capture gap and adoption of an untracked catalog replacement. A Node store probe confirmed the reload-cancel status defect. Each probe checked the observed commands or request counts. No database statements were sent to PostgreSQL.

## Evidence

- Reviewed all 31 committed paths from the recorded merge base through the target. Scope comprised FastAPI routing, schemas and SQL, native and manual fixture machinery, backend and frontend tests, the React record page and parts UI, API and session state, styles, the active spec and both verification documents. Reviewed affected parent-removal, authentication, session deadline, physical-connection and database schema callers/contracts. The request, ledger, dependencies and build output were outside the code delta.
- Product SQL parameterizes owner, vehicle, service and child IDs. Service row locks serialize attachment and parent deletion. The catalog query locks the exact pair, checks ID and all four preview strings, and copies identity from the server row. Historical list reads use the service index and stable ID order with one list query. Catalog edits preserve copied values and deletion clears the FK. The native race tests check actual PostgreSQL blockers in both parent-removal orders. Response preparation and serialization occur before transaction exit. Routing preserves mutation policy, sanitized errors, no-store, safe cookie handling and success-only deadline headers.
- Client review covered input/response shapes, timeout, explicit confirmation, synchronous request gating, session and route generations, local expiry, monotonic deadlines, blocked overlapping parent/part actions, and live feedback and focus. The focused Node cases cover neutral snapshot-404 recovery, confirmed-write refresh failures, uncertain results without replay and stale completion cancellation. No focused/skip/placeholder declarations were found in the new test suites.
- The original Step 4 JUnit and cleanup artifacts report **537 native passes**, 535 exact cleanup receipts and two read-only cases. The original full frontend/backend and browser checklist, including full idle observation, preceded this repair. Recorded repair lint and build passed. These are reused observations.
- The separately approved repair JUnit, native-cleanup JSON and final-repair-results JSON under `blueprint/.state/staging/feature-6-f05-f06-repair/` show **12 native passes in 51.31 seconds**, zero failures/skips and 12 exact cleanup receipts. Separate guarded connections verified absence of 24 user IDs, 24 sessions, 12 vehicles, 12 services, 14 snapshots and 3 catalog IDs. These counts include already removed or rolled-back fixtures. Every physical connection checks its test database before use.
- The user reported passing the focused repair checks in Chrome 157.0.8103.79 on November 20, 2026 in both Vite development and production preview. They observed ordinary and 404 reloads, confirmed Add/Remove with failed refresh, uncertain Add/Remove, one attempted write per scenario and catalog-inclusive cleanup. Real writes and reloads were observed separately from simulated 404, 503 and lost acknowledgments. The repair recheck did not repeat the full checklist or full idle observation. See `docs/verification/SERVICE_PARTS_STATUS.md` and `docs/verification/BROWSER_CHECKS.md`.

## Findings

- **F-05 [P1] open.** Unknown same-name snapshots now stop cleanup without deletion. The repair leaves the ordinary native API test's two successful writes dependent on post-commit header assertions and response decoding to capture their IDs. An intervening failure leaves the guarded fixture unable to clean its own data. Capture those IDs before commit.
- **F-07 [P1] open, new.** Catalog cleanup can select another writer's unreferenced replacement for deletion if it takes the fixture's exact UUID-tagged catalog pair after the original moves or disappears. A mock finalizer with known ID 22 and replacement ID 23 targeted 23. Capture catalog IDs before commit and reject unknown replacements.
- **F-08 [P2] open, new.** Canceling a reload leaves its question in the live status and can displace the explanation for a confirmed write whose refresh failed. The probe observed one Add and no request on cancel.
- **F-06 [P1] closed.** Snapshot 404 and ordinary reloads no longer replay mutation success. Confirmed refresh failures and uncertain outcomes retain their distinct feedback under the repaired flows.
- **F-04 [P2] open.** Carried forward verbatim and nonblocking.

## Remaining risk

- F-05 and F-07 block this checkpoint. The simulated F-05 failure stops cleanup without deleting an unknown snapshot. F-07 needs a second writer to reuse the exact exposed catalog pair in the guarded test database. No real cleanup failure or unintended deletion was observed. Existing native passes establish their exercised success and failure paths only.
- Live PostgreSQL and direct browser/server runs were outside this review's authorized scope. The native and browser evidence above was reused. There is no configured browser-test command, typecheck or combined Verify command. No network-backed dependency audit or performance benchmark was run. No dependencies changed. Unchanged full suites and the full browser idle check were not rerun for this audit.

## Findings from the gpt-6.2-astra repair review (historical)

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

### F-05 [P1] open - Fixture cleanup can adopt a second snapshot with the same name

**File:** backend/tests/database_support.py:411
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** Browser fixtures reserve a user-entered snapshot name under a synthetic service. Once that tuple is reserved, any additional row with the same parent and name passes the guard, even after the original write succeeded and its sole returned ID was tracked. Teardown independently recovers every matching row at line 532 and targets each ID for deletion at line 575. In a database-free check using the existing mocked connections, one write registered ID 22. A subsequent read also returned ID 23 from a separate writer under the same parent/name. The guard added 23 to the tracked set, and the mock cleanup issued DELETE for both IDs. The guard therefore permits deleting another writer's row in the guarded test database. No actual database deletion was performed or observed.
**Suggested fix:** For caller-named snapshot fixtures, record the ID from the insert result during response preparation, before commit, with its exact parent/owner. Use that identity for lookup and recovery even if the acknowledgment is lost. Make the guard and teardown stop on an unexpected same-name ID. Keep support for two genuinely fixture-created identical snapshots by tracking each returned ID. Add a database-free regression covering an unrelated same-name row, acknowledged duplicates, and uncertain commit recovery.
**Resolution:** The November 20 repair stops both browser inspection and teardown from adopting unknown same-name IDs. Browser inserts, the native query helper and direct linked-fixture SQL capture returned IDs before commit. Distinct acknowledged duplicates, rollback and lost acknowledgment are covered by focused tests and the 12-case native evidence. One writer still needs the repair. In backend/tests/test_service_part_api_integration.py:55 and :65, the positive API test checks headers (including a separate database read) before its first capture of either returned ID. A reviewer-run database-free invocation of that test body simulated a committed response and a failed header assertion. The reservation existed, the ID map was empty and the guarded finalizer stopped without issuing any DELETE. The previous name-based recovery masked this gap. Exact cleanup of the test-owned snapshot and parents is now unavailable when the response or intervening assertion fails. Keep this finding open for that recovery regression. Capture the ID in the endpoint query preparation callback for both positive API writes, as the failure-injection API cases already do, and cover a post-commit assertion/response failure. Keep the unknown-ID refusal in place.

### F-06 [P1] closed - Reload feedback can claim a mutation committed after a removal returned 404

**File:** frontend/src/servicePartState.js:145
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** If a snapshot disappears after the list is displayed, DELETE returns the fixed snapshot 404. The store sets the same refresh flag used after confirmed writes. When the user reloads and the list request fails, the live status says "The change committed". A reviewer-run Node fixture observed exactly one DELETE, a snapshot-missing result and an unavailable list result followed by this claim. In a second check, a successful earlier addition followed by a snapshot 404 and successful manual reload reported "Part snapshot added" again. The current removal received no success acknowledgment. Both paths misattribute an outcome while the user is inspecting history.
**Suggested fix:** Use neutral reload feedback when the snapshot was already absent. Associate commit feedback with the specific confirmed mutation and consume it on its own refresh. Cover both failed and successful reloads following a snapshot 404, including after an earlier successful mutation.
**Resolution:** Independently verified on November 20 at 8eb3b63cad61649ea702f0f98d9c3cba65ef66d4. A confirmed mutation sets the feedback marker, its first successful refresh consumes it, and a snapshot 404 clears it. Reviewer-run Node cases covered 404 followed by successful and failed reads, with and without a prior Add, confirmed writes with failed refresh, uncertain writes and single-dispatch guards. User-reported focused checks in development and production preview observed one write per scenario and no replay on ordinary reload. F-08 describes separate prompt cancellation behavior that existed before this repair.

### F-07 [P1] open - Catalog teardown can delete an unrelated replacement at a reserved pair

**File:** backend/tests/database_support.py:478
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** The fixture creates a UUID-tagged manufacturer/part-number pair and exposes it during the browser workflow. Once its row is deleted or its pair edited, another writer can reuse that known pair. Uniqueness applies only to rows that currently exist. Teardown adds every ID found at the pair to its owned set, then deletes an unreferenced row by ID. In a database-free finalizer probe, fixture ID 22 was absent and the same pair returned replacement ID 23. Cleanup added 23 to the tracked IDs and issued a mock DELETE for 23. This requires reuse of the exact known pair in the guarded test database. No real row was touched.
**Suggested fix:** Capture catalog INSERT RETURNING IDs before commit at fixture create/replace call sites. Keep those IDs through acknowledgment loss and catalog edits. Treat an unknown ID found at a reserved pair as grounds to stop cleanup, preserving the foreign row. Cover the replacement and genuine fixture-created replacements with database-free tests.
**Resolution:**

### F-08 [P2] open - Canceling a parts reload leaves its question in the live status

**File:** frontend/src/servicePartState.js:205
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** Opening the reload confirmation overwrites the current status. Choosing Keep current view closes the panel but leaves its question in the live status. A reviewer-run Node check started with a confirmed Add whose automatic refresh failed. After opening and canceling reload, refresh was still required but the committed-write explanation had been replaced by the question about discarding the preview. One Add and two list calls occurred, including the initial list and failed refresh. Cancel sent no request.
**Suggested fix:** Keep the prompt copy in the confirmation panel and preserve the prior result when the user cancels. Test cancellation after a confirmed write with a failed refresh.
**Resolution:**

## First repair review by gpt-6.1-sol (historical)

# Independent Review

**Status:** changes-requested
**Target commit:** 8eb3b63cad61649ea702f0f98d9c3cba65ef66d4
**Base commit:** a55857122368529eba9481ff4613abdc94285716
**Base ref:** main
**Spec hash:** 93562657bd53ebef916aed04e95f7b84ce461f833f3363df83481ac8a14943c9
**Prepared by:** codex
**Builder model:** unknown (runtime did not expose exact model)
**Requested reviewer:** codex
**Requested model:** gpt-6.1-sol
**Requested execution:** automatic
**Requested at:** 2026-11-20T23:24:03.264462+00:00
**Workflow:** regular
**Check required:** no

**Reviewer adapter:** codex
**Reviewer model:** gpt-6.1-sol
**Reviewer context:** fresh subagent
**Actual execution:** automatic
**Reviewed at:** 2026-11-20T23:29:23+00:00
**Scope:** current
**Lenses:** quality, security, performance, tests
**Verdict:** changes-requested
**Check result:** not-required

## Commands

- This reviewer ran `git status --short --untracked-files=all`, `git rev-parse HEAD`, `git merge-base main HEAD`, `git branch --show-current`, `git ls-tree HEAD -- blueprint/context/current-feature.md`, `git ls-files --stage blueprint/context/current-feature.md`, `Get-FileHash blueprint/context/current-feature.md -Algorithm SHA256`, `git diff --stat main...HEAD`, `git diff --name-only main...HEAD` and `git diff --check main...HEAD`: passed. The spec is tracked, all checkpoint bindings match, and only findings.md/review.md differ.
- This reviewer ran `backend/.venv/Scripts/python.exe -B -` with an inline database-free Python probe of the real positive native API test body and linked/catalog finalizers. Assertions confirmed F-05's uncaptured committed snapshot and safe refusal, and F-07's adoption/mock deletion of an unknown exact-pair replacement. psycopg.connect was explicitly forbidden; no PostgreSQL connection occurred.
- This reviewer ran `node --input-type=module` with an inline probe using frontend/tests/servicePartFixtures.js under installed Node 22.23.4. Four snapshot-404 reload combinations reconfirmed F-06 closed; a confirmed Add/failed-refresh/reload-cancel case reconfirmed F-08 with no cancellation request or duplicate write.
- This reviewer ran `backend/.venv/Scripts/python.exe -B -` with inline ElementTree/JSON artifact inspection: original JUnit has 537 cases, repair JUnit has 12, both have zero failures/errors/skips; repair JSON has 12 exact cleanup receipts and the documented ID totals. This parsed existing artifacts and did not execute those tests.
- This reviewer used local Get-Content/rg/git diff reads to inspect the complete delta and affected contracts. The corrected rg search found no skip/xfail/only/todo declarations in the new suites. An initial Windows glob-style rg invocation failed; it was replaced with rg -g filters. The activity helper initially could not find node; it succeeded after setting the supplied fnm PATH. No installation occurred.
- Reused, not executed by this reviewer: preceding fresh Astra review's `backend/.venv/Scripts/python.exe -B -m pytest -q -c backend/pyproject.toml backend/tests/test_service_part_fixture_safety.py backend/tests/test_service_link_fixture_safety.py backend/tests/test_manual_service_parts.py backend/tests/test_manual_registration_server.py backend/tests/test_service_part_queries.py backend/tests/test_service_part_api.py -m "not integration" -p no:cacheprovider --tb=short`: 393 passed in 14.02 seconds, one existing deprecation warning.
- Reused, not executed by this reviewer: preceding fresh Astra review's `node --test --test-reporter=spec frontend/tests/servicePartApi.test.js frontend/tests/servicePartState.test.js`: 210 passed in 0.62 seconds, none failed/skipped/canceled. Its receipt is preserved in blueprint/.state/staging/feature-6-f05-f06-repair/astra-repair-review.md.
- Reused recorded `npm --prefix frontend run lint` and `npm --prefix frontend run build` repair passes. Unchanged full suites and native/browser runs were not repeated, consistent with the user's proportional verification policy.

## Evidence

- Fresh isolated Codex child with no builder transcript, explicitly selected gpt-6.1-sol/high reasoning. All 31 committed paths in a55857122368529eba9481ff4613abdc94285716..8eb3b63cad61649ea702f0f98d9c3cba65ef66d4 were reviewed across all four lenses, including the complete spec, schemas, queries, API, fixture/server changes, all new tests, React components, request/state/validation logic, CSS and both verification documents. Nearby service-removal locks, authentication/CSRF/session deadlines, session state, physical connection guard and authoritative SQL constraints/indexes were inspected. Audit records, dependency trees, generated/build artifacts and unrelated source were excluded from application scope.
- Strict models reject coerced IDs/quantity/confirmation, forbidden ownership fields and unsafe Unicode. Public models preserve valid historical text. SQL binds trusted owner, vehicle, service and child IDs; authorizes the parent before catalog classification; locks the service before attachment/removal and the catalog row before comparison/copy; compares all reviewed identity fields and copies server values. Preparation/serialization occurs within the transaction, success returns after commit/closure, and uncertain writes are not retried. Existing FK behavior preserves snapshot text after catalog changes/deletion. Native race tests synchronize both parent-removal orderings with actual PostgreSQL blockers.
- Routes reuse authentication and pre-body mutation policy, sanitize field/path/union/preview errors, omit private exception data, apply no-store and attach committed deadlines only to success. The client validates IDs/shapes, separates drafts and saved values, invalidates stale previews, requires deliberate reload/inspection/acknowledgment for uncertain creation and fresh confirmation for removal, and gates duplicate/overlapping service/part actions. Session/resource generations and local expiry clear private state and discard late replies. UI labels, associations, escaped text, focus/cancel handling and wrapping styles were inspected; runtime UI evidence is user-attributed.
- No additional quality, security, performance or tests findings were confirmed. List work uses owner/service indexes, a single ordered child query and linear parsing/rendering; no N+1 or polling was introduced. No dependency/schema/configuration change or new runner was introduced. Missing pagination/profiling is not treated as a defect without established scale.
- Reused original 537 native passes with 535 cleanup receipts and two read-only health cases, and the focused repair's 12 native passes in 51.31 seconds with 12 exact cleanup receipts. The latter verified absence of 24 users, 24 sessions, 12 vehicles, 12 services, 14 snapshots and 3 catalog IDs through separate guarded connections. These are tracked identities verified absent, including rolled-back/previously removed IDs, not broad deletion counts. Existing success evidence does not cover F-05's unexercised post-commit assertion failure or F-07's deliberate untracked replacement.
- Reused the user's November 20, 2026 Chrome 157.0.8103.79 focused repair observations in BOTH Vite development and production preview: ordinary/404 reloads, confirmed Add/Remove with failed refresh, uncertain Add/Remove, write count stayed 1 and exact catalog-inclusive cleanup. Real guarded writes/reloads remain separate from simulated 404/503/lost acknowledgments. No reviewer browser execution is claimed. Original full-checklist/full-idle evidence predates the focused repair; full idle was not repeated.
- Applied AGENTS.md, project overview, coding standards, active spec, configuration and installed Audit/independent-review contract. Preserved historical/astra records unchanged and F-04 verbatim.

## Findings

- **F-05 [P1] open, reconfirmed.** The positive native API test at backend/tests/test_service_part_api_integration.py:55 and :65 captures IDs only after post-commit assertions. A failing response/assertion can strand fixture-owned data because unknown IDs correctly stop finalization. Capture both IDs in the existing query preparation callback before commit, then retain exact-ID refusal. This explicit recovery contract gap blocks the receipt.
- **F-07 [P1] open, reconfirmed.** backend/tests/database_support.py:478 adopts an unknown ID found at the reserved catalog pair and :491 can delete it. Requires deliberate reuse of the exposed exact UUID pair after the fixture row disappears/moves; no accidental collision or actual deletion is claimed. The explicit no-unrelated-deletion boundary makes this blocking. Capture fixture catalog IDs before commit and stop on unknown replacements.
- **F-08 [P2] open, reconfirmed.** frontend/src/servicePartState.js:205 closes the reload panel but leaves its question in the live status, displacing failed-refresh feedback. Write gating and request counts remain correct; nonblocking.
- **F-06 [P1] closed, independently reconfirmed.** Current-generation snapshot 404 reloads use neutral feedback and do not replay prior success. Resolution now records this reviewer's focused evidence.
- **F-04 [P2] open, carried forward verbatim and nonblocking.** No repair or acceptance. No new finding IDs added.
- Repair F-05/F-07 first; F-08 is the small feedback follow-up. No finding was accepted on the user's behalf.

## Remaining risk

- F-05 and F-07 prevent a passing receipt at this checkpoint. Probes used mocks only: no real stranded fixture or unintended deletion occurred in this review. F-07's narrow second-writer exact-pair precondition is part of the finding, not a probability claim.
- Live PostgreSQL/native integration commands, manual guarded backend/dev/preview servers and direct browser checks were unavailable under this review's explicit read-only/no-database/no-server scope. Existing evidence above was reused. No configured Browser tests command exists; UI accessibility/layout were source-reviewed and supported by user observations, not independently exercised.
- No typecheck or combined Verify command is configured. No network-backed `npm --prefix frontend audit`, dependency installation, performance benchmark, full backend/frontend suite rerun or repeated full idle check was performed. Dependencies did not change; the focused prior checks and native/browser evidence remain separately attributed.

## Findings from the first gpt-6.1-sol repair review (historical)

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

### F-05 [P1] open - Fixture cleanup can adopt a second snapshot with the same name

**File:** backend/tests/database_support.py:411
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** Browser fixtures reserve a user-entered snapshot name under a synthetic service. Once that tuple is reserved, any additional row with the same parent and name passes the guard, even after the original write succeeded and its sole returned ID was tracked. Teardown independently recovers every matching row at line 532 and targets each ID for deletion at line 575. In a database-free check using the existing mocked connections, one write registered ID 22. A subsequent read also returned ID 23 from a separate writer under the same parent/name. The guard added 23 to the tracked set, and the mock cleanup issued DELETE for both IDs. The guard therefore permits deleting another writer's row in the guarded test database. No actual database deletion was performed or observed.
**Suggested fix:** For caller-named snapshot fixtures, record the ID from the insert result during response preparation, before commit, with its exact parent/owner. Use that identity for lookup and recovery even if the acknowledgment is lost. Make the guard and teardown stop on an unexpected same-name ID. Keep support for two genuinely fixture-created identical snapshots by tracking each returned ID. Add a database-free regression covering an unrelated same-name row, acknowledged duplicates, and uncertain commit recovery.
**Resolution:** The November 20 repair stops both browser inspection and teardown from adopting unknown same-name IDs. Browser inserts, the native query helper and direct linked-fixture SQL capture returned IDs before commit. Distinct acknowledged duplicates, rollback and lost acknowledgment are covered by focused tests and the 12-case native evidence. One writer still needs the repair. In backend/tests/test_service_part_api_integration.py:55 and :65, the positive API test checks headers (including a separate database read) before its first capture of either returned ID. A reviewer-run database-free invocation of that test body simulated a committed response and a failed header assertion. The reservation existed, the ID map was empty and the guarded finalizer stopped without issuing any DELETE. The previous name-based recovery masked this gap. Exact cleanup of the test-owned snapshot and parents is now unavailable when the response or intervening assertion fails. Keep this finding open for that recovery regression. Capture the ID in the endpoint query preparation callback for both positive API writes, as the failure-injection API cases already do, and cover a post-commit assertion/response failure. Keep the unknown-ID refusal in place.

Fresh gpt-6.1-sol review on November 20 independently retains P1/open at checkpoint 8eb3b63cad61649ea702f0f98d9c3cba65ef66d4. The reviewer invoked the real positive native API test body with mocked responses and database access forbidden. Its initial list passed, the simulated committed POST returned, and the next header assertion failed before track_part_snapshot ran. One reservation remained with an empty ID map. Calling the real linked finalizer with that committed ID raised Unexpected snapshot ID with zero mock DELETEs. The repaired unknown-ID refusal is correct and was not bypassed, but assertion/response failure can still strand the test's own data and prevent the required exact cleanup. This is an explicit failure-recovery contract gap, not a production persistence bug. The separate failure-injection API cases already capture the ID before commit; the ordinary positive test must do the same for both inserts.


### F-06 [P1] closed - Reload feedback can claim a mutation committed after a removal returned 404

**File:** frontend/src/servicePartState.js:145
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** If a snapshot disappears after the list is displayed, DELETE returns the fixed snapshot 404. The store sets the same refresh flag used after confirmed writes. When the user reloads and the list request fails, the live status says "The change committed". A reviewer-run Node fixture observed exactly one DELETE, a snapshot-missing result and an unavailable list result followed by this claim. In a second check, a successful earlier addition followed by a snapshot 404 and successful manual reload reported "Part snapshot added" again. The current removal received no success acknowledgment. Both paths misattribute an outcome while the user is inspecting history.
**Suggested fix:** Use neutral reload feedback when the snapshot was already absent. Associate commit feedback with the specific confirmed mutation and consume it on its own refresh. Cover both failed and successful reloads following a snapshot 404, including after an earlier successful mutation.
**Resolution:** Independently verified on November 20 at 8eb3b63cad61649ea702f0f98d9c3cba65ef66d4. A confirmed mutation sets the feedback marker, its first successful refresh consumes it, and a snapshot 404 clears it. Reviewer-run Node cases covered 404 followed by successful and failed reads, with and without a prior Add, confirmed writes with failed refresh, uncertain writes and single-dispatch guards. User-reported focused checks in development and production preview observed one write per scenario and no replay on ordinary reload. F-08 describes separate prompt cancellation behavior that existed before this repair.

Fresh gpt-6.1-sol review independently reconfirmed closed on November 20 at the same checkpoint. A reviewer-run inline Node probe exercised all four combinations of prior Add present/absent and post-404 reload success/failure using the existing store fixture. Each result used neutral list feedback, retained refreshRequired only for a failed reload, dispatched exactly one DELETE and no replay, and dispatched an Add only when deliberately requested. Full state/API inspection confirms the refresh marker is set by acknowledged writes, consumed by successful refresh and cleared by snapshot 404. Existing confirmed/uncertain regression results are reused separately from this probe.


### F-07 [P1] open - Catalog teardown can delete an unrelated replacement at a reserved pair

**File:** backend/tests/database_support.py:478
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** The fixture creates a UUID-tagged manufacturer/part-number pair and exposes it during the browser workflow. Once its row is deleted or its pair edited, another writer can reuse that known pair. Uniqueness applies only to rows that currently exist. Teardown adds every ID found at the pair to its owned set, then deletes an unreferenced row by ID. In a database-free finalizer probe, fixture ID 22 was absent and the same pair returned replacement ID 23. Cleanup added 23 to the tracked IDs and issued a mock DELETE for 23. This requires reuse of the exact known pair in the guarded test database. No real row was touched.
**Suggested fix:** Capture catalog INSERT RETURNING IDs before commit at fixture create/replace call sites. Keep those IDs through acknowledgment loss and catalog edits. Treat an unknown ID found at a reserved pair as grounds to stop cleanup, preserving the foreign row. Cover the replacement and genuine fixture-created replacements with database-free tests.
**Resolution:**

Fresh gpt-6.1-sol review independently retains P1/open on November 20 at checkpoint 8eb3b63cad61649ea702f0f98d9c3cba65ef66d4. A reviewer-run database-free probe invoked _delete_catalog_fixtures with tracked ID 22 absent and another writer's ID 23 at the exact reserved pair. The real finalizer added 23 and issued the mock DELETE for 23 after finding no references. P1 is based on the explicit rule to delete only test-created immutable identities, not a claimed random UUID collision, production threat model or observed real deletion. This requires deliberate reuse of the exposed exact pair after the fixture row moves/disappears. The reservation can detect an unexpected row but cannot establish its ownership. Pre-commit capture plus refusal of unknown IDs is the bounded repair and preserves genuine fixture replacements and acknowledgment-loss recovery.


### F-08 [P2] open - Canceling a parts reload leaves its question in the live status

**File:** frontend/src/servicePartState.js:205
**Found:** 2026-11-20 by /audit independent current (quality, tests)
**Why it matters:** Opening the reload confirmation overwrites the current status. Choosing Keep current view closes the panel but leaves its question in the live status. A reviewer-run Node check started with a confirmed Add whose automatic refresh failed. After opening and canceling reload, refresh was still required but the committed-write explanation had been replaced by the question about discarding the preview. One Add and two list calls occurred, including the initial list and failed refresh. Cancel sent no request.
**Suggested fix:** Keep the prompt copy in the confirmation panel and preserve the prior result when the user cancels. Test cancellation after a confirmed write with a failed refresh.
**Resolution:**

Fresh gpt-6.1-sol review independently retains P2/open on November 20. A reviewer-run inline Node probe acknowledged one Add, failed its immediate list refresh, opened and canceled reload, then verified reloadPrompt false while message still equaled the reload question rather than the prior committed-write/failed-refresh feedback. refreshRequired remained true; request counts stayed one Add and two lists (initial plus failed refresh). No request occurred on cancel and write gating remained intact, so this is a nonblocking feedback-restoration issue rather than another uncertain-write or data-integrity failure.

## Verification and completion evidence

All runtime results below were previously recorded. The initial full suites reported
2,660 database-free backend passes and 978 frontend passes across 13 files, with
pip check, lint and build passing. The first repair recorded 110 focused backend
and 210 focused frontend passes, plus lint and build. The final fixture-only
repair recorded 110 focused database-free passes. The final independent reviewer
ran 12 focused database-free regressions and reused unchanged evidence.

The original guarded native run recorded 537 passes, 535 cleanup receipts and
two read-only cases. The F-05/F-06 repair recorded 12 passes and 12 exact cleanup
receipts. The F-05/F-07 repair recorded seven passes in 17.69 seconds with seven
exact receipts. Separate guarded connections confirmed absence of 14 user IDs,
14 session IDs, seven vehicle and seven service IDs, six snapshot IDs, and ten
catalog IDs for that last run. Counts refer to tracked fixture identities.

The original user-performed development and production preview checklist included
a full visible idle observation. On November 20, 2026, the user reported the
focused F-05/F-06 repair checks in both modes using Chrome 157.0.8103.79, with
no replay and exact cleanup. The focused recheck did not repeat the full idle
observation. Simulated responses and acknowledgment loss are separately recorded.

Completion checked the receipt and spec identity, the exact repair patches, the
saved test reports, plan fingerprint, archive contents and recovery trees.
Runtime suites, database checks and browser checks were reused by instruction.
The final fixture repair left application behavior unchanged. F-04 and F-08
remain open and nonblocking. Existing warnings and limitations are preserved in
the records below. The following source documents retain their original wording
and timestamps, including historical status and prospective step instructions.

## Preserved Feature 6 verification record

# Parts used verification

Feature 6: Record parts used during a service.

## Current status

**Blocking fixture repairs F-05/F-07, November 20, 2026:** The two native API
writes now register exact snapshot IDs immediately on receiving their responses,
before header assertions. Catalog teardown never adopts IDs discovered at a
reserved pair; trusted catalog writers capture exact IDs before commit.
Focused database-free checks pass. The seven separately approved guarded native
cases passed with exact cleanup as recorded below. Application, HTTP contracts
and frontend behavior are unchanged, so no new browser check was run or proposed.
F-05/F-07 remain open pending independent review;
F-06 remains closed, and F-04/F-08 stay open and unchanged. The active audit
receipt is preserved as historical/stale evidence for the changed code.

### Earlier checkpoint and F-05/F-06 repair status (historical)

**F-05/F-06 repair, November 20, 2026:** Targeted code and database-free
regressions are implemented; both P1 findings remain OPEN pending independent
verification. F-04 remains unchanged, open P2/nonblocking. The checkpoint and
original changes-requested audit receipt are preserved. That receipt is
historical and stale for the changed code; no fresh passing review is claimed.
The separately approved 12-case native repair set passed with exact cleanup;
the user confirmed all focused browser checks in development and preview on
November 20, 2026, using Chrome 157.0.8103.79, with exact cleanup. The repair is
ready for checkpoint review; F-05/F-06 remain open for independent verification.
The original implementation/browser results below describe the pre-repair
checkpoint, not proof of the changed cleanup or feedback behavior.

Step 3 was approved. Step 4's Parts used interface and guarded manual setup are
implemented. Automated and native final verification passed as recorded below.
The user confirmed the complete browser checklist passed in development and
production preview on November 20, 2026, including the full visible idle check
and exact cleanup. Step 4 is complete and awaiting final review/checkpoint
approval. No staging, commit, audit or feature completion is authorized by this
record. F-04 remains open and nonblocking, unchanged.

Branch: `feature/record-parts-used-during-a-service`.
Parent HEAD: `a55857122368529eba9481ff4613abdc94285716`.
Verification date: November 19, 2026. No agent-controlled browser run occurred.
User-browser evidence recorded: November 20, 2026. Application/test hashes match
the passing November 19 candidate; automated/native checks were not rerun for
this documentation update.

## Contract and implementation review

- The active specification and API both use POST
  `/api/vehicles/{vehicle_id}/services/{service_id}/parts/lookup`.
  The specification does not say `/catalog-match`; no route discrepancy or
  contract edit was needed before wiring the section.
- The existing protected service-detail page renders the new section after its
  service request completes. It uses the Step 3 request/state helpers without
  adding a page, route, catalog browser, dependency or compatibility claim.
- Saved snapshots, manual draft, exact pair and reviewed preview are separate.
  Manual entry works independently of the catalog. Lookup spelling/case is
  preserved. Saving rechecks all preview identity fields and copies only the
  locked catalog row. A stale preview inserts nothing and needs deliberate
  lookup or explicit manual entry. Catalog change/deletion preserves copied
  historical text; a null reference is not labeled as proof of manual origin.
- Removal requires explicit confirmation and affects only the chosen snapshot.
  The service and catalog entry remain. Parent service locks serialize attachment
  with service removal. No vehicle/service readings, cost or maintenance links
  are updated by snapshot operations. Values are bound SQL parameters.
- Public JSON is prepared inside the business transaction. Success leaves the
  connection context only after commit/closure. Known failures roll back and
  close before safe translation; uncertain acknowledgments cannot promise
  rollback. The frontend never automatically retries a write, requires reload
  and inspection, and warns that a missing entry does not prove an Add failed.
- Service edits/removal and parts requests disable each other's active controls
  with synchronous state checks. This avoids overlapping the existing session
  store's single private-request slot. Canceling service/part confirmation sends
  no mutation. Reload warnings explain draft/preview effects.
- Existing authenticated actor, CSRF/Origin/JSON rules, safe errors, no-store
  and committed deadline helper are reused. Only successful current-generation
  results can advance the deadline. No polling or expiry-triggered request is
  added. Old service request helpers/F-04 are not repaired incidentally.
- Inputs have labels, hints/error associations, first-error/preview focus,
  inline removal/reload panels, cancel focus restoration, status announcements,
  disabled pending controls and wrapping CSS. Accessibility/responsive evidence
  comes from the user's checklist below; source/build alone is not proof.

## Automated checks run in Step 4

Commands run from the repository root using the existing Python virtual
environment and fnm Node 22.23.4. No installation or unrelated upgrade occurred.

| Check | Actual result |
| --- | --- |
| Focused manual-server and fixture safety checks | 77 passed; Starlette/AnyIO deprecation warning |
| Complete database-free backend suite | 2660 passed, 537 integration tests deselected; 1 deprecation warning; 33.23 s |
| Complete Node command, all 13 test files | 978 passed, 0 failed/cancelled/skipped; 1.07 s; existing experimental MockTimers warnings |
| Backend pip check | No broken requirements found |
| Frontend lint | Passed |
| Frontend production build | Passed on final UI; Vite 6.4.5, 68 modules; 1.38 s |
| Tracked and untracked whitespace checks | Passed; candidate diff/manifest include all 28 feature files |

Focused command:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_manual_service_parts.py backend/tests/test_manual_registration_server.py backend/tests/test_service_part_fixture_safety.py -p no:cacheprovider --tb=short
```

An initial focused run had 76 passes/1 failure because a Mock constructor's
`name` argument names the mock rather than creating a string `.name` attribute.
The fixture-result stub now uses SimpleNamespace. The rerun passed all 77;
this was a test-double correction, not a product or guard-policy change.

Complete commands:

```powershell
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m "not integration" -p no:cacheprovider
backend/.venv/Scripts/python.exe -m pip check
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js frontend/tests/servicePartApi.test.js frontend/tests/servicePartState.test.js
npm --prefix frontend run lint
npm --prefix frontend run build
git diff --check
```

The Node suites cover request shapes, ID validation, preview invalidation,
uncertainty, required refresh, duplicate guards, stale responses, authentication
generations and deadlines, including the existing F-01/F-02/F-03 regressions.
There is no installed DOM/browser runner; these are logic tests, not UI evidence.

## Native PostgreSQL verification (separate from browser)

The final complete run PASSED: **537 passed, 2660 deselected, 0 failures or
skips**, 821.69 seconds. One existing Starlette/AnyIO deprecation warning.
This November 19 Step 4 run is distinct from the earlier Step 2/3 runs; it is
reused unchanged for the November 20 documentation/evidence refresh.

```powershell
$env:RUN_DB_TESTS = '1'
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m integration -x -p no:cacheprovider -o junit_logging=all --junitxml=blueprint/.state/staging/feature-6-step-4/native.xml
```

Only `backend/.env.test` is loaded. Settings must name `garageguide_app_test`;
every physical test connection checks `SELECT current_database()` as its first
statement before exposure. No connection is redirected to the application
database, no schema is initialized/changed, and cleanup is registered before
writes. Exact snapshot/linked children are cleaned before services, vehicles
and users; exact synthetic catalog IDs are cleaned after their references.
Separate guarded connections verify absence. No truncation, prefix deletion,
sequence reset or adoption of ordinary data is permitted.

The captured JUnit report contains 535 exact synthetic cleanup receipts. The
remaining two tests (`test_real_database_health` and
`test_health_transaction_is_read_only_on_native_database`) are read-only health
checks without synthetic fixtures. Across the 535 receipts, these tracked
synthetic IDs were verified absent through separate guarded connections:

| Record type | Tracked IDs verified absent |
| --- | ---: |
| Users | 978 |
| Sessions | 944 |
| Vehicles | 460 |
| Services | 288 |
| Part snapshots | 50 |
| Maintenance completions | 19 |
| Schedules | 20 |
| Catalog entries | 30 |

These are verified fixture ID counts, including IDs already removed by a test,
not a claim of deleting that many rows during cleanup or clearing ordinary data.
All 537 cases passed and no cleanup failed. Raw results and the receipt summary
are in ignored `blueprint/.state/staging/feature-6-step-4/native.xml`,
`native.log`, and `cleanup.json`. Summarizing those recorded receipts opened no
additional database connection and did not rerun the suite.

Two new native tests exercise the test-terminal catalog controller directly:
create/change/replace/delete preserve snapshot text and parents, reject stale
previews, and refuse untracked linked rows. They do not start a browser/server
and must not be described as browser evidence. Existing native tests also prove
attachment/removal lock order in both directions using database blocking
evidence, ownership, transactions, safe API responses and Features 1-5 regressions.

## Prior-step results (historical, not new Step 4 runs)

- Step 1: 264 focused database-free schema passes.
- Step 2: 592 focused database-free passes; 95 native query/regression passes.
  All 95 per-test cleanup receipts confirmed absence of 190 users, 190 sessions,
  114 vehicles, 108 services, 31 snapshots, 12 completions, 13 schedules and
  20 catalog IDs. These are tracked synthetic ID counts, not ordinary deletions.
- Step 3: 184 focused API passes; 201 focused Node passes; complete gates then
  had 2638 backend/978 Node passes. Final native API run: 65 passed. All 65
  cleanup receipts confirmed 130 users, 130 sessions, 73 vehicles, 73 services,
  8 snapshots and 7 catalog IDs absent. An earlier 25-pass/1-failure API run
  exposed a test helper adding Content-Type to an intended missing-header case;
  raw JSON fixed that test setup. Three-case recheck and final 65 passed; all
  94 cleanup receipts across initial/recheck/final runs were verified. No
  application-policy relaxation was made.
- Earlier command/results/cleanup artifacts remain in ignored
  `blueprint/.state/staging/feature-6-step-2/` and `feature-6-step-3/`.
  They are distinct from final Step 4 results and are not checkpoint files.

## User-performed browser verification: complete

The user reported all performed Feature 6 checks passed, then explicitly
confirmed the entire checklist in BOTH Vite development and production preview,
including the full visible idle-deadline check. Test date: November 20, 2026.
Browser version: 157.0.8103.79. Browser product name was not separately supplied;
no name is inferred from an older feature's report. No checks were reported
skipped after the whole-checklist confirmation.

Real browser/backend coverage reported through that checklist: manual entry
with an empty catalog, exact catalog selection/miss, reviewed preview and stale
preview recovery, explicit manual switch, snapshot survival after catalog changes
or deletion, quantity and optional values, list/confirmed removal/cancel/re-add,
service deletion blocking, account isolation, protected navigation, headers and
deadline synchronization without extra authentication requests, local expiry
without polling/renewal, keyboard/focus/announcements and responsive widths/zoom.
These are the user's checklist observations, not agent-controlled browser runs
or newly inferred detailed traces. No numeric idle duration or unreported
assistive-technology testing is claimed.

### Simulated failures (separate from real behavior)

The checklist's simulated network/timeout, rejected/forbidden/unavailable,
malformed/unexpected response, required-refresh failure, stale work and lost
write-acknowledgment checks are covered by the user's complete pass report.
They remain browser simulations, not proof of real PostgreSQL outages, server
revocation or a genuinely lost commit acknowledgment. Recorded native tests
remain a separate category; no native suite or browser session was rerun by the
agent to enter this report.

### User-reported guarded cleanup

The user supplied this exact final backend message:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, schedules, and catalog entries are absent.
```

This confirms the reported guarded browser fixture cleanup, separately from the
535 automated native cleanup receipts above. Step 4 is complete and awaiting
final review. The repeatable procedure is retained in BROWSER_CHECKS.md.

## Limitations and review handoff

- Browser evidence is user-performed and covers the confirmed checklist; no agent
  browser run or earlier-feature browser evidence is substituted. No additional
  browser traces, product name, numeric idle duration or assistive-technology
  coverage is inferred. No independent audit has run for Feature 6.
- POST/DELETE uncertainty is preserved; list absence is not proof of failure.
  Identical attachments are allowed, with no automatic retry/idempotency layer.
- No real catalog seed, browsing, saved parts, fitment assertion, cost calculation,
  schema migration, ORM, dependency, session-algorithm change or F-04 repair.
- Existing Starlette/AnyIO and Node MockTimers warnings remain. Git's LF/CRLF
  conversion notices describe working-copy policy, not whitespace-test failure.
- Passing focused/full runtime evidence is reused while applicable code and
  environment are unchanged. Final documentation, hashes and checkpoint
  preparation cause file/whitespace checks, not repeated runtime suites.
- The final review packet/manifest freezes current code, specification progress
  and user-attributed evidence after browser confirmation. All 28 paths and raw
  hashes were refreshed; only three verification/progress documents changed
  since the passing candidate. It is a proposal for review, not staging, commit,
  independent-audit or feature-completion authorization.

## F-05/F-06 targeted repair evidence

The approved checkpoint remains `f84e348cd8c88b181b69da0bfb7148cabb51a665`.
The original audit receipt/findings are unchanged in the live records and copied
byte-for-byte to ignored `blueprint/.state/staging/feature-6-f05-f06-repair/` as
`historical-review.md` and `historical-findings.md`. No finding is marked fixed,
closed or accepted by this repair record. The active specification is unchanged.

### F-05: exact snapshot identity

Previously, a parent/name reservation allowed another matching ID to be adopted
by both the browser guard and cleanup scan. Now discovery scans never add IDs.
They reject any unexpected same-name ID before deletion. Fixture writers capture
their own INSERT RETURNING ID before commit/response preparation can fail.
Browser wrappers and existing direct linked-fixture writers use that capture;
post-commit tracking still verifies the exact ID/parent/owner. Two acknowledged
identical inserts have two separately recorded IDs. An absent captured ID after
rollback is harmless; an ambiguous or uncaptured match stops cleanup rather than
guessing ownership. The database-name/first-statement guards remain unchanged.

Database-free tests prove refusal without DELETE or adoption, rollback of the
cleanup context, retained recovery metadata, exact-ID lost-ack recovery, harmless
absent IDs, acknowledged duplicates, invalid IDs and callback ordering before
response preparation/commit. The initial repair pass made no database connection.
The subsequently approved native helper/refusal cases ran only against guarded
garageguide_app_test, with results recorded below.

### F-06: mutation-specific refresh feedback

A separate refresh-mutation marker is set only by a validated successful write
response and consumed by its successful list refresh. Ordinary reloads do not
replay historical Add/Remove messages. Snapshot 404 resets that marker and uses
neutral failed/successful reload feedback. A confirmed write whose refresh fails
still honestly says the change committed. An uncertain write remains uncertain
through failed inspection; no retry is sent. Initial list loading retains the
existing empty feedback so it does not steal focus with a reload announcement.

### Executed repair checks

```powershell
backend/.venv/Scripts/python.exe -m pytest -q -c backend/pyproject.toml backend/tests/test_service_part_fixture_safety.py backend/tests/test_service_link_fixture_safety.py backend/tests/test_manual_service_parts.py backend/tests/test_manual_registration_server.py -m "not integration" -p no:cacheprovider --tb=short
node --test frontend/tests/servicePartApi.test.js frontend/tests/servicePartState.test.js
npm --prefix frontend run lint
npm --prefix frontend run build
git diff --check
```

- Focused affected backend checks: **110 passed**, 2.64 seconds, one existing
  Starlette/AnyIO deprecation warning. Real database access is forbidden by the
  test fixtures.
- Focused frontend API/state checks: **210 passed**, 0 failed/skipped/cancelled,
  0.48 seconds. Existing Node MockTimers experimental warning.
- Frontend lint: passed. Production build: passed, Vite 6.4.5, 68 modules,
  2.16 seconds. Tracked/repair-file whitespace checks passed. No dependency,
  schema, lockfile or configuration change was made. An earlier build displayed
  an npm major-version update notice; no upgrade was performed.
- No full suite or pip check was rerun for these narrow repairs. Unaffected
  evidence stays historical. The 537 earlier native passes do not verify the
  changed cleanup; the separately approved 12 cases below provide fresh targeted
  cleanup evidence without rerunning the full native suite.

### Approved 12-case native verification: passed

The user approved exactly 12 cases covering untracked same-name
refusal without deletion, two acknowledged identical snapshots, manual
prepare/rollback/lost-ack and catalog lost-ack, API Add prepare/rollback/lost-ack,
both old linked-fixture removal/insert orderings, and synthetic catalog lifecycle.
That exact set ran: **12 passed, 0 failures, 0 skips, 51.31 seconds**, one existing
Starlette/AnyIO deprecation warning. No case or full suite was added. RUN_DB_TESTS=1
was required; only .env.test settings were loaded, effective and connected
databases were garageguide_app_test, and every new physical connection performed
its first-statement current_database() guard. Schema was not initialized/changed.

All 12 cases have captured exact cleanup receipts. Separate guarded connections
verified absence of **24 users, 24 sessions, 12 vehicles, 12 services, 14 snapshot
IDs and 3 catalog IDs**; no completion or schedule fixture was created. These
are tracked IDs verified absent, including rows already removed/rolled back by
a case, not global deletion counts. The unknown-row case restored only its own
hidden fixture ID in finally so final teardown remained exact. No guard or
cleanup failure occurred. Expected guard rejection inside that test is a passing
refusal assertion, not a real cleanup incident requiring broader recovery.

The exact executed command (the approved 12 node IDs plus JUnit capture options),
native.log, native.xml and native-cleanup.json are preserved under ignored
blueprint/.state/staging/feature-6-f05-f06-repair/. The count and every node ID
were checked against the approved proposal. Summarizing the receipts opened no
additional database connection and did not rerun tests.

### Focused user-browser verification: complete

The user reported completing all focused F-05/F-06 browser checks in BOTH Vite
development and production preview on November 20, 2026, in Chrome 157.0.8103.79.
Ordinary reload and removal 404 recovery, confirmed Add/Remove with failed
refresh, and uncertain Add/Remove behaved as expected. The user explicitly
reported that reloads did not replay old success messages or send another
mutation, and the write count stayed 1 in each scenario. These observations
apply to the focused repair, separately from the original full checklist.

Real guarded writes/reloads and simulated 404/503/lost-acknowledgment behavior
remain distinct categories. The simulations are not proof of a real PostgreSQL
outage or genuinely lost commit. No agent/reviewer browser run, additional
per-case network trace, repeated full checklist or repeated full idle test is
claimed. The 12 native results above are preserved and were not rerun to enter
these observations; neither were the passing focused database-free, Node,
lint or build checks because their code remains unchanged.

The user supplied this exact final guarded cleanup message:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, schedules, and catalog entries are absent.
```

This user-reported browser cleanup is separate from the 12 automated native
cleanup receipts. The repeatable focused guide remains in BROWSER_CHECKS.md.
The final repair checkpoint proposal includes only the 14 repair/evidence files;
the unchanged historical audit receipt and findings records are excluded.
F-05/F-06 stay OPEN pending independent review and F-04 remains unchanged.
No staging, commit, audit, completion, merge or push has occurred during this
repair. Only documentation/hash/whitespace work was needed for this update.

## Targeted F-05/F-07 fixture repair

Parent checkpoint remains `8eb3b63cad61649ea702f0f98d9c3cba65ef66d4` on
`feature/record-parts-used-during-a-service`. The current Sol receipt and complete
findings ledger are byte-identical to their copies at ignored
`blueprint/.state/staging/feature-6-f05-f07-repair/historical-review.md` and
`historical-findings.md`. No finding was closed, accepted, reclassified or edited
by this repair. The active specification and application code are unchanged.

F-05: both the manual and catalog positive API writes register their response's
exact snapshot ID before header checks or other test assertions. The later
database verification remains. A database-free regression invokes the real
native test body for each write, injects a later header assertion failure, and
uses the real linked-fixture finalizer with mock SQL to prove only the already
registered IDs are deleted. A response without a usable ID cannot establish
ownership; cleanup must continue to fail safely instead of guessing.

F-07: catalog IDs are captured from the fixture's own INSERT RETURNING before
commit, including create/replace terminal controls and both native replacement
helpers. The discovery scan checks for unknown IDs and raises a safety error
without adopting/deleting them. Known IDs survive edits and lost acknowledgments.
Tests cover unknown replacements with/without a tracked original, no deletion
or registry adoption on failure, exact known replacements, invalid IDs and
pre-commit capture before a lost-acknowledgment exception. Separate guarded
verification and the existing physical database guards remain unchanged.

Focused command:

```powershell
backend/.venv/Scripts/python.exe -m pytest -q -c backend/pyproject.toml backend/tests/test_service_part_api_fixture_safety.py backend/tests/test_service_part_fixture_safety.py backend/tests/test_manual_service_parts.py backend/tests/test_manual_registration_server.py -m "not integration" -p no:cacheprovider --tb=short
```

Result: **110 passed**, no failures, one existing Starlette/AnyIO deprecation
warning. Tracked and untracked repair-file whitespace checks passed. No unchanged
full suite, frontend suite, lint/build or pip check was rerun for fixture-only
changes. Earlier native passes remain historical, separate from the fresh
seven-case result below. No new browser-execution claim is made.

The user approved exactly seven native cases: both positive API
later-assertion/cleanup paths, unknown catalog replacement refusal, guarded
catalog controller lifecycle, native API and query replacements, and known-ID
cleanup after catalog identity edits. That exact set ran: **7 passed, 0 failures,
0 skips, 17.69 seconds**, with one existing Starlette/AnyIO deprecation warning.
No case was added, and no full suite or browser check ran.

RUN_DB_TESTS=1 and .env.test settings were used. The effective database was
garageguide_app_test; every new physical connection performed its first-statement
current_database() guard. Cleanup used exact fixture IDs and separate guarded
absence verification. All seven cleanup receipts verified **14 users, 14 sessions,
7 vehicles, 7 services, 6 snapshot IDs and 10 catalog IDs absent**. No completion
or schedule fixture was created. These are tracked IDs verified absent, including
already removed/rolled-back identities, not global deletion totals. No real guard
or teardown failure occurred; the unknown-row case's expected rejection was
caught and its own hidden ID restored in finally for exact final cleanup.

The approved node list, exact executed command and raw native.log/native.xml
are retained in ignored blueprint/.state/staging/feature-6-f05-f07-repair/.
native-cleanup.json records each receipt and aggregate counts; every executed
node/count was matched to the approved proposal. There were no schema changes,
broad deletions or sequence resets. Receipt parsing and this documentation
update did not open additional database connections or rerun runtime checks.

The final nine-file repair checkpoint proposal freezes the current exact paths,
raw hashes, diff, reused 110 focused passes and fresh seven-case native evidence.
It excludes the historical audit records and active specification. F-05/F-07
stay open for independent verification; F-06 stays closed and nonblocking
F-04/F-08 remain open, unchanged. No further repair scope was introduced.

No staging, commit, audit, completion, merge or push occurred during this repair.

## Preserved Feature 6 browser evidence and guide

# Manual browser verification

## Feature 6 Step 4: user-performed browser verification complete

### F-05/F-06 focused repair recheck: user-performed checks complete

The user confirmed completing ALL focused repair checks in BOTH Vite development
and production preview on November 20, 2026, using Chrome 157.0.8103.79.
Removal 404, confirmed Add/Remove with failed refresh, and uncertain Add/Remove
behaved as expected. Reloads did not replay old success messages or send another
mutation; the user reported the write count stayed 1 in each scenario.

These are user-performed observations, not agent/reviewer browser execution.
Real guarded Add/Remove and normal reload behavior remain separate from the
shim's simulated 404/503 and lost-acknowledgment cases. Simulations do not prove
a real database outage or lost commit. The separately recorded 12 native passes
and cleanup receipts are preserved; no runtime suite was rerun for this record.
No full Feature 6 checklist or idle-deadline check is claimed to have been
repeated during this focused repair verification.

The user supplied this exact guarded cleanup confirmation:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, schedules, and catalog entries are absent.
```

Focused browser acceptance is recorded. F-05/F-06 remain OPEN pending fresh
independent review; F-04 is unchanged. The steps below are retained as a
repeatable procedure, not additional execution evidence. The original full
Feature 6 browser report follows in its own historical section.

#### Guarded setup for the focused recheck

Stop any other backend on port 8000. From the repository root, in terminal 1:

```powershell
$env:RUN_DB_TESTS = '1'
backend/.venv/Scripts/python.exe backend/tests/manual_registration_server.py --service-parts
```

Use only the printed reserved synthetic emails. Register one with a password
you choose privately, then sign in. Never paste the password, cookies or tokens
into a report or screenshot. The launcher loads .env.test and checks the test
database and existing schema; it must refuse an unsafe database or nonempty
test catalog. If it refuses, stop rather than deleting ordinary data. No catalog
entry or terminal catalog command is needed for these manual-part checks.

In terminal 2, run development:

```powershell
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173`, create one synthetic vehicle and dated service,
and open that service's Parts used section. Perform all four flows below.
Then run production preview in another terminal, using the existing passing
production build (no rebuild needed for documentation changes):

```powershell
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
npm --prefix frontend run preview
```

Open `http://127.0.0.1:4173`, sign in with the reserved account if needed, and
repeat the four flows on an owned service. Cookies share the loopback hostname
across ports. Keep the guarded backend running through both modes. Start each
mode with a normal page load and previous fetch overrides removed.

#### Install the temporary, parts-only simulation control

After Parts used has loaded, paste this once into DevTools Console in that
mode. It stores no authentication data and prints no request bodies/values.
It does not touch authentication or catalog lookup requests. `writes` counts
attempted Add/Remove requests for repeat-submission checks, not database rows.

```javascript
(() => {
  const realFetch = window.fetch.bind(window)
  const h = {
    mode: 'normal', failLists: false, writes: 0,
    restore() { window.fetch = realFetch; delete window.ggRepair },
  }
  window.ggRepair = h
  const fixed = (status, detail) => new Response(JSON.stringify({ detail }), {
    status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  })
  window.fetch = async (input, init) => {
    const url = new URL(input instanceof Request ? input.url : String(input), location.origin)
    const method = (init?.method ?? (input instanceof Request ? input.method : 'GET')).toUpperCase()
    const part = url.origin === location.origin && /^\/api\/vehicles\/[1-9][0-9]*\/services\/[1-9][0-9]*\/parts(?:\/[1-9][0-9]*)?$/.test(url.pathname)
    if (!part) return realFetch(input, init)
    if (method === 'GET' && h.failLists) return fixed(503, 'Service parts unavailable. Please try again.')
    if (!['POST', 'DELETE'].includes(method)) return realFetch(input, init)
    h.writes += 1
    if (method === 'DELETE' && h.mode === 'missing') {
      h.failLists = true
      return fixed(404, 'Part snapshot not found.')
    }
    const response = await realFetch(input, init)
    if (response.ok && ['confirmed', 'uncertain'].includes(h.mode)) {
      h.failLists = true
      if (h.mode === 'uncertain') throw new TypeError('Synthetic lost acknowledgment')
    }
    return response
  }
})()
```

#### Four flows, repeated in development and preview

1. **Ordinary reload:** leave `ggRepair.mode = 'normal'` and
   `ggRepair.failLists = false`. Add two manual snapshots with identical name
   and values; both remain separate. After each Add 201 its immediate list
   refresh may announce that Add once. Click **Reload and inspect parts**, then
   **Reload saved parts**. Expect only "Saved parts reloaded."; no earlier
   Add/Remove success should repeat. Remove one with explicit confirmation;
   the other remains. Repeat the deliberate reload and check neutral feedback.
2. **Removal 404:** ensure a displayed snapshot remains. In Console set
   `ggRepair.mode = 'missing'; ggRepair.failLists = false; ggRepair.writes = 0`.
   Click its **Remove snapshot**, then **Permanently remove snapshot**. The shim
   returns 404 without sending DELETE to the backend. Click the two reload
   controls above; the simulated GET now returns 503. Expect "Saved parts could
   not be reloaded...", never "The change committed", "Part snapshot added"
   or "Part snapshot removed". Another write stays blocked. Set
   `ggRepair.mode = 'normal'; ggRepair.failLists = false`, then deliberately
   reload again. The row is still present; expect only "Saved parts reloaded."
   `ggRepair.writes` must remain 1; recovery sends no mutation.
3. **Confirmed write / failed refresh:** set
   `ggRepair.mode = 'confirmed'; ggRepair.failLists = false; ggRepair.writes = 0`.
   Add a uniquely named manual part. The real POST returns 201; its immediate
   GET is simulated 503. Expect "The change committed, but saved parts could
   not be reloaded..." and blocked further writes. Set
   `ggRepair.mode = 'normal'; ggRepair.failLists = false` and deliberately reload.
   This current Add success may appear once. Reload once more: neutral list
   feedback only. `ggRepair.writes` stays 1. Repeat this flow with confirmed
   removal of a displayed snapshot: real DELETE 200, failed GET, honest commit
   warning, one removal-success refresh, then a neutral reload.
4. **Uncertain write:** set
   `ggRepair.mode = 'uncertain'; ggRepair.failLists = false; ggRepair.writes = 0`.
   Add a uniquely named manual part. The shim forwards the real write but loses
   its acknowledgment; the UI must say it may have been added, not that it
   committed. The UI must not retry or auto-refresh. Deliberately reload: the
   simulated GET fails, so feedback must remain uncertain and explain that
   inspection failed. Set `ggRepair.mode = 'normal'; ggRepair.failLists = false`
   and reload again. Inspect name/quantity/notes. The duplicate warning remains;
   an absent entry would not prove failure. The explicit risk acknowledgment
   only unlocks the form and sends nothing: `ggRepair.writes` stays 1. Do not
   add again when the row already exists. Repeat with removal of a displayed
   snapshot: after failed then successful inspection, feedback describes current
   absence/presence only. It must not claim which request removed it; any retry
   while present requires a new explicit confirmation. No automatic mutation,
   polling or deadline-only authentication request should appear.

#### Restore and report

After each mode, run `ggRepair.restore()` (or reload the page) to remove the shim.
The 404/503/lost-ack cases are simulations, distinct from real successful writes
and reads; they do not prove a real outage or lost commit. Do not manually inject
an untracked row to test cleanup; the approved native set covers that refusal.

After both modes, close frontend test pages/servers and type `quit` in the
guarded backend terminal. Wait for this exact line:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, schedules, and catalog entries are absent.
```

For future reruns, if any guard or cleanup fails, stop and report it without
broad deletion or reset. Report browser/version, test date, both modes, the four
outcomes, separate simulation observations and the exact cleanup line. The
current focused user-observation record and cleanup are documented above;
this retained procedure does not imply another browser run.

### Original checkpoint browser observations (historical)

The user reported that all performed Feature 6 manual checks passed and then
explicitly confirmed completing the entire checklist in BOTH Vite development
and production preview, including the full visible idle-deadline check.
Test date: November 20, 2026. Browser version: 157.0.8103.79; the browser product
name was not separately supplied. No agent or independent-reviewer browser run
is claimed.

The reported checklist covers empty-catalog manual entry, exact lookup/miss,
preview review/save/invalidation, stale changed/replaced/deleted previews,
explicit manual fallback, preserved historical snapshot details, quantities,
confirmed individual removal/cancellation/correction, service removal blocking,
two-account isolation, protected navigation, session deadlines, local expiry,
keyboard/focus/announcements, responsive widths and zoom. This is the user's
whole-checklist pass report, not additional per-case observations inferred by
the agent. No unreported numeric idle duration or assistive-technology run is
claimed.

Real browser/backend checks and the guide's simulated network, timeout, error,
stale-response and lost-acknowledgment cases remain separate. Passing simulations
does not prove a real PostgreSQL outage, server revocation or lost commit.
Automated/native results are recorded separately in SERVICE_PARTS_STATUS.md
and are reused unchanged; none were rerun to record these observations.

The user supplied the exact guarded backend cleanup message:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, schedules, and catalog entries are absent.
```

Both required modes, full visible idle check and cleanup are confirmed. Step 4
is complete and awaiting final review/checkpoint approval. The procedure below
is retained for repeatability and is not another execution record. Prior
Feature 1-5 observations remain unchanged.

### Guarded setup and two modes

Use only the prepared `garageguide_app_test` database and the existing
`backend/.env.test`. Stop other backends on port 8000. From the repository root:

```powershell
$env:RUN_DB_TESTS = '1'
backend/.venv/Scripts/python.exe backend/tests/manual_registration_server.py --service-parts
```

This test-only launcher checks settings and the physical database before any
business SQL, verifies the existing schema without changing it, reserves three
unique synthetic account emails, and guards parents/catalog/snapshot writes.
It requires the test catalog to be empty initially. If it refuses a nonempty
catalog or another guard fails, STOP; do not clear rows or change databases.
There is no product catalog-management endpoint. Terminal catalog commands below
can change only their own reserved synthetic rows and check linked references.

Register only the printed reserved emails. Choose your own matching 15-128
character passwords; no password is printed or supplied by this launcher.
Do not paste passwords, cookie values, tokens, request bodies, or sensitive
screenshots into verification reports. Use two independent Chrome profiles
(or normal and Incognito) for accounts A and B. Dev/preview share the cookie
host, so ports alone do not isolate accounts. Create a vehicle and dated service
for each through the UI. Record the synthetic vehicle/service IDs for navigation.

In a second terminal, set the existing Node path and start development:

```powershell
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173`. For preview, build then run:

```powershell
$env:PATH = "$env:APPDATA\fnm\node-versions\v22.23.4\installation;$env:PATH"
npm --prefix frontend run build
npm --prefix frontend run preview
```

Open `http://127.0.0.1:4173`. Keep the guarded backend running for both modes.
Complete the empty-catalog checks in BOTH modes BEFORE `catalog create`.
Then complete all remaining applicable checks in both modes. These are manual
launch commands; the agent has not started servers or executed browser checks.

### Real browser and backend checks

1. Open the existing protected service detail page
   `/vehicles/VEHICLE_ID/services/SERVICE_ID`. The saved service loads before
   Parts used. An owned empty service shows an empty parts list and manual entry
   works even though the catalog is empty. Check direct load, refresh, Back and
   Forward, case/encoded/trailing-slash route variants and invalid/unrelated
   paths. Private parts, drafts and previews must remain hidden while session
   validation is unresolved and after logout, rejection or account changes.
2. **Before creating any catalog row**, add a manual snapshot in each mode:
   name required; manufacturer, part number and notes optional; quantity begins
   at 1. Blank optional values show Not recorded; literal `0` remains a recorded
   string. Test blank name, zero/fraction/overflow quantity, valid quantity 1
   and 2147483647, Unicode/U+FEFF and interior whitespace. Correct errors and
   submit. Expect one POST 201 then one list GET; saved values match. Rapid
   repeat submission must not create duplicate POSTs. A subsequent invalid draft
   must submit once corrected after the required list refresh has succeeded.
3. Choose Exact catalog lookup and enter an invented unmatched pair. Expect the
   fixed catalog 404 and an explicit Switch to manual entry option. Do not
   silently create a manual snapshot. After choosing manual, adding still works.
4. At the backend `fixture>` prompt, type `catalog create`. It prints only a
   synthetic reviewed preview. Copy its exact manufacturer and part number into
   the browser lookup fields. Test a changed-case pair does not match; then use
   the exact pair. Expect POST `.../parts/lookup` 200 and a visible preview with
   name, manufacturer, part number and category. No `/catalog-match` is used.
   Lookup is not a vehicle-compatibility claim. Changing either lookup field
   must invalidate the preview and disable Add until a new lookup succeeds.
5. Review and add the catalog-backed snapshot. Expect one POST 201 plus GET.
   Quantity and notes are user input; identity comes from the server's catalog
   row. Category is review-only and is not stored in the snapshot. Finish/cancel
   a service edit before parts actions, and finish parts actions before service
   mutations. Ensure both sets of controls explain these temporary exclusions.
6. Look up again but do not add. Type `catalog change` at the fixture prompt,
   then Add using the old preview. Expect the fixed stale-preview 409, no new
   snapshot, preview invalidation, and deliberate fresh lookup or manual switch.
   There must be no automatic re-lookup/save. Reload saved parts and confirm the
   earlier saved snapshot still has its original copied name and other text.
7. Obtain a fresh preview. Type `catalog replace` before Add. The same pair now
   has a new catalog ID. Old-preview Add must conflict without writing. Look up
   again, review the new preview and add successfully. Type `catalog delete`,
   then reload parts: both saved copies retain their text/quantity/notes and
   lose only the catalog reference. The UI must not claim they were originally
   manual. A lookup miss again offers an explicit manual switch. Use
   `catalog create` to prepare another synthetic example if needed for preview.
8. Request removal of one snapshot. The inline panel names it and explains
   removal affects only that snapshot. Cancel sends no DELETE, returns focus
   and leaves it saved. Confirm sends exactly one DELETE with literal
   `confirm_removal: true`, then GET. Other snapshots and the service remain.
   If a catalog entry still exists, looking it up still succeeds. Correct a
   snapshot by deliberately removing and re-adding it; no edit endpoint exists.
9. Try removing the service while parts remain: the existing Feature 5 linked
   record conflict leaves service and parts intact. After removing all parts,
   normal service removal is possible unless another existing link blocks it.
   Do not add maintenance/parts-catalog product pages or modify ordinary data.
10. With account B, navigate to A's exact synthetic vehicle/service URLs and
    attempt the nested part list, lookup, add and removal using the UI/fetch
    policy below. Missing and foreign parents have the same safe fixed 404;
    no catalog preview or A's snapshot values are disclosed. B's owned service
    still works. A still sees its own saved data. Use only fixture-owned IDs.
11. Check Network: no-store on successes and errors; the committed
    X-GarageGuide-Session-Expires-At header only on successful 200/201 responses.
    A valid newer response updates the visible local deadline with no extra
    `/api/auth/session` call solely for synchronization. Failed responses do not
    extend it. No periodic polling or automatic mutation retry occurs.
12. Wait until the visible local deadline with the page visible and no deliberate
    activity. Private identity, snapshots, drafts and previews clear at equality
    without an expiry-triggered request. Later deliberate navigation/visibility
    return/retry may validate again. Record whether this full real observation
    was performed; do not replace it with a simulated error or fake clock claim.
13. Use only the keyboard: labeled inputs, first-error focus, associated errors,
    preview focus, confirmation/cancel focus, reload warning, status messages
    and repeat-submission prevention. Check narrow layouts at 375/768/1440 px
    and 200% zoom with long part names/notes and no horizontal overflow.

For a real ownership probe in DevTools, replace only the fixture-owned IDs and
select the method/body deliberately. Do not log the result values or tokens:

```javascript
const partsPath = '/api/vehicles/VEHICLE_ID/services/SERVICE_ID/parts'
await fetch(partsPath, { credentials: 'same-origin' })
// A deliberate manual add probe; do not repeat it automatically:
await fetch(partsPath, {
  method: 'POST', credentials: 'same-origin',
  headers: { 'Content-Type': 'application/json', 'X-GarageGuide-CSRF': '1' },
  body: JSON.stringify({ source: 'manual', name: 'Synthetic isolation probe' }),
})
// For lookup use partsPath + '/lookup', the same headers, and the exact pair.
// For DELETE use partsPath + '/SNAPSHOT_ID' and { confirm_removal: true }.
```

The browser supplies Origin; do not attempt to spoof it. All probes must stay
within the guarded setup. Browser records should report status/behavior only.

### Simulated failures and stale work (separate evidence)

In each mode, use this temporary fetch wrapper for **parts paths only**. It
never prints bodies, passwords, cookies or tokens. Set one fault, operate the
UI, then restore real fetch before the next case. Do not modify API/session
implementation files or persist this shim. Rejecting promises and fake bodies
are simulations; they do not prove an actual PostgreSQL outage or revocation.

```javascript
window.ggPartsFetch = window.fetch
window.ggPartsFault = null
window.fetch = async function (input, init) {
  const url = new URL(typeof input === 'string' ? input : input.url, location.origin)
  if (!/^\/api\/vehicles\/[1-9][0-9]*\/services\/[1-9][0-9]*\/parts(?:\/|$)/.test(url.pathname)) {
    return window.ggPartsFetch.call(this, input, init)
  }
  const fault = window.ggPartsFault
  if (fault === 'network') throw new TypeError('Synthetic connection failure')
  if (fault === 'timeout') return new Promise((resolve, reject) => {
    init.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
  })
  if (fault === 'late') {
    const response = await window.ggPartsFetch.call(this, input, init)
    await new Promise(resolve => setTimeout(resolve, 4000))
    return response
  }
  if (fault === 'lost-write' && ['POST', 'DELETE'].includes(init?.method) && !url.pathname.endsWith('/lookup')) {
    await window.ggPartsFetch.call(this, input, init)
    throw new TypeError('Synthetic lost acknowledgment')
  }
  const cases = {
    rejected: [401, { detail: 'Not authenticated.' }],
    forbidden: [403, { detail: 'Request not allowed.' }],
    unavailable: [503, { detail: 'Service parts unavailable. Please try again.' }],
    'auth-unavailable': [503, { detail: 'Authentication unavailable. Please try again.' }],
    unexpected: [500, { detail: 'Internal server error' }],
    malformed: [200, { parts: 'invalid' }],
  }
  if (cases[fault]) {
    const [status, body] = cases[fault]
    return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } })
  }
  return window.ggPartsFetch.call(this, input, init)
}
// Set one case, perform an action, then restore:
// window.ggPartsFault = 'unavailable'
// window.fetch = window.ggPartsFetch; delete window.ggPartsFetch; delete window.ggPartsFault
```

- On list/lookup network/timeout/503/malformed/500, show safe feedback, retain
  correctable values while the session is valid, and require deliberate retry.
  A 401 or authentication 503 gates private content according to session policy.
  Restore real fetch before retrying or signing in again.
- To test failed required refresh, temporarily return the unavailable response
  only when `init?.method === 'GET'` while letting an Add succeed. Another Add
  remains blocked until a deliberate real list reload succeeds. After that,
  make a new draft invalid, correct it, and verify submission works.
- With `lost-write`, allow one Add/Remove then restore fetch. The UI must not
  retry. Reload and inspect identity, quantity and notes. An uncertain Add
  requires explicit acknowledgment of duplicate risk before unlocking, and
  acknowledgment itself sends nothing. Absence after reload does not prove
  failure. An uncertain Remove's later absence proves only current absence;
  if still present, another DELETE requires a new explicit confirmation.
- With `late`, navigate to another service/vehicle, leave/return via history,
  hide the page, or sign out/sign in (including same account). Late list,
  lookup, Add/Remove results must not restore private state, preview or an old
  deadline. Restore fetch and deliberately reload to inspect possible writes.

### Cleanup and reporting

Restore fetch shims. Stop frontend terminals. In the guarded backend terminal,
type `quit` so it stops accepting requests before exact cleanup. Wait for:

```text
Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, schedules, and catalog entries are absent.
```

This includes only reserved/tracked synthetic IDs and their guarded recovery
reservations; it is not a global catalog/database reset. If cleanup fails, stop
and report the failure; do not approve browser acceptance or delete broad data.
Report exact browser/version, date, both modes, observed real cases, separately
simulated cases, full-idle observation if performed, and the exact cleanup line.


## Recorded evidence from feature-6-step-2/commands-and-results.json

```json
{
  "databaseFree": "backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_part_schemas.py backend/tests/test_service_part_queries.py backend/tests/test_service_part_fixture_safety.py backend/tests/test_service_fixture_safety.py backend/tests/test_service_link_fixture_safety.py backend/tests/test_session_fixture_safety.py backend/tests/test_service_queries.py backend/tests/test_service_record_queries.py backend/tests/test_manual_registration_server.py -m \"not integration\" -p no:cacheprovider",
  "native": "backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_part_queries_integration.py backend/tests/test_service_queries_integration.py backend/tests/test_service_record_queries_integration.py -m integration -x -p no:cacheprovider -o junit_logging=all --junitxml=blueprint/.state/staging/feature-6-step-2/native.xml",
  "nativeEnvironment": "RUN_DB_TESTS=1; load_settings(testing=True); effective and physical database exactly garageguide_app_test; backend/.env.test only; no schema changes",
  "results": {
    "databaseFreePassed": 592,
    "databaseFreeSeconds": 2.1,
    "nativePassed": 95,
    "nativeSeconds": 202.55,
    "warnings": "One existing Starlette/AnyIO BlockingPortal deprecation per pytest run"
  },
  "cleanup": "95 successful receipts; exact totals and cases in cleanup.json; separate guarded absence verification; no broad deletes or schema writes",
  "boundaries": "Step 2 only; no API, frontend, dependency, F-04 changes, staging or commits"
}
```

## Recorded evidence from feature-6-step-3/results.json

```json
{
  "branch": "feature/record-parts-used-during-a-service",
  "head": "a55857122368529eba9481ff4613abdc94285716",
  "focusedBackend": {
    "passed": 184,
    "seconds": 4.52
  },
  "focusedFrontend": {
    "passed": 201
  },
  "backend": {
    "passed": 2638,
    "integrationDeselected": 535,
    "seconds": 31.0
  },
  "frontend": {
    "passed": 978,
    "files": 13,
    "failed": 0,
    "skipped": 0
  },
  "pip": "No broken requirements found.",
  "lint": "passed",
  "build": {
    "passed": true,
    "modules": 66,
    "seconds": 1.42,
    "scopedElevation": true
  },
  "native": {
    "artifact": "native.xml",
    "passed": 65,
    "failed": 0,
    "cleanupVerified": true,
    "cleanupReceipts": 65,
    "verifiedAbsenceTotals": {
      "users": 130,
      "sessions": 130,
      "vehicles": 73,
      "services": 73,
      "part_snapshots": 8,
      "maintenance_completions": 0,
      "schedules": 0,
      "catalog_parts": 7
    },
    "testsByFile": {
      "tests.test_service_part_api_integration": 64,
      "tests.test_service_record_api_integration": 1
    }
  },
  "initialNative": "25 passed, 1 helper failure; json= restored deliberately missing Content-Type. Raw-content helper corrected; 3-case recheck then full 65-case pass. All 94 receipts across runs verified cleanup.",
  "commands": {
    "focusedBackend": "backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_part_api.py -p no:cacheprovider",
    "backend": "backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -m \"not integration\" -p no:cacheprovider",
    "focusedFrontend": "node --test frontend/tests/servicePartApi.test.js frontend/tests/servicePartState.test.js",
    "frontend": "node --test frontend/tests/api.test.js frontend/tests/sessionState.test.js frontend/tests/credentialValidation.test.js frontend/tests/vehicleApi.test.js frontend/tests/vehicleState.test.js frontend/tests/vehicleSession.test.js frontend/tests/vehicleDetailApi.test.js frontend/tests/vehicleDetailState.test.js frontend/tests/serviceApi.test.js frontend/tests/serviceState.test.js frontend/tests/serviceSession.test.js frontend/tests/servicePartApi.test.js frontend/tests/servicePartState.test.js",
    "pip": "backend/.venv/Scripts/python.exe -m pip check",
    "lint": "npm --prefix frontend run lint",
    "build": "npm --prefix frontend run build",
    "native": "RUN_DB_TESTS=1; backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_part_api_integration.py backend/tests/test_service_record_api_integration.py::test_native_get_patch_confirmed_delete_and_repeated_delete_contracts -m integration -x -p no:cacheprovider -o junit_logging=all --junitxml=blueprint/.state/staging/feature-6-step-3/native.xml",
    "recheck": "RUN_DB_TESTS=1; backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests/test_service_part_api_integration.py -m integration -k missing-content-type -x -p no:cacheprovider -o junit_logging=all --junitxml=blueprint/.state/staging/feature-6-step-3/native-recheck.xml"
  },
  "files": [
    {
      "path": "backend/app/main.py",
      "purpose": "Register only the approved nested parts router.",
      "rawSha256": "f68d251a14644a56e0f9c776e6712e3ff51af7569c6b4d445492ade9a4edc035"
    },
    {
      "path": "backend/app/routes/service_parts.py",
      "purpose": "Authenticated routes, fixed sanitized errors, pre-body mutation policy, prepared responses and headers.",
      "rawSha256": "73a877f527bde5e829b9acf0740136cd2a9f84b55b0a8ae620fe791a1fe3de03"
    },
    {
      "path": "backend/tests/test_service_part_api.py",
      "purpose": "184 database-free API boundary tests.",
      "rawSha256": "a31ff77ef483bce7edb7c009b49544e365e406687c003e14fb5b927b89ea8347"
    },
    {
      "path": "backend/tests/test_service_part_api_integration.py",
      "purpose": "64 guarded native API cases; raw-content policy helper preserves missing headers.",
      "rawSha256": "ff2e225657e9b554860985b9d713437158d164b9e13906480180c3fb8757fb61"
    },
    {
      "path": "frontend/src/api.js",
      "purpose": "Separate snapshot list/lookup/add/remove helpers with strict IDs/shapes, timeout/cancellation and uncertainty classification; old service helper block unchanged.",
      "rawSha256": "221bab80493219c77a83e8657a5c9684c5beb737373f6bb135a3b1f318f61d6a"
    },
    {
      "path": "frontend/src/serviceValidation.js",
      "purpose": "Export the unchanged linear Python-compatible trim for reuse.",
      "rawSha256": "2a8f46c8f4e50402bc2398cde57996f57c5230880ad665e72691e88d16e35ba6"
    },
    {
      "path": "frontend/src/servicePartValidation.js",
      "purpose": "Strict snapshot/preview/body/error validation and exact/manual text rules.",
      "rawSha256": "4cf53639badbf215a6b33e8ba15f41749cf88c44c73d8e73dce5f8466d154192"
    },
    {
      "path": "frontend/src/servicePartState.js",
      "purpose": "Private resource lifecycle, preview invalidation, confirmation, required refresh, uncertain-write inspection and generation/deadline guards.",
      "rawSha256": "875b9f56dd3215ad04136d024e07cc1ef43b4da0518cf20977f5edc072518883"
    },
    {
      "path": "frontend/tests/servicePartFixtures.js",
      "purpose": "Synthetic Node transport/session/store fixtures.",
      "rawSha256": "4d49dc36adf8f0df2739f203f5a8b2ccaa06acdc6ed7252babb454997386c959"
    },
    {
      "path": "frontend/tests/servicePartApi.test.js",
      "purpose": "Request, parsing, strict IDs/quantity, safe errors, timeout/cancellation and no-retry regressions.",
      "rawSha256": "d86b93b40eb83b1e6a5e7dbd7ba68e6bbb7b10195c5cb7488046fec27afcbbab"
    },
    {
      "path": "frontend/tests/servicePartState.test.js",
      "purpose": "Draft, preview, confirmation, refresh, uncertainty, stale-response and local expiration regressions.",
      "rawSha256": "3d2bb8f635818454fd71b6fe27eabef860d27b776ba468db12065df4fc013add"
    },
    {
      "path": "blueprint/context/current-feature.md",
      "purpose": "Mark Step 3 checked, record actual commands/results/cleanup/limitations; leave Step 4 unstarted.",
      "rawSha256": "0fa96f95837e231306b6a34195fd7c716c12cb9eb4a5b7fccf314b993f46eb15"
    }
  ],
  "limitations": [
    "No visible Parts used section, new React route, or browser run. Step 4 requires approval.",
    "Native test transport helper initially synthesized a deliberately missing Content-Type; corrected and rerun. No policy relaxation.",
    "Fault injection and Node mocks/fake clocks are simulations, not real outages or browser evidence.",
    "Existing Starlette/AnyIO, Node MockTimers and Git LF/CRLF notices; no dependency changes.",
    "F-04 code/status unchanged; no staging, commits, audit, schema changes, or native writes outside guarded test database."
  ]
}
```

## Recorded evidence from feature-6-step-4/verified-results.json

```json
{
  "backend": {
    "passed": 2660,
    "integrationDeselected": 537,
    "seconds": 33.23
  },
  "focusedFixtureSafety": {
    "passed": 77
  },
  "frontend": {
    "passed": 978,
    "files": 13,
    "failed": 0,
    "skipped": 0
  },
  "native": {
    "tests": 537,
    "passed": 537,
    "failed": 0,
    "cleanup_receipts": 535,
    "read_only_tests_without_synthetic_fixtures": [
      {
        "classname": "tests.test_health",
        "name": "test_real_database_health",
        "time": "0.176"
      },
      {
        "classname": "tests.test_user_queries_integration",
        "name": "test_health_transaction_is_read_only_on_native_database",
        "time": "0.101"
      }
    ],
    "tracked_ids_verified_absent": {
      "users": 978,
      "sessions": 944,
      "vehicles": 460,
      "services": 288,
      "snapshots": 50,
      "completions": 19,
      "schedules": 20,
      "catalog": 30
    },
    "receipt_counts": {
      "users_sessions_vehicles": 535,
      "services": 257,
      "links": 55,
      "catalog": 27
    },
    "database": "garageguide_app_test",
    "duration_seconds": 821.685
  },
  "pipCheck": "passed",
  "lint": "passed",
  "build": {
    "status": "passed",
    "modules": 68,
    "seconds": 1.38
  },
  "whitespace": "git diff --check and all 28 modified/untracked UTF-8 file checks passed after documentation update",
  "browser": {
    "performer": "user",
    "testDate": "2026-11-20",
    "version": "157.0.8103.79",
    "productName": "not separately supplied",
    "development": "complete checklist passed",
    "productionPreview": "complete checklist passed",
    "fullVisibleIdleDeadline": "confirmed completed",
    "cleanupMessage": "Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, schedules, and catalog entries are absent.",
    "agentBrowserExecution": false,
    "independentReviewerBrowserExecution": false,
    "evidenceBasis": "User whole-checklist pass report and explicit follow-up confirmation; no additional per-case traces inferred.",
    "simulations": "Checklist simulated network/timeout/error/stale/lost-acknowledgment cases remain separate from real backend behavior; not proof of a real outage/revocation/lost commit."
  },
  "warnings": [
    "Existing Starlette/AnyIO deprecation",
    "Existing Node MockTimers experimental warnings",
    "Git LF/CRLF conversion notices"
  ],
  "initialFocusedFailure": "76 passed/1 failed due to Mock(name=...) stub; corrected to SimpleNamespace; final focused 77 passed",
  "evidencePolicy": "Reuse passing runtime results while code/environment unchanged; documentation-only updates receive file/whitespace checks.",
  "runtimeEvidenceReused": {
    "originalDate": "2026-11-19",
    "documentationRefreshDate": "2026-11-20",
    "allApplicationAndTestHashesUnchanged": true,
    "runtimeTestsRerun": false,
    "databaseConnectionsOpenedForRefresh": false
  }
}
```

## Recorded evidence from feature-6-step-4/cleanup.json

```json
{
  "tests": 537,
  "passed": 537,
  "failed": 0,
  "cleanup_receipts": 535,
  "read_only_tests_without_synthetic_fixtures": [
    {
      "classname": "tests.test_health",
      "name": "test_real_database_health",
      "time": "0.176"
    },
    {
      "classname": "tests.test_user_queries_integration",
      "name": "test_health_transaction_is_read_only_on_native_database",
      "time": "0.101"
    }
  ],
  "tracked_ids_verified_absent": {
    "users": 978,
    "sessions": 944,
    "vehicles": 460,
    "services": 288,
    "snapshots": 50,
    "completions": 19,
    "schedules": 20,
    "catalog": 30
  },
  "receipt_counts": {
    "users_sessions_vehicles": 535,
    "services": 257,
    "links": 55,
    "catalog": 27
  },
  "database": "garageguide_app_test",
  "duration_seconds": 821.685
}
```

## Recorded evidence from feature-6-f05-f06-repair/final-repair-results.json

```json
{
  "focusedBackend": {
    "passed": 110,
    "seconds": 2.64
  },
  "focusedFrontend": {
    "passed": 210,
    "failed": 0,
    "skipped": 0,
    "cancelled": 0
  },
  "lint": "passed",
  "productionBuild": {
    "status": "passed",
    "modules": 68,
    "seconds": 2.16
  },
  "whitespace": "passed",
  "native": {
    "status": "passed",
    "tests": 12,
    "failures": 0,
    "skipped": 0,
    "seconds": 51.31,
    "database": "garageguide_app_test",
    "cleanupReceiptCount": 12,
    "trackedIdsVerifiedAbsent": {
      "users": 24,
      "sessions": 24,
      "vehicles": 12,
      "services": 12,
      "snapshots": 14,
      "completions": 0,
      "schedules": 0,
      "catalog": 3
    },
    "receipts": [
      {
        "class": "tests.test_manual_service_parts_integration",
        "test": "test_untracked_same_name_snapshot_blocks_guard_and_cleanup_without_deletion",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          2,
          0,
          0,
          0
        ]
      },
      {
        "class": "tests.test_service_part_queries_integration",
        "test": "test_manual_snapshot_exact_values_and_order_without_catalog_dependency[None-None]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          2,
          0,
          0,
          0
        ]
      },
      {
        "class": "tests.test_service_part_queries_integration",
        "test": "test_native_rollback_closure_and_uncertain_commit_recovery[prepare-manual]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          1,
          0,
          0,
          0
        ]
      },
      {
        "class": "tests.test_service_part_queries_integration",
        "test": "test_native_rollback_closure_and_uncertain_commit_recovery[pre-commit-manual]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          1,
          0,
          0,
          0
        ]
      },
      {
        "class": "tests.test_service_part_queries_integration",
        "test": "test_native_rollback_closure_and_uncertain_commit_recovery[lost-ack-manual]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          1,
          0,
          0,
          0
        ]
      },
      {
        "class": "tests.test_service_part_queries_integration",
        "test": "test_native_rollback_closure_and_uncertain_commit_recovery[lost-ack-catalog]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          1,
          0,
          0,
          1
        ]
      },
      {
        "class": "tests.test_service_part_api_integration",
        "test": "test_native_failure_boundary_rolls_back_or_preserves_uncertain_commit_without_retry[prepare-add]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          1,
          0,
          0,
          0
        ]
      },
      {
        "class": "tests.test_service_part_api_integration",
        "test": "test_native_failure_boundary_rolls_back_or_preserves_uncertain_commit_without_retry[pre-commit-add]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          1,
          0,
          0,
          0
        ]
      },
      {
        "class": "tests.test_service_part_api_integration",
        "test": "test_native_failure_boundary_rolls_back_or_preserves_uncertain_commit_without_retry[lost-ack-add]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          1,
          0,
          0,
          0
        ]
      },
      {
        "class": "tests.test_service_record_queries_integration",
        "test": "test_child_insert_commits_first_and_waiting_mutation_rechecks_links[remove-part]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          1,
          0,
          0,
          0
        ]
      },
      {
        "class": "tests.test_service_record_queries_integration",
        "test": "test_removal_commits_first_and_blocked_child_insert_cannot_commit[part]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          0,
          0,
          0,
          0
        ]
      },
      {
        "class": "tests.test_manual_service_parts_integration",
        "test": "test_guarded_terminal_catalog_lifecycle_preserves_snapshots_and_stale_preview_conflicts",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          2,
          0,
          0,
          2
        ]
      }
    ],
    "note": "Exact fixture IDs verified absent through separate guarded connections, not a global reset or count of rows deleted during teardown. No browser execution."
  },
  "browser": {
    "performer": "user",
    "testDate": "2026-11-20",
    "browser": "Chrome",
    "version": "157.0.8103.79",
    "development": "all focused repair checks passed",
    "productionPreview": "all focused repair checks passed",
    "observations": [
      "Removal 404 recovery behaved as expected.",
      "Confirmed add/removal followed by failed refresh behaved as expected.",
      "Uncertain add/removal behaved as expected.",
      "Reloads did not replay old success messages or send another mutation.",
      "Reported write count stayed 1 in each scenario."
    ],
    "cleanupMessage": "Verified cleanup: all reserved synthetic accounts, sessions, vehicles, services, part snapshots, maintenance completions, schedules, and catalog entries are absent.",
    "agentBrowserExecution": false,
    "simulationBoundary": "404/503 and lost-acknowledgment simulations remain separate from real guarded writes/reloads, not proof of a real outage or lost commit.",
    "coverageBoundary": "Focused repair only; no repeated full Feature 6 checklist or full idle observation claimed."
  },
  "evidenceReuse": "All code/test hashes unchanged; no runtime suite or database connection for this documentation update.",
  "warnings": [
    "Existing Starlette/AnyIO deprecation",
    "Existing Node MockTimers experimental warning",
    "Git LF/CRLF notices",
    "Earlier npm upgrade notice; no upgrade performed"
  ],
  "findings": {
    "F-04": "open P2, unchanged, nonblocking",
    "F-05": "open P1 pending independent review",
    "F-06": "open P1 pending independent review"
  }
}
```

## Recorded evidence from feature-6-f05-f06-repair/native-executed-command.json

```json
[
  "C:\\Users\\ethan\\Desktop\\GarageGuide\\GarageGuide\\backend\\.venv\\Scripts\\python.exe",
  "-m",
  "pytest",
  "-c",
  "backend/pyproject.toml",
  "backend/tests/test_manual_service_parts_integration.py::test_untracked_same_name_snapshot_blocks_guard_and_cleanup_without_deletion",
  "backend/tests/test_service_part_queries_integration.py::test_manual_snapshot_exact_values_and_order_without_catalog_dependency[None-None]",
  "backend/tests/test_service_part_queries_integration.py::test_native_rollback_closure_and_uncertain_commit_recovery[prepare-manual]",
  "backend/tests/test_service_part_queries_integration.py::test_native_rollback_closure_and_uncertain_commit_recovery[pre-commit-manual]",
  "backend/tests/test_service_part_queries_integration.py::test_native_rollback_closure_and_uncertain_commit_recovery[lost-ack-manual]",
  "backend/tests/test_service_part_queries_integration.py::test_native_rollback_closure_and_uncertain_commit_recovery[lost-ack-catalog]",
  "backend/tests/test_service_part_api_integration.py::test_native_failure_boundary_rolls_back_or_preserves_uncertain_commit_without_retry[prepare-add]",
  "backend/tests/test_service_part_api_integration.py::test_native_failure_boundary_rolls_back_or_preserves_uncertain_commit_without_retry[pre-commit-add]",
  "backend/tests/test_service_part_api_integration.py::test_native_failure_boundary_rolls_back_or_preserves_uncertain_commit_without_retry[lost-ack-add]",
  "backend/tests/test_service_record_queries_integration.py::test_child_insert_commits_first_and_waiting_mutation_rechecks_links[remove-part]",
  "backend/tests/test_service_record_queries_integration.py::test_removal_commits_first_and_blocked_child_insert_cannot_commit[part]",
  "backend/tests/test_manual_service_parts_integration.py::test_guarded_terminal_catalog_lifecycle_preserves_snapshots_and_stale_preview_conflicts",
  "-m",
  "integration",
  "-x",
  "-p",
  "no:cacheprovider",
  "-o",
  "junit_logging=all",
  "--junitxml=blueprint\\.state\\staging\\feature-6-f05-f06-repair\\native.xml"
]
```

## Recorded evidence from feature-6-f05-f07-repair/final-repair-results.json

```json
{
  "focusedBackend": {
    "passed": 110,
    "failures": 0,
    "seconds": 2.11,
    "reusedUnchanged": true
  },
  "native": {
    "status": "passed",
    "tests": 7,
    "failures": 0,
    "skipped": 0,
    "seconds": 17.69,
    "database": "garageguide_app_test",
    "cleanupReceiptCount": 7,
    "trackedIdsVerifiedAbsent": {
      "users": 14,
      "sessions": 14,
      "vehicles": 7,
      "services": 7,
      "snapshots": 6,
      "completions": 0,
      "schedules": 0,
      "catalog": 10
    },
    "receipts": [
      {
        "class": "tests.test_service_part_api_integration",
        "test": "test_native_response_id_survives_later_assertion_and_exact_cleanup[manual]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          1,
          0,
          0,
          0
        ]
      },
      {
        "class": "tests.test_service_part_api_integration",
        "test": "test_native_response_id_survives_later_assertion_and_exact_cleanup[catalog]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          2,
          0,
          0,
          1
        ]
      },
      {
        "class": "tests.test_manual_service_parts_integration",
        "test": "test_untracked_catalog_replacement_blocks_cleanup_and_preserves_row",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          0,
          0,
          0,
          2
        ]
      },
      {
        "class": "tests.test_manual_service_parts_integration",
        "test": "test_guarded_terminal_catalog_lifecycle_preserves_snapshots_and_stale_preview_conflicts",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          2,
          0,
          0,
          2
        ]
      },
      {
        "class": "tests.test_service_part_api_integration",
        "test": "test_native_reviewed_preview_conflicts_are_fixed_and_leave_no_attachment[replace]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          0,
          0,
          0,
          2
        ]
      },
      {
        "class": "tests.test_service_part_queries_integration",
        "test": "test_changed_disappeared_or_replaced_preview_writes_nothing[replace]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          0,
          0,
          0,
          2
        ]
      },
      {
        "class": "tests.test_service_part_queries_integration",
        "test": "test_saved_snapshot_is_historical_after_catalog_edit_or_deletion[edit]",
        "trackedIdsVerifiedAbsent": [
          2,
          2,
          1,
          1,
          1,
          0,
          0,
          1
        ]
      }
    ],
    "scopeExpanded": false,
    "note": "Exact fixture IDs verified absent through separate guarded connections, including already removed/rolled-back IDs; not global deletion counts."
  },
  "whitespace": "passed",
  "applicationBehaviorChanged": false,
  "fullSuitesRerun": false,
  "browserRerun": false,
  "findings": {
    "F-05": "open pending independent review",
    "F-07": "open pending independent review",
    "F-06": "closed unchanged",
    "F-04": "open P2 unchanged",
    "F-08": "open P2 unchanged"
  },
  "warning": "Existing Starlette/AnyIO deprecation; Git LF/CRLF notices"
}
```

## Recorded evidence from feature-6-f05-f07-repair/native-executed-command.json

```json
[
  "C:\\Users\\ethan\\Desktop\\GarageGuide\\GarageGuide\\backend\\.venv\\Scripts\\python.exe",
  "-m",
  "pytest",
  "-c",
  "backend/pyproject.toml",
  "backend/tests/test_service_part_api_integration.py::test_native_response_id_survives_later_assertion_and_exact_cleanup[manual]",
  "backend/tests/test_service_part_api_integration.py::test_native_response_id_survives_later_assertion_and_exact_cleanup[catalog]",
  "backend/tests/test_manual_service_parts_integration.py::test_untracked_catalog_replacement_blocks_cleanup_and_preserves_row",
  "backend/tests/test_manual_service_parts_integration.py::test_guarded_terminal_catalog_lifecycle_preserves_snapshots_and_stale_preview_conflicts",
  "backend/tests/test_service_part_api_integration.py::test_native_reviewed_preview_conflicts_are_fixed_and_leave_no_attachment[replace]",
  "backend/tests/test_service_part_queries_integration.py::test_changed_disappeared_or_replaced_preview_writes_nothing[replace]",
  "backend/tests/test_service_part_queries_integration.py::test_saved_snapshot_is_historical_after_catalog_edit_or_deletion[edit]",
  "-m",
  "integration",
  "-x",
  "-p",
  "no:cacheprovider",
  "-o",
  "junit_logging=all",
  "--junitxml=blueprint\\.state\\staging\\feature-6-f05-f07-repair\\native.xml"
]
```

## Retained local evidence digests

```json
[
  {
    "path": "blueprint/.state/staging/feature-6-step-2/commands-and-results.json",
    "rawSha256": "8a3c60f951c9106ccd5a67a5309fe76ec0a30811a9b49f7981c79e214742227a"
  },
  {
    "path": "blueprint/.state/staging/feature-6-step-3/results.json",
    "rawSha256": "3f531e92ae6097e92e5fe7a20ead0f932f4d5240129f751edfb4eb47a32ba68c"
  },
  {
    "path": "blueprint/.state/staging/feature-6-step-4/verified-results.json",
    "rawSha256": "f4e963c4b86b34a45176ca272e5ac273450460dbd468db488b7695196418b851"
  },
  {
    "path": "blueprint/.state/staging/feature-6-step-4/cleanup.json",
    "rawSha256": "7b43c5c397fe5d7a93de301d57e5f94a35c239f8a0cadc3b9f69378eb7f9cacd"
  },
  {
    "path": "blueprint/.state/staging/feature-6-f05-f06-repair/final-repair-results.json",
    "rawSha256": "845ddcea66842b93f7fa1b2a39a080c468cde43e5ca0ad85b5d2b385073ecd32"
  },
  {
    "path": "blueprint/.state/staging/feature-6-f05-f06-repair/native-executed-command.json",
    "rawSha256": "df020164cd18bcb43bd4657361f5c8ce550d276d34374537898166945749a817"
  },
  {
    "path": "blueprint/.state/staging/feature-6-f05-f07-repair/final-repair-results.json",
    "rawSha256": "0d896581a96e15e0698c658a3b1f07e360e9c0fb943126128872e7ded4b0c160"
  },
  {
    "path": "blueprint/.state/staging/feature-6-f05-f07-repair/native-executed-command.json",
    "rawSha256": "4b36db0af8bb92347018cf200dfc6601a9bb417cbe1e31ef5ce4391fe00987e2"
  },
  {
    "path": "blueprint/.state/staging/feature-6-step-4/native.xml",
    "rawSha256": "9d89ae9cde12a493c2c4a3d413d464b5e0a9be69b9cfa0df293b0815b2f8c985"
  },
  {
    "path": "blueprint/.state/staging/feature-6-f05-f06-repair/native.xml",
    "rawSha256": "088824f4938935b6e14fa057d2e80ce18eee409f709f639fe218b78a0327de1f"
  },
  {
    "path": "blueprint/.state/staging/feature-6-f05-f07-repair/native.xml",
    "rawSha256": "fe893a1aff9b72672001acee877edaf8b5d96ab7cc083762bc9aafe4ab97f84f"
  },
  {
    "path": "blueprint/.state/staging/feature-6-f05-f06-repair/native-cleanup.json",
    "rawSha256": "4293c8b42fd4f549e3c4ff9a908ee666abd811082ab831e9d36416f5098d628c"
  },
  {
    "path": "blueprint/.state/staging/feature-6-f05-f07-repair/native-cleanup.json",
    "rawSha256": "4b4ed967e940084f448ac402699a0926715a88287b2c74b93cc4d0f9850d0170"
  },
  {
    "path": "blueprint/.state/staging/feature-6-f05-f07-repair/native-test-proposal.json",
    "rawSha256": "2908d5ccd5920670dca3db7e51afc9ddc4bac3025c89e10d1355ac74e4f2691a"
  }
]
```

## Try it now

Run or do:

With the guarded test app already running, sign in with a reserved synthetic
account and open an owned service record. In Parts used, choose **Reload and
inspect parts**, then **Reload saved parts**.

Expected:

The saved snapshot list refreshes and shows "Saved parts reloaded." An earlier
Add or Remove success does not repeat. The reload sends a list request.

This proves:

A deliberate list reload reads the current snapshots without replaying earlier
mutation feedback.
