# Unit 14 — Wire Audit Submission & Telemetry

## Goal

Connect the Unit 11 input screen to the real `POST /audits` endpoint
(Unit 04/05) and the Unit 12 telemetry screen to the real SSE stream,
replacing all mock data with live data for the first time.

## Design

No new visual design — this unit changes data sources only, per the
layouts already built in Units 11–12.

## Implementation

1. Replace Unit 11's console-log-on-submit with a real authenticated
   `POST /audits` call (using the session from Unit 03); on success,
   navigate to the telemetry screen with the returned `audit_id`.
2. Replace Unit 12's mock-interval log source with a real
   `EventSource` connection to `GET /audits/{audit_id}/stream`;
   parse each event's agent tag and route it to the correct panel
   exactly as the mock-data interface from Unit 12 already expects.
3. Handle SSE reconnection/error states (connection drop mid-audit)
   gracefully — show a reconnecting indicator rather than a blank
   panel.
4. On receiving a terminal `status: COMPLETED` (or `FAILED`) event,
   navigate to the dashboard route with `audit_id` (dashboard itself
   is wired in Unit 15).

## Dependencies

- Native `EventSource` (or a small SSE client wrapper) — no new major
  library required.

## Verification Checklist

- [ ] Submitting the Input screen creates a real `audits` row scoped
      to the caller's `organization_id`
- [ ] The telemetry screen shows real log events tagged by real agent
      names as the backend graph (Unit 05/10) actually executes
- [ ] A simulated connection drop shows a reconnecting state and
      recovers without losing already-displayed log lines
- [ ] Reaching `COMPLETED` or `FAILED` status navigates correctly
- [ ] No mock data path remains reachable in production code
