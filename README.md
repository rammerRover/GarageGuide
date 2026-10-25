# GarageGuide PostgreSQL setup and learning guide

This package builds the database for GarageGuide's planned MVP. It contains ten tables, an expense-summary view, 34 executable database tests, and a rollback-only practice script. The project stack remains React, Python/FastAPI and PostgreSQL. No Docker or ORM is required to use these files.

## Files and order

| File | What to do with it |
|---|---|
| `01_schema.sql` | Run once in each fresh database to create the ten tables and indexes. |
| `02_views.sql` | Run after the schema to create the live expense-summary query. It can be rerun. |
| `03_database_tests.sql` | Run on the test database. Expect 34 PASS results. |
| `04_practice_queries.sql` | Optional guided insert/read/update exercise; changes roll back. |
| `TEST_PLAN.md` | Explains which planned features these tests cover and which need app tests later. |
| `test-results.json` | Actual automated results from this development environment. |
| `VERIFICATION.md` | Test environment, results and limitations. |

If you already applied an earlier schema, do not run this over it or delete useful data. Create a new empty database with a different name, or prepare a migration. `01_schema.sql` intentionally fails on existing tables rather than pretending an older schema is current.

## 1. Understand the pieces

**PostgreSQL** is the running database server that stores your data. **pgAdmin** is a graphical application that connects to it. Closing pgAdmin does not delete or stop the server's data. **psql** is an alternative command-line client.

A server can hold several **databases**. Inside a database, the `public` **schema** groups your tables. A **table** is a set of records; a **row** is one record; a **column** is a field. A **primary key** uniquely identifies a row. A **foreign key** links one row to another and prevents broken references. An **index** helps common lookups. A **view** is a reusable query, not a second copy of your data.

`BEGIN` starts a transaction. `COMMIT` saves it. `ROLLBACK` undoes it. The schema file commits its tables. The test and practice files roll back their sample rows. Identity counters may advance even after rollback; gaps in IDs are normal.

## 2. Install and connect on Windows

If PostgreSQL is already installed and running, keep it and skip installation.

1. Use the official [PostgreSQL Windows download page](https://www.postgresql.org/download/windows/). Its linked installer includes the server and pgAdmin. Include command-line tools if offered.
2. During installation, choose and save your local `postgres` administrator password. Keep the default port `5432` unless another installation uses it. Extra Stack Builder packages are not needed for these SQL files.
3. Open pgAdmin, expand **Servers**, and connect to your local PostgreSQL server using the password you selected. If no server appears, register one with host `localhost`, your chosen port, maintenance database `postgres`, and username `postgres`.
4. A pgAdmin master password, if requested, protects pgAdmin's saved credentials. It is separate from the PostgreSQL account password.

## 3. Create separate development and test databases

In pgAdmin, right-click **Databases → Create → Database**. Create:

- `garageguide`: future development/app data.
- `garageguide_test`: disposable testing and SQL practice.

For your initial local setup you may use `postgres` as owner. Before wiring up the deployed FastAPI app, create a dedicated restricted application role instead of using the administrator account. The app's `users` table stores GarageGuide accounts; those are different from PostgreSQL login roles.

## 4. Build the tables in each database

For `garageguide`:

1. Right-click the database and open **Query Tool**.
2. Confirm the connection is to `garageguide`, not the default `postgres` database.
3. Use **Open File** to load `01_schema.sql`.
4. Clear any text selection and use **Execute script** to run the whole file. Look for successful completion and no ERROR in Messages.
5. Open `02_views.sql` in the same connected Query Tool and execute the whole file.
6. Refresh **Schemas → public → Tables**. There should be ten tables; **Views** should contain `vehicle_expense_summary`.

Repeat the same steps for `garageguide_test` in a Query Tool connected to that database.

To verify which database you are using, execute:

```sql
SELECT current_database(), current_user, version();
```

To list the application tables:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

## 5. Run the tests in pgAdmin

1. Open Query Tool on **garageguide_test**.
2. Load `03_database_tests.sql` and execute the whole script, with no partial selection.
3. Look through Data Output/result sets for the table containing `test_id`, `feature_id`, `test_name`, and `result`. There should be **34 rows marked PASS**, followed by a summary with `passed_tests = 34`.
4. Messages should contain no unhandled ERROR. The final `ROLLBACK` is intentional: it cleans up fixtures, not a failed test.
5. Run the entire file again to confirm it is repeatable.

If your pgAdmin version displays only the last result, inspect the result-set selector or use the psql method below, which prints every result table.

A negative test deliberately tries something invalid, such as a negative cost. The test catches the expected PostgreSQL error and reports PASS. If invalid data is accepted, or the wrong error occurs, the script raises `FAIL DBxx` and the test run has failed. Do not count earlier PASS rows as a completed run.

After an error, run `ROLLBACK;` before trying again. Read the first error, correct its cause, then rerun the complete test file. Do not remove a failing test just to obtain a pass.

The fixture names and parts are synthetic. They do not represent verified real-world compatibility or usable credentials.

## 6. Run from Windows PowerShell instead (optional)

Open PowerShell in the extracted package folder. Set the path to your installed version (change `18` if needed):

```powershell
$pgBin = 'C:\Program Files\PostgreSQL\18\bin'
& "$pgBin\psql.exe" -h localhost -U postgres -d garageguide_test -v ON_ERROR_STOP=1 -f .\01_schema.sql
& "$pgBin\psql.exe" -h localhost -U postgres -d garageguide_test -v ON_ERROR_STOP=1 -f .\02_views.sql
& "$pgBin\psql.exe" -h localhost -U postgres -d garageguide_test -v ON_ERROR_STOP=1 -f .\03_database_tests.sql
$LASTEXITCODE
```

Run the first two commands only if you have not already built that database in pgAdmin. The test command can be repeated. Enter your local database password when prompted; it is not part of these files. Check each command succeeds before running the next.

`ON_ERROR_STOP=1` tells psql to stop when a statement fails. An exit code of `0` after the test command means it finished successfully; a nonzero value means investigate the error. The test output must also show all 34 PASS rows and the 34-test summary.

To capture evidence:

```powershell
& "$pgBin\psql.exe" -h localhost -U postgres -d garageguide_test -v ON_ERROR_STOP=1 -f .\03_database_tests.sql *> .\local-test-output.txt
$LASTEXITCODE
Get-Content .\local-test-output.txt
```

## 7. Practice reading and changing data

Run `04_practice_queries.sql` on `garageguide_test`. It creates a fake account, a sample Discovery and an oil-change record, reads them with JOIN, shows expenses, updates current mileage, and demonstrates that historical mileage remains unchanged. It ends with ROLLBACK, so the sample rows disappear.

Read the comments as you run it. Do not replace ROLLBACK with COMMIT unless you intentionally want to retain the examples. Avoid editing password fields or using example hashes for real authentication.

## 8. How this supports your features

| Tables | Role |
|---|---|
| `users`, `user_sessions` | Account storage and revocable/expiring session storage. |
| `vehicles` | Each user's cars, dirt bikes and other vehicles, with current miles/hours. |
| `service_records`, `service_parts` | Service details, costs and independent historical replacement-part snapshots. |
| `maintenance_schedules`, `maintenance_completions` | Recurrence intervals/baselines and links to completed services. |
| `parts`, `part_fitments`, `saved_parts` | Limited sourced catalog, documented fitment and personal references. |

The expense view totals each service once, includes vehicles with no services, and counts unknown costs separately. Its total is recorded maintenance/repair spending, not full ownership cost (fuel, insurance and depreciation are not modeled).

Upcoming/overdue calculations, dashboard responses and AI report generation still need Python/FastAPI code. The database stores their inputs. For future reminders, days/miles/hours and combined intervals are supported; reminder thresholds and completion-baseline selection need application tests. See TEST_PLAN.md.

Passwords and session tokens must be securely hashed by Python before storage. Schema constraints do not hash values, authenticate callers, enforce every route's ownership, or confirm part accuracy. FastAPI must obtain the owner from the authenticated session and filter private queries; accepting a user ID supplied by the browser is insufficient. Never connect React directly to PostgreSQL.

## 9. Troubleshooting and evidence

- **Connection refused:** confirm the Windows PostgreSQL service is running, and check host/port.
- **Password authentication failed:** use the PostgreSQL role password, not your pgAdmin master password.
- **Relation already exists:** the schema was already applied. Use the existing tables or a new empty database; do not delete your work blindly.
- **Relation does not exist:** check the connected database and run schema before views/tests.
- **Current transaction is aborted:** run `ROLLBACK;`, then fix the first reported error.
- **psql not recognized:** use its full path as shown above.

For your Work Log, capture the ten-table list and your 34-PASS test output, and link directly to SQL/test documentation after committing it to GitHub. Record actual work dates and time. This package does not update your tracker or claim eight hours of work.

Official references: [PostgreSQL Windows installation](https://www.postgresql.org/download/windows/), [psql and ON_ERROR_STOP](https://www.postgresql.org/docs/current/app-psql.html), [pgAdmin Query Tool toolbar](https://www.pgadmin.org/docs/pgadmin4/latest/query_tool_toolbar.html).
