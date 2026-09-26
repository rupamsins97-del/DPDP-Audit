# Unit 10 — `synthesis_agent` & Scoring

## Goal

Replace the Unit 05 stub with the real `synthesis_agent`: full
parallel dispatch to all six workers, promise-vs-reality
reconciliation, the DPDP Compliance Index computation, and a hashed
immutable audit trail (NFR-1, NFR-3).

## Design

This is what computes `audits.compliance_score` and reconciles
`audit_findings` for Unit 15's dashboard.

## Implementation

1. Set `apps/api/agents/prompts/synthesis_agent.md` to the exact
   system prompt from `master-prompts-and-ui-ux-v3.md` §2.1,
   verbatim, including its three operational mandates.
2. Replace the Unit 05 no-op nodes' orchestration with real dispatch:
   `policy_agent` (Unit 06) runs first, then `frontend_agent` (Unit
   08) and `backend_agent` (Unit 07) run in parallel, then the three
   domain-extension agents (Unit 09) run.
3. Reconciliation: for every governance promise in
   `governance_promises` that has a corresponding technical
   observation, compare them. Implement the statutory misrepresentation
   rule explicitly: a "we do not share data without consent" promise
   contradicted by a pre-consent network tracker from `frontend_agent`
   is upgraded to a CRITICAL "Statutory Misrepresentation" finding
   under Section 6(1), distinct from `frontend_agent`'s own raw finding.
4. Implement the documented DPDP Compliance Index formula (0–100%):
   - Domain Weights:
     - Frontend Consent & Tracking: 25%
     - Backend PII Security & Plaintext Logging: 25%
     - Legal Governance & DPA Alignment: 20%
     - Children's Data Protection: 10%
     - Incident Management & 72h SLA: 10%
     - DPR & Grievance Redressal: 10%
   - Scoring deductions per domain (starting from 100):
     - `CRITICAL`: -30 pts
     - `HIGH`: -15 pts
     - `MEDIUM`: -8 pts
     - `LOW`: -3 pts
   - Composite Index = `∑ (Domain Score × Domain Weight)`.
   - **Zero-Tolerance Critical Cap**: If any `CRITICAL` finding is detected
     in any domain, the maximum final Compliance Index is hard-capped at 59% (FAIL).
5. Write the final `compliance_score` to `audits` and set `status = 'COMPLETED'`
   (or `'FAILED'` on unrecoverable error).
6. NFR-3: after synthesis, produce a canonical JSON serialization of
   the full `AuditContextState` and store its SHA-256 hash in `audits.state_hash`
   for tamper-evidence.
7. NFR-1: reject/refuse to finalize an audit if any finding lacks an
   `act_section` or `rules_clause` (Invariant 3).

## Dependencies

- Everything from Units 05–09 must be complete and passing their own
  verification checklists first.

## Verification Checklist

- [ ] A full audit run produces a `compliance_score` between 0 and 100 using the domain-weighted deduction formula
- [ ] Presence of any `CRITICAL` finding correctly forces the composite score to $\le 59\%$ (FAIL)
- [ ] Pre-consent tracker vs. privacy policy contradiction produces a CRITICAL Statutory Misrepresentation finding
- [ ] Every row in `audit_findings` has a verified statutory clause reference
- [ ] SHA-256 state hash is generated and written to `audits.state_hash`
- [ ] Complete 360° audit completes in under 3 minutes against a standard test target (NFR-2)
