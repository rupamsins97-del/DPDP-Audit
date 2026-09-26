# Unit 15 — Wire Dashboard to Live Findings

## Goal

Connect the Unit 13 dashboard to real `compliance_score` and
`audit_findings` data via the gateway, for a completed audit produced
by Unit 10's real `synthesis_agent`.

## Design

No new visual design — same layout as Unit 13, real data.

## Implementation

1. Add/confirm `GET /audits/{audit_id}` (from Unit 04) returns the
   final `compliance_score` and the full `audit_findings` list,
   scoped to the caller's `organization_id`.
2. Replace Unit 13's mock findings array with data fetched from this
   endpoint on the dashboard route.
3. Map each finding's real `agent_role` to the correct Action button
   label using the same mapping already built in Unit 13 — no new
   mapping logic, just a new data source.
4. Handle the empty/zero-findings case (a fully compliant audit) with
   a clear "no violations found" state rather than an empty table.

## Dependencies

- None beyond what Units 04, 10, and 13 already provide.

## Verification Checklist

- [ ] Loading the dashboard for a real completed audit shows the
      real compliance score in the correct color band
- [ ] Every real finding row shows the correct severity, section
      citation, and action label
- [ ] A different organization's session cannot load this audit's
      dashboard (re-verify isolation at this new read path)
- [ ] A zero-findings audit renders a clear compliant-state message,
      not an empty table
- [ ] `npm run build` passes
