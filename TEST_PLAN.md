# GarageGuide database test plan

These are executable database-level tests mapped to your feature IDs. They cover the storage/integrity portions of the earlier feature tests, not the complete UI/API narratives. Test IDs DB01–DB34 are distinct from your workbook's Fxx.Txx tests.

Run `03_database_tests.sql` after `01_schema.sql` and `02_views.sql` in `garageguide_test`. Each assertion raises an exception on failure. A complete run returns 34 PASS rows and rolls back fixtures. Repeated execution is supported.

| Test | Feature | Successful outcome |
|---|---|---|
| DB01 | F01, F16 | Reject duplicate email. |
| DB02 | F01 | Require normalized email. |
| DB03 | F16 | Reject ownerless vehicle. |
| DB04 | F04 | Reject negative mileage. |
| DB05 | F04 | Reject negative hours. |
| DB06 | F06 | Reject negative cost. |
| DB07 | F06 | Reject unsupported service type. |
| DB08 | F06 | Reject empty description. |
| DB09 | F08 | Require an interval. |
| DB10 | F08 | Require matching baseline. |
| DB11 | F08 | Reject zero interval. |
| DB12 | F10 | Reject duplicate completion. |
| DB13 | F10, F16 | Reject cross-vehicle completion. |
| DB14 | F12 | Reject duplicate saved catalog part. |
| DB15 | F12 | Reject manual origin with catalog ID. |
| DB16 | F11 | Reject fitment without source. |
| DB17 | F11 | Reject duplicate manufacturer/part number. |
| DB18 | F02, F03 | Require session expiration after creation. |
| DB19 | F16 | Protect parent with service history. |
| DB20 | F06 | Reject zero replacement quantity. |
| DB21 | F04, F05 | Retain separate miles and hours. |
| DB22 | F06, F13 | Keep unknown and zero distinct. |
| DB23 | F13 | Known total and unknown count. |
| DB24 | F13 | Separate vehicle totals. |
| DB25 | F13, F15 | Empty vehicle remains visible. |
| DB26 | F08 | Store date and hours schedules. |
| DB27 | F10, F13 | Multiple completion links do not multiply expenses. |
| DB28 | F11 | Exact catalog lookup returns fixture. |
| DB29 | F05 | Current reading does not rewrite history. |
| DB30 | F07, F13 | Expense view reflects edit. |
| DB31 | F07, F12 | Removing saved part preserves history. |
| DB32 | F12 | Removing catalog part preserves snapshot. |
| DB33 | F07, F10, F13 | Service deletion cleans links and updates expenses. |
| DB34 | F03 | Session revocation can be stored. |

## Application tests still required

| Features | What SQL tests do not prove |
|---|---|
| F01–F03 | Registration forms, actual password hashing, password rules, correct/incorrect login, secure cookies, session rejection after expiry/revocation, unsaved-change warnings and sign-out navigation. |
| F04–F07 | Forms, persistence through API/browser refresh, lower-reading confirmation, service editing/deletion confirmation, error/retry behavior and display ordering. |
| F08–F10 | Duplicate schedule review, actual upcoming/due/overdue status calculations, missing-reading messages, selecting latest applicable completion, baseline fallback after deletion, required completion readings, and atomic API completion saves. DB26 checks stored interval arithmetic only. |
| F11–F12 | Real source verification, part search normalization, incomplete/unsupported vehicle responses, manual duplicate review, and saved-part UI. Fixture fitment is explicitly fictional. |
| F13 | UI labels, links to contributing services and API ownership. The expense view's arithmetic is tested. |
| F14 | AI request minimization, grounded report accuracy, no invented diagnosis/fitment, timeouts, retries and continued availability of core features. |
| F15 | Dashboard presentation, partial loading, responsive widths, keyboard operation and deployed persistence. |
| F16 | Authenticated route authorization using two real accounts, credential hashing and secrets, HTTPS, logging, and external-data handling. Cross-vehicle foreign keys alone do not enforce account isolation. |

Do not mark those workbook test cases passed solely because this database suite passes. Track their results when the corresponding application features exist.

## Evidence

Capture the table list and test results on your local PostgreSQL installation. Save console output with the README command. Record database version, test date, tester name, pass/fail result and any failures fixed. The supplied automated results describe the assistant's test environment, not a test already conducted on your PC.

