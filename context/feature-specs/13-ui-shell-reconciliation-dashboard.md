# Unit 13 — UI Shell: Reconciliation Dashboard

## Goal

Build the static Reconciliation Dashboard — compliance index
badge/gauge plus the findings table — against mock data matching the
exact example rows in the master-prompts mock.

## Design

Per `ui-context.md` layout pattern 3: a compliance badge at top
(colored via `--state-success`/`--state-warn`/`--state-error`
depending on score band) showing e.g. "Overall DPDP Compliance Index:
72% [WARN]", and a findings table below with columns exactly
`Violation Title | Severity | Section | Action`. Severity cells use
the severity color tokens. Action cells render a button whose label
depends on `agent_role`: "View Network Trace" (frontend), "Apply
Auto-Fix PR" (backend), "Generate DB Script" (backend/retention),
"Download DPA Clause" (policy).

## Implementation

1. Build with mock findings data matching the four example rows in
   `master-prompts-and-ui-ux-v3.md` §1.1 (Pre-Consent Meta Pixel
   Fire / CRITICAL / Sec 6(1); Plaintext PII Logging / HIGH / Sec
   8(5); Missing Erasure Cron Job / HIGH / Sec 8(7); DPA 60-day
   Retention Term / CRITICAL / Rule 6(1)(e)).
2. Use shadcn `Table` and a `Badge` component for severity, styled
   with the tokens from `ui-context.md` — no hardcoded colors.
3. Action buttons in this unit only open a placeholder modal/toast —
   real behavior (network trace viewer, patch apply, etc.) arrives in
   Units 15–16.
4. Sort the table by severity (CRITICAL first) by default, with
   client-side column sorting available.

## Dependencies

- shadcn/ui `Table`, `Badge`, `Dialog` (for the placeholder modal).

## Verification Checklist

- [ ] The compliance badge renders in the correct color band for a
      given mock score (test at least one value in each of PASS/WARN/
      FAIL)
- [ ] The findings table renders all four mock rows with correct
      severity coloring and correct action-button labels per
      `agent_role`
- [ ] Default sort places CRITICAL findings first
- [ ] Clicking an action button opens a placeholder modal, no real
      API calls yet
- [ ] `npm run build` passes
