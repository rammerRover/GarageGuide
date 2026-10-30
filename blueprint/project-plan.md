# Project Plan

## 1. Title and Tagline - What is the project called, and what's it about?

The title of this project is **GarageGuide - Know Your Vehicle's History. Plan
Its Future.**

GarageGuide is a vehicle maintenance and parts assistant that helps owners and
at-home mechanics organize service records, plan upcoming maintenance, track
expenses, and save replacement-part information.

The current application is a technical backbone with a connectivity screen,
health checks, and a PostgreSQL schema. The features below describe the
intended minimum viable product (MVP), not functionality that is already
complete.

## 2. Problem - What problem are we solving?

Vehicle owners and at-home mechanics often have maintenance records, receipts,
part numbers, service recommendations, and owner's manuals scattered across
glove compartments, websites, emails, and personal notes. This makes it
difficult to determine what work has already been completed, what maintenance
is approaching, and which replacement parts belong to a specific vehicle.

This becomes especially difficult when someone maintains several types of
vehicles. My family owns cars, dirt bikes, and a RZR, and my dad currently has
to keep track of the maintenance needs and parts for all of them. GarageGuide
will provide one organized location for this information. It will support
vehicles that use mileage, operating hours, or both. Missing readings and costs
will remain unknown instead of being treated as zero.

GarageGuide is not intended to diagnose mechanical problems, replace a
qualified mechanic, or use AI to guarantee part compatibility. Its purpose is
to organize verified information, make maintenance easier to track, and help
users understand the recorded history and upcoming needs of their vehicles.

## 3. Users - Who is this for?

The primary users will be individual vehicle owners and at-home mechanics who
maintain one or more vehicles. This includes families managing several cars and
enthusiasts working on motorcycles, dirt bikes, ATVs, RZRs, or similar
recreational vehicles.

Users may perform maintenance themselves or record work completed by a
mechanic. Each user will have a private account and will be able to access only
their own vehicles and associated records. The MVP will focus on individuals
and families. Shared garages, commercial repair shops, fleet operators, teams,
and role-based organizations are outside its scope.

## 4. Team Members - Who is working on this and how are they qualified?

- **Ethan Pearson:** I am completing this project individually. I have
  experience with Java, Python, Node.js, React, Django relational
  database design, and full-stack web development. For this project I want to
  use a full standalone relational database and I chose PostgreSQL.
  I will plan the application,
  review its architecture, design and maintain its database, develop and
  review the frontend and backend, test its features, document my decisions,
  and deploy the completed application.

## 5. Features - What does the MVP need?

- **User accounts and authentication:** Users can register, sign in, sign out,
  and securely access only their own GarageGuide records.
- **Digital garage:** Users can add and manage multiple vehicles. Each profile
  can contain the year, make, model, engine, vehicle type, and current mileage
  and/or operating hours.
- **Service and repair history:** Users can record and review routine
  maintenance, repairs, inspections, diagnostic results, costs, notes,
  readings, and replaced parts. Historical service readings and part details
  remain unchanged when current vehicle information or saved-part references
  change.
- **Maintenance schedules:** Users can create and update recurring maintenance
  items based on dates, mileage, operating hours, or a combination of limits.
- **Maintenance status and reminders:** GarageGuide calculates upcoming, due,
  and overdue work from saved schedules and available vehicle readings. Missing
  information is identified instead of producing a misleading status.
- **Maintenance completion:** Users can record completed maintenance or link an
  existing service record to one or more schedules without duplicating service
  costs.
- **Limited parts lookup:** Users can search a curated collection of parts for
  supported vehicle configurations. Results include stored part information,
  fitment details, source information, and verification dates. Incomplete
  fitment data is not presented as confirmed compatibility.
- **Saved parts:** Users can save catalog results or manually confirmed part
  names, numbers, notes, and manufacturers to a vehicle for later reference.
- **Expense tracking:** Costs recorded in service entries are summarized by
  vehicle. Unknown costs are excluded and identified, while a recorded cost of
  zero remains a valid known value.
- **AI-assisted reports:** Users can request readable summaries of a selected
  vehicle's recorded service history, expenses, and maintenance status. Reports
  use verified data stored in GarageGuide, identify missing information, are
  labeled as AI-generated, and do not diagnose mechanical problems or decide
  part compatibility.
- **Vehicle dashboard:** A responsive dashboard gives users a high-level view
  of their garage, including vehicles, recent services, upcoming or overdue
  maintenance, and recorded costs.

### Explicitly excluded from the MVP

- VIN decoding and automatic vehicle entry
- Owner's-manual scanning and AI extraction
- A complete parts-compatibility database covering every vehicle
- Receipt and document scanning
- Email, text-message, mobile, or push notifications
- Shared household accounts and collaborative garages
- Repair-shop and fleet workflows, including customers, work orders, employee
  permissions, and large-scale inventory
- Payment processing, subscriptions, and advertising

These may be considered after the course if the MVP is complete and a separate
product decision approves the additional scope.

## 6. Data - What are we storing?

GarageGuide uses a relational PostgreSQL database to store:

- **Users and sessions:** normalized email addresses, password hashes, and
  hashed session tokens with creation, expiration, and revocation timestamps.
  Plaintext passwords and raw session tokens are never stored.
- **Vehicles:** owner, year, make, model, vehicle type, optional engine, current
  mileage and/or operating hours, and reading update time.
- **Service records:** vehicle, date, service category, description, optional
  readings, optional total cost, and notes. Historical readings describe that
  service and are not rewritten when the vehicle's current reading changes.
- **Maintenance schedules and completions:** day, mileage, and operating-hour
  intervals with matching baselines, source notes, and links between completed
  work and service records. Completion values come from the service record
  rather than being duplicated.
- **Parts catalog and fitments:** manufacturer, part number, name, category,
  supported vehicle configuration, configuration notes, source URL, and
  verification date.
- **Saved vehicle parts:** catalog references or manual entries saved for later
  use.
- **Service parts:** historical snapshots of parts actually used during a
  service, including identifying details, quantity, and notes.
- **Report inputs:** selected vehicle, service, expense, and maintenance data
  needed to produce an AI-assisted report. Generated reports do not become a
  substitute for the underlying records.

The numbered SQL files in `database/` are the schema source of truth. Expense
summaries are calculated from service-record costs. Maintenance status is
calculated from schedules and available current readings. The initial parts
catalog is intentionally limited and requires a documented curation process.

Account and vehicle records can reveal information about a user's possessions,
expenses, and vehicle history. Passwords are hashed, private routes require
account ownership checks, and deployed communication uses encrypted
connections. Outside services receive only the information necessary for the
selected request. An AI provider must not receive passwords, session tokens,
complete account information, unrelated vehicles, or another user's records.
GarageGuide will not sell user or vehicle data.

## 7. Tech - What stack are we using?

- **Frontend:** React 19, Vite, JavaScript, HTML, and CSS
- **Frontend-to-backend communication:** the Fetch API
- **Backend:** Python 3.13 and FastAPI
- **Database access:** psycopg with parameterized SQL
- **Database:** PostgreSQL using the existing hand-managed SQL scripts
- **Authentication:** secure password hashing, private sessions, expiration,
  revocation, secure cookies in production, and owner-scoped authorization
- **AI integration:** an external AI API that receives only the selected,
  necessary stored data and produces grounded, labeled summaries
- **Vehicle data:** a vehicle-data API may be evaluated where appropriate, but
  the MVP must continue to support manual vehicle entry and cannot depend on a
  paid service
- **Testing and quality checks:** pytest, PostgreSQL assertion scripts, ESLint,
  frontend production builds, and manual browser verification
- **Version control:** Git and GitHub

There is currently no ORM or automatic schema creation. Do not introduce an ORM
or migration framework without an approved feature and a clear reason. Database
constraints protect data integrity, while FastAPI must also enforce validation,
authentication, and record ownership.

## 8. Related Work - Who has done similar work before?

- **[CARFAX Car Care](https://www.carfax.com/Service/):** Tracks service
  history, maintenance reminders, recalls, and multiple cars. It demonstrates
  the value of placing maintenance history and upcoming service information in
  one location. GarageGuide places more emphasis on user-recorded work, saved
  parts, recreational vehicles, and personalized reports.
- **[AUTOsist](https://autosist.com/features/):** Provides preventive
  maintenance schedules, service histories, reminders, inspections, reports,
  and parts-inventory tools. It shows how maintenance records become more
  useful when connected to reminders and reports. GarageGuide focuses on
  individuals, families, and at-home mechanics rather than fleet operations.
- **[Simply Auto](https://simplyauto.app/):** Tracks maintenance, mileage,
  fuel, and expenses across multiple vehicles. GarageGuide uses a similar
  centralized approach while placing more emphasis on repairs, saved
  replacement parts, recreational vehicles, and AI-assisted summaries.

These products demonstrate the value of centralized vehicle records.
GarageGuide combines maintenance tracking, limited verified parts information,
family and recreational vehicles, expense summaries, and grounded AI-assisted
reports for at-home vehicle maintenance.

## 9. Monetization - How will this make money?

GarageGuide will not include payment or money-making features during this
course. The MVP will initially be available free to people I know so that I can
test whether it is useful and collect feedback.

If the application received future funding, it could use a subscription or
freemium model. A free plan could include a limited number of vehicles and
basic maintenance tracking. A paid plan could provide additional vehicles,
document storage, household sharing, advanced reports, and expanded parts-data
access. GarageGuide could also receive affiliate revenue when a user chooses to
purchase a verified part through a linked retailer. Selling user or vehicle
data would not be part of the business model.

## 10. UI/UX - How should this look and feel?

GarageGuide should have a clean, modern appearance inspired by a well-organized
garage. It should remain approachable to users with limited mechanical
knowledge while providing useful detail to experienced at-home mechanics.

- A garage overview showing vehicles and upcoming or overdue maintenance
- Vehicle profiles with current information, service history, expenses, and
  saved parts
- Straightforward forms for recording vehicles, services, schedules, parts,
  and costs
- A parts lookup with clear fitment and source information
- Readable AI-assisted reports linked to the underlying records
- Responsive layouts that work on computers, tablets, and phones
- Clear loading, empty, unavailable, and retry states

Unknown mileage, operating hours, and costs must appear differently from a
recorded zero. Maintenance status should show the due value and the information
used to calculate it. A part is presented as compatible only when its stored
fitment information is complete enough and has a documented source.

## 11. Deployment - Where and how will this ship?

GarageGuide will be deployed as a browser-based web application. Users will not
install traditional desktop software. They will visit the application, create
an account, and sign in to access their digital garage.

The React frontend will likely be hosted through Vercel. The FastAPI backend
will use a compatible cloud-hosting service, and PostgreSQL will use a managed
database provider. Final providers will be selected based on project
compatibility and available free or educational hosting.

The current development setup remains local: Vite serves the frontend on
`127.0.0.1:5173`, proxies `/api` to FastAPI on `127.0.0.1:8000`, and FastAPI
connects to PostgreSQL. The frontend production build is generated in
`frontend/dist/`. The database is provisioned separately from the application
and initialized with the numbered files in `database/`; schema creation is not
automatic.

Backend configuration and service credentials are supplied through private
environment variables. Database credentials and AI keys must never be included
in frontend assets or committed to Git. The deployed application must use
encrypted connections and verify that private routes reject missing, expired,
revoked, and wrong-owner sessions.

## 12. Product and Implementation Constraints

- The SQL schema and views in `database/` remain the database source of truth.
- The development database is `garageguide_app`; application tests use only
  `garageguide_app_test`.
- Product features are developed as small, reviewable vertical slices through
  React, FastAPI, and PostgreSQL.
- Private records require authentication and owner-scoped authorization before
  they are returned or changed.
- Database health checks remain read-only and do not expose credentials,
  product data, or sensitive driver errors.
- AI-assisted reports use only verified stored data for the selected vehicle,
  are clearly labeled, identify missing data, and do not diagnose mechanical
  problems or determine part compatibility.
- Reminders remain inside the application during the MVP; no background worker
  or scheduled notification service is required.
- Do not add future features, hypothetical scaling infrastructure, or paid
  services without reviewing the change against the course timeline.
