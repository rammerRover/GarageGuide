# Build Plan

Features are listed in implementation order. The current React scaffold,
responsive connectivity screen, FastAPI health endpoints, PostgreSQL schema,
and database verification are completed foundation. They do not make any of
the product features below complete.

Each feature should be planned, reviewed, implemented, tested, audited, and
approved before it is marked complete. Future features excluded by the Project
Plan must not be introduced during these feature loops.

## MVP Features

- [ ] 1. **Register a user account.** Validate email and password input, prevent
  duplicate accounts, hash the password, and give the user clear success and
  error results without exposing sensitive details.
- [ ] 2. **Sign in, sign out, and protect private sessions.** Verify credentials,
  create expiring and revocable sessions, protect private routes, and confirm
  that one user cannot access another user's records.
- [ ] 3. **Create and list vehicles in a digital garage.** Allow an authenticated
  user to add cars and recreational vehicles using manual year, make, model,
  engine, type, mileage, and/or operating-hour information, then display only
  that user's vehicles.
- [ ] 4. **View and update a vehicle profile.** Let the owner review and correct
  vehicle details and current readings while preserving readings already saved
  with historical service records.
- [ ] 5. **Record and review service history.** Create, list, edit, and remove
  dated maintenance, repair, inspection, and diagnostic records with
  descriptions, optional readings, optional cost, notes, and clear ownership
  checks.
- [ ] 6. **Record parts used during a service.** Save catalog-backed or manual
  part snapshots with the service so historical part details remain available
  even if a saved reference or catalog entry later changes or is removed.
- [ ] 7. **Create and update maintenance schedules.** Support positive day,
  mileage, and operating-hour intervals with matching baselines, source notes,
  validation, and duplicate-task review without inventing manufacturer
  recommendations.
- [ ] 8. **Calculate maintenance status and in-app reminders.** Calculate
  upcoming, due, and overdue work from dates and available readings, use the
  first reached limit for combined schedules, and clearly identify missing or
  stale information.
- [ ] 9. **Complete scheduled maintenance.** Record completed work or link an
  existing service record to one or more schedules, prevent duplicate links or
  partial saves, and calculate the next due occurrence without duplicating
  expenses.
- [ ] 10. **Search the limited parts catalog.** Search supported parts by name,
  category, or part number and show stored source, verification, and vehicle
  fitment information without presenting uncertain matches as confirmed.
- [ ] 11. **Save parts to a vehicle.** Save catalog results or manually confirmed
  part information, distinguish their origins, support editing and removal,
  prevent duplicates, and preserve historical service-part snapshots.
- [ ] 12. **Review vehicle expenses.** Summarize each owned vehicle's known
  service costs, link the total to contributing records, keep unknown costs
  distinct from zero, and update the summary after service changes.
- [ ] 13. **Generate an AI-assisted vehicle report.** Send only the necessary
  verified records for the selected vehicle to an approved AI provider and
  produce a labeled summary of service history, expenses, and maintenance
  status. Explain missing data, handle provider failures, link back to source
  records, and do not diagnose problems or determine part compatibility.
- [ ] 14. **Build the responsive garage dashboard and navigation.** Present the
  user's vehicles, recent services, maintenance status, in-app reminders, and
  recorded costs with clear links to the completed features. Distinguish empty,
  loading, partial-failure, and unavailable states on phone, tablet, and
  desktop layouts.
- [ ] 15. **Deploy and verify the complete MVP.** Deploy the React frontend,
  FastAPI backend, and PostgreSQL database using private environment
  configuration. Verify the complete user journey, stored-data persistence,
  HTTPS, session protection, owner isolation, responsive interaction, and
  failure recovery in the deployed environment.

## Future Features Outside This Build Plan

- VIN decoding
- Owner's-manual scanning or AI extraction
- Complete parts compatibility coverage or automatic catalog synchronization
- Receipt and document scanning
- Email, text-message, mobile, or push notifications
- Shared household garages
- Repair-shop and fleet management
- Subscription billing, advertising, and payment processing

These items remain unchecked future ideas and must not be treated as part of
the course MVP.
