# DPDP 360° AI Compliance Auditor

## Overview

An enterprise-grade, open-source compliance engine that verifies
whether an organization's actual digital infrastructure — frontend
tracking behavior, backend application code, and vendor legal
contracts — aligns with its statutory obligations under India's
Digital Personal Data Protection (DPDP) Act, 2023 and the DPDP
Rules, 2025. A multi-agent system (LangGraph + Vertex AI Gemini)
reconciles what an organization's Privacy Policy and DPAs *promise*
against what its website network traffic, consent UI, and source
code *actually do*, and outputs a scored, evidence-backed audit
report with auto-generated remediation patches.

## Goals

1. Detect statutory misrepresentation — cases where a legal
   document's promise (e.g. "we do not share data without consent")
   contradicts observed technical reality (e.g. a tracker fires
   before consent) — and flag it as a CRITICAL finding citing the
   exact Section/Rule.
2. Produce a full 360° audit (legal, frontend, backend, incident
   readiness, child safety, DPR/grievance) for a standard web
   application in under 3 minutes (NFR-2).
3. Generate reviewable, non-breaking auto-remediation code patches
   (Unified Diff format) for backend PII-handling violations.
4. Remain self-compliant with the DPDP Act while auditing third
   parties: ephemeral code handling, PII masking in evidence, 1-year
   log retention, and strict data residency in India (asia-south1 /
   asia-south2).

## Core User Flow

1. User submits a target URL, an optional code repository URL,
   uploaded legal documents (Privacy Policy / DPA PDFs), and selects
   the compliance framework (DPDP Act 2023 / Rules 2025).
2. User starts a 360° audit; `synthesis_agent` creates the audit
   context and dispatches worker agents.
3. `policy_agent` extracts governance promises from the legal
   documents via RAG against the DPDP Act/Rules corpus.
4. `frontend_agent` and `backend_agent` run in parallel against the
   live site and code repo respectively, evaluating actual behavior.
5. `incident_management_agent`, `child_safety_agent`, and
   `dpr_portal_agent` run their domain-specific checks.
6. User watches a real-time telemetry stream (live browser actions +
   terminal/AST agent logs) while the audit runs.
7. `synthesis_agent` reconciles promises vs. reality, computes the
   DPDP Compliance Index (0–100%), and the user lands on the
   Reconciliation Dashboard: a compliance score and a findings table
   with per-row remediation actions (view network trace, apply
   auto-fix PR, generate DB script, download DPA clause).

## Features

### Governance & Legal Auditing
- Itemised-notice and multi-lingual (22 Eighth Schedule languages)
  notice parsing
- DPA extraction: erasure clauses, 1-year log retention terms,
  breach-reporting SLAs
- Statutory RAG comparison against DPDP Act/Rules embeddings

### Live Technical Auditing
- Pre-consent third-party tracker network interception (CDP)
- Consent UI unbundling/pre-checked-box/AXTree verification
- Consent-withdrawal step-parity testing
- Plaintext PII logging detection (AST/Semgrep) across
  Python/JS/TS/Go/Java
- DB schema audit for field encryption and erasure/retention
  triggers
- Auto-generated Unified Diff remediation patches

### Domain Extensions
- Breach playbook and 72-hour DPB notification pipeline audit
- Age-gating / Verifiable Parental Consent (Rule 10) and minor
  ad-tracking exclusion audit
- Data Principal Rights portal SLA (<90 days) and Consent Manager
  interoperability audit

### Reporting
- Real-time dual-pane telemetry stream during execution
- Reconciliation Dashboard with compliance score and actionable
  findings table
- Cryptographically hashed, immutable JSON audit trail per run

## Scope

### In Scope
- Auditing against DPDP Act 2023 and DPDP Rules 2025 only
- Web application frontend behavior, backend source code (static
  analysis only, no execution of untrusted code), and legal document
  text supplied by the user
- Multi-tenant SaaS delivery with organization-scoped data isolation

### Out of Scope
- Any compliance framework other than DPDP (no GDPR/CCPA mapping in
  v1)
- Executing or running the audited organization's code beyond
  AST/static analysis
- Automatically applying remediation patches without human review
  (patches are always PENDING_REVIEW until explicitly approved)
- Mobile app or native SDK auditing (web only in v1)

## Success Criteria

1. A user can submit a URL + repo + legal PDF and receive a
   completed audit with a numeric Compliance Index in under 3
   minutes for a standard web app.
2. Every finding on the dashboard cites a specific DPDP Act Section
   or Rule number and links to supporting evidence (masked/hashed,
   never raw PII).
3. A detected plaintext-PII-logging violation produces a reviewable
   `.patch` file that does not alter unrelated business logic.
4. No cloned source code or raw PII is ever found persisted in
   Supabase after an audit completes.
5. All provisioned GCP/Supabase resources are confirmed to be in
   `asia-south1` or `asia-south2`.
