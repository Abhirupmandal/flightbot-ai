# Testing AeroScheduler Expert System

## Overview
The AeroScheduler Expert System is a Flask web app for airline flight and cargo scheduling with a rule-based inference engine (15 rules, forward chaining).

## Starting the Server
```bash
cd /path/to/repo
pip install -r requirements.txt
python app.py
# Server runs at http://localhost:5000
```

The app uses **in-memory storage** — data resets on server restart. Restart the server before testing to get a clean slate.

## UI Navigation
- **Dashboard** (`/`): Shows summary stats (total flights, cargo, approved, rejected, warnings, total cargo weight). Also shows detected schedule conflicts.
- **Flight Scheduling** (`/flights`): Form to add flights + table of scheduled flights with status badges.
- **Cargo Scheduling** (`/cargo`): Form to add cargo shipments + table with utilization progress bars + cargo summary.
- **Knowledge Base** (`/knowledge`): Read-only reference tables for aircraft fleet (6), airports (8), cargo types (6), expert rules (15), and scheduling parameters.

## Form Submission Behavior
- Forms submit via **AJAX** (`fetch()` with JSON body), not traditional form POST.
- On success, results display inline (validation alerts + status banner) for ~2 seconds, then the page **auto-reloads**.
- The inline validation results flash briefly — to inspect them, you may need to intercept the reload (e.g., add a breakpoint or extend the timeout in `flights.html`/`cargo.html`).
- After reload, the flight/cargo table shows the new entry with its final status badge.

## Key Test Scenarios

### Flight Rejection (Range Exceeded)
- Aircraft: `B737-800` (range 5765 km), Route: `JFK → DXB` (11023 km)
- Expected: **Rejected** — Rule R01 fires
- Message contains: "11023 km exceeds max range 5765 km"

### Flight Approval (Valid Route)
- Aircraft: `B777-300ER` (range 13650 km), Route: `JFK → LHR` (5539 km)
- Expected: **Approved** — no rules fire

### Cargo Rejection (Hazmat Overweight)
- Aircraft: `B737-800`, Route: `JFK → LAX`, Cargo: `Hazardous Materials`, Weight: `600 kg`, Flight Type: `Passenger`
- Expected: **Rejected** — Rule R08 fires (hazmat limit 500 kg per flight)
- Also triggers R13 (hazmat on passenger flight warning)

### Cargo Approval (Valid Freighter)
- Aircraft: `B747-400F` (capacity 112760 kg), Route: `JFK → LHR`, Cargo: `General`, Weight: `50000 kg`, Flight Type: `Dedicated Freighter`
- Expected: **Approved** — R14 info recommendation fires

### Dashboard Verification
- After adding flights/cargo, dashboard stats should update to reflect exact counts.
- Conflict detection may flag gate conflicts if two flights depart from the same airport at similar times.

## Tips for Browser Testing
- Time inputs (`type="time"`) can be tricky to fill via computer use tool. Use JavaScript via console to set values reliably:
  ```javascript
  document.querySelector('input[name="departure_time"]').value = '10:00';
  document.querySelector('input[name="arrival_time"]').value = '22:00';
  ```
- Select dropdowns can also be set via JS:
  ```javascript
  document.querySelector('select[name="aircraft"]').value = 'B777-300ER';
  document.querySelector('select[name="destination"]').value = 'LHR';
  ```
- After setting values via JS, you can click the submit button normally with the computer use tool.

## API Endpoints (alternative to UI testing)
- `POST /api/flights` — JSON body with `flight_number`, `aircraft`, `origin`, `destination`, `departure_time`, `arrival_time`
- `POST /api/cargo` — JSON body with `aircraft`, `origin`, `destination`, `cargo_type`, `weight_kg`, `volume_m3`, `is_passenger_flight`
- `GET /api/summary` — returns current schedule summary
- `GET /api/conflicts` — returns detected scheduling conflicts

## Devin Secrets Needed
None — this is a self-contained Flask app with no external dependencies or authentication.
