# Manual browser verification

Start both applications with the initialized development database using the root README. Record actual results, date, browser/version and viewport sizes separately from historical evidence. These checks remain pending until performed.

## Connection button

1. Open `http://127.0.0.1:5173`. Confirm the initial ready-to-check message.
2. Tab to **Check connection**, confirm visible keyboard focus, then press Enter.
3. Confirm **Checking…** appears and the button is disabled during the request. Browser network throttling can make this short state easier to observe.
4. Confirm **Connected. GarageGuide is ready.** Developer tools should show `GET /api/health/db` returning HTTP 200 with `status: ok`, `database: connected`, and `schema: ready`.
5. Confirm requests use the frontend origin, contain no database credentials, and produce no console errors.

## Responsive foundation

1. Use device emulation at widths of 375, 768 and 1440 pixels, then resize between them.
2. Confirm no horizontal scrolling, clipped text, overlaps or inaccessible controls. On mobile, the button sits beneath the status; wider layouts place it alongside.
3. Repeat at 200% zoom and navigate by keyboard. Confirm readable text, visible focus and reachable controls. Status must be understandable without relying on color.
4. Repeat with the longer unavailable message. Record which browsers and sizes were actually checked.

## Database unavailable and retry

1. Keep FastAPI and the browser running. Temporarily change `PGPORT` in private `backend/.env` to a confirmed unused local port (for example 65432). Remove exported `PGPORT` overrides first if necessary. This avoids stopping a shared PostgreSQL service.
2. Click **Check connection**. Expect a loading state, then **Connection unavailable. Please try again.** and an enabled **Try again** button. The request should return HTTP 503 with a generic message.
3. Confirm `http://127.0.0.1:8000/api/health` still returns HTTP 200.
4. Restore the original port. Settings are read for each request; restarting FastAPI is unnecessary.
5. Click **Try again** without refreshing. Confirm a new request succeeds and the connected message returns.
6. Optionally stop FastAPI, check that the UI recovers from that failure too, then restart it and retry.

Restore temporary configuration after checking. Do not delete tables or alter development records to simulate an outage.
