# Unit 09 — Domain Extension Agents

## Goal

Implement the three smaller domain-specific worker agents:
`incident_management_agent`, `child_safety_agent`, and
`dpr_portal_agent` (FR-4, FR-5, FR-6).

## Design

Each contributes its own `[agent_name]` lines to the terminal log
panel and its own findings block in `AuditContextState.findings`.

## Implementation

1. Set the three prompt files
   (`apps/api/agents/prompts/incident_management_agent.md`,
   `child_safety_agent.md`, `dpr_portal_agent.md`) to the exact
   system prompts from `master-prompts-and-ui-ux-v3.md` §2.5–2.7,
   verbatim.
2. `incident_management_agent` (FR-4.1, FR-4.2): audit breach
   playbook documents (reuse `policy_agent`'s document-parsing
   utility from Unit 06 rather than duplicating it) for Rule 7
   template compliance; verify an automated alert/notification
   integration exists capable of a 72-hour DPB notification (Rule
   7(2)); check the notification payload schema for required fields
   (breach nature, impacted count, mitigation steps).
3. `child_safety_agent` (FR-5.1, FR-5.2): audit age-gating UI (via
   `frontend_agent`'s Stagehand session — reuse rather than opening a
   second browser session) and Rule 10 VPC integration (DigiLocker/
   virtual tokens); scan ad-tech/analytics scripts to confirm minors
   are excluded from behavioral tracking.
4. `dpr_portal_agent` (FR-6.1, FR-6.2): audit grievance-portal DB
   models/task queues for a ≤90-day SLA timer (Rule 14(3)); verify a
   nomination-of-representative flow exists (Section 14); audit API
   hooks for Consent Manager interoperability (Section 6(7)–(9),
   Rule 4).
5. Each finding cites its specific Section/Rule per Invariant 3.

## Dependencies

- Reuses Unit 06's document parser and Unit 08's Stagehand session —
  do not stand up a second browser or a second PDF parser for this
  unit; if code sharing turns out to be impractical, flag it as a
  split decision in `progress-tracker.md` rather than duplicating
  silently.

## Verification Checklist

- [ ] A test breach-playbook missing the 72-hour pipeline is flagged
      under Rule 7(2)
- [ ] A test site with no age-gating is flagged under Section 9/Rule
      10
- [ ] A test grievance portal with a 120-day SLA is flagged under
      Rule 14(3)
- [ ] All three agents' findings appear in their own
      `AuditContextState.findings` keys (`incident`, `child_safety`,
      `dpr_portal`) matching the schema in
      `agent-flow-and-interagent-bus-v3.md`
- [ ] No duplicate browser session or duplicate document-parsing
      logic was introduced (reuse confirmed by code review)
