# Coding Standards

GarageGuide uses React 19, Vite, JavaScript, plain CSS, Python 3.13, FastAPI,
psycopg, and native PostgreSQL. Follow the proportional-engineering contract in
`AGENTS.md`. Add machinery only for established requirements.

## Runtimes and Dependencies

- Use the existing fnm-managed Node installation satisfying the frontend engine
  requirement (22.12+) and npm with `frontend/package-lock.json`.
- Use `backend/.venv/Scripts/python.exe` for backend commands. Do not create a
  root virtual environment or download runtimes during ordinary feature work.
- Declare runtime Python dependencies in `backend/requirements.txt`, and test
  dependencies in `backend/requirements-dev.txt`. Keep `pyproject.toml` for
  tool settings unless a separately approved change establishes packaging.
- Reuse existing dependencies and native framework features. Do not add
  TypeScript, an ORM, a CSS framework, or a test runner as incidental setup.

## React

- Functional components only (no class components)
- Use hooks for state and side effects
- Keep components focused - one job per component
- Extract a custom hook only when reusable behavior warrants one
- This is a client-rendered Vite application using JavaScript and JSX
- Keep request helpers in `frontend/src/api.js` while that remains sufficient
- Preserve explicit loading, success, unavailable, disabled-request, and retry
  behavior for asynchronous controls

## FastAPI

- Keep app creation and router registration in `backend/app/main.py`
- Keep endpoint handlers in `backend/app/routes/`; place database operations
  and configuration in the existing backend modules while they remain focused
- Validate new request boundaries with FastAPI request models and return
  meaningful HTTP status codes with user-safe errors
- Keep synchronous psycopg work in synchronous handlers; do not block an async
  handler with synchronous database calls
- Startup must not create, alter, reset, or seed database objects

## File Organization

- `frontend/src/`: React entry point, components, API helper, and styles
- `backend/app/`: FastAPI application, settings, database access, and routes
- `backend/tests/`: pytest tests and fixtures
- `database/`: authoritative schema, views, SQL assertions, and practice scripts
- `docs/verification/`: dated verification evidence and manual instructions
- Create feature subdirectories only when the code needs them

> TODO: Choose client-side routing when product navigation needs it. No router
> or frontend routing convention is configured yet.

## Naming

- React component names and component files: PascalCase (`ItemCard.jsx`)
- JavaScript functions and variables: camelCase
- Python modules, functions, and variables: snake_case
- Python classes: PascalCase
- Constants: SCREAMING_SNAKE_CASE
- SQL identifiers: snake_case, following the existing schema

## Styling

- Use plain CSS in `frontend/src/styles.css`, extending the existing light theme
- Prefer fluid widths, Grid/Flexbox, and content-driven breakpoints
- Check layouts around 375, 768, and 1440 pixels and avoid horizontal overflow
- Use semantic HTML, labels, keyboard-reachable controls, visible focus, and
  understandable status text that does not depend on color alone
- Announce asynchronous status changes through the existing live-region pattern

## Database

- PostgreSQL SQL in `database/` is the source of truth; use psycopg, not an ORM
- Use parameterized queries and short-lived, context-managed connections
- Keep health checks read-only, bounded by timeouts, and limited to connectivity
  and expected schema presence
- Use `garageguide_app` for development and `garageguide_app_test` for tests
- Never run fixture-based SQL on development data; existing fixture scripts
  roll back rows but can advance identity counters
- Do not reapply the initial schema to an initialized database. Plan future
  schema changes explicitly without resetting or deleting existing data
- Preserve historical mileage/hours, unknown versus zero costs, completion
  integrity, and the expense view's aggregation rules
- Development database verification is deferred. Onboarding must not connect
  to, initialize, or modify databases

## Data Fetching

- React calls relative `/api` URLs through the Vite development/preview proxy
- Only FastAPI receives database credentials or connects to PostgreSQL
- Keep private environment values in ignored `backend/.env` and
  `backend/.env.test`; examples contain placeholders only
- Test configuration must reject any effective database name other than
  `garageguide_app_test` and must never load development credentials
- Authentication and ownership enforcement are not implemented yet. Future
  private routes must derive the owner from the authenticated session and scope
  queries accordingly; never trust a browser-supplied owner identifier

## Error Handling

- Return generic backend errors without passwords, connection strings, SQL, or
  driver details; keep logs free of private connection details
- Keep the current FastAPI HTTP error response shape unless a feature requires
  a reviewed API change
- Use bounded frontend requests, readable unavailable messages, and a usable
  retry action; do not display raw backend exceptions

## Testing

Backend pytest is already configured in `backend/pyproject.toml`, with tests in
`backend/tests/`. The `Test` command in `AGENTS.md` enables the backend logic
gate and excludes native database integration. Run that documented command;
use focused tests while developing and the full applicable gate before review.

There is no frontend unit-test runner, typecheck, formatter, combined Verify
command, or GitHub Actions workflow. Frontend work currently uses ESLint, the
production build, and direct browser evidence where applicable. Do not silently
install missing tooling. `/tests` and `/ci` own explicit test and CI setup.

When `AGENTS.md` declares a `Verify` command, treat it as the umbrella automated
gate. It combines only the checks this project actually has, in this order when
available: typecheck, tests, then build. The command does not enable an absent
test runner or replace focused evidence. It gives local work and optional CI one
exact command to run. `/ci` owns Verify and CI setup. `/tests` adds the real test
command to Verify when it already exists, but never creates CI only because
testing was configured.

**The opt-in switch is one signal: a `Test` command in the Commands section of
`AGENTS.md`.** Declare one and **tests become a gate for logic-bearing steps**,
not an optional extra; leave it out and the loop verifies logic with the evidence
it already uses (run it, a screenshot, the build). Adding the runner is itself a
deliberate step, never a silent mid-step install. This is the single definition
of the switch; the skills and `ai-interaction.md` only point back here.

- **What to test (the scope rule):** logic where a wrong answer is possible,
  such as parsers, formatters, validators, calculations, or API error handling. These have
  assertable inputs and outputs and real edge cases (empty, missing, malformed).
- **What not to unit test:** static markup, cosmetic changes, implementation
  details, or tests that only mirror the code. Use browser/API evidence for
  integration behavior and preserve the existing health-route tests.
- **The gate (when a runner is configured):** a build step that adds in-scope logic
  must ship a passing test in the same reviewable diff. The project's test command
  must be green before the step is approved, before any checkpoint commit, and
  before `/complete` merges. UI and integration-only steps are exempt and ride on
  screenshot plus build evidence.
- **When it's named:** the `/feature` spec's Testing section predicts the coverage,
  `/implement` writes the test with the step, and if a step surfaces logic the spec
  didn't foresee, add a focused test then.
- An empty suite should fail, not pass, so "no tests ran" never looks like "passed".
- Backend test files live in `backend/tests/` and use `test_*.py` names.
- Run them via the project's test command (see Commands in `AGENTS.md`), not a
  hardcoded tool name.

Use pytest fixtures and monkeypatching for deterministic backend behavior.
Native PostgreSQL integration requires both `RUN_DB_TESTS=1` and effective
`PGDATABASE=garageguide_app_test`. It is opt-in, not part of the normal Test
command. Keep application integration checks read-only. Historical PGlite
results are not evidence of current native application connectivity.

## Browser Verification

For UI and integration behavior, prefer real browser evidence over reading the
code and assuming it works.

- Browser automation is separately opt-in through `/tests browser`. That setup
  reuses a compatible runner or prefers Playwright for supported projects, then
  documents the exact command as `Browser tests` in `AGENTS.md`.
- When `Browser tests` is declared, add focused coverage for stable behavioral
  done-whens when it is proportionate, and run the documented command during
  `/check`. Do not assume it proves visual fidelity, real authenticated-profile
  behavior, browser chrome, or another claim the test does not observe.
- If no Browser tests command is declared, do not add a runner silently in the
  middle of an unrelated feature. Use the available dev server, browser
  screenshots, build output, API output, or manual evidence instead.
- Browser tests are not part of the default Verify command or CI unless the user
  separately chooses that slower gate.
- Browser evidence is especially important for flows that click, type, submit,
  navigate, download files, render complex layouts, or depend on client-side
  state.

## Code Quality

- No commented-out code unless specified
- No unused imports or variables
- Keep functions under 50 lines when possible

## Comments

Write code that explains itself; comment only what the code cannot say.
Over-commenting is a common AI tell, so resist it.

- Comment the **why**, not the **what**. Delete any comment that restates the code.
- No banner/header blocks, section dividers, or step-by-step narration of obvious
  code. A file does not need a comment announcing each region.
- A comment earns its place only when it captures something the code can't: a
  non-obvious decision, a gotcha or workaround, why a value is what it is, or a
  link to a spec or issue.
- Prefer self-documenting names and small functions over explanatory comments.
- Keep doc comments minimal: a one-line purpose on an exported type or function is
  plenty; don't write JSDoc that just repeats the signature.
- When in doubt, leave the comment out.

## Writing

- No em dashes (U+2014) in generated content: docs, comments, commit messages,
  READMEs, specs. They read as AI-generated.
- Use a hyphen for `term - description` separators; rephrase prose with commas,
  parentheses, or a colon. Avoid en dashes and the ellipsis character too.
