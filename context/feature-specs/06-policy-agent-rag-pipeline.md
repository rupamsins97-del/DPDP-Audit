# Unit 06 — `policy_agent` RAG Pipeline

## Goal

Implement real legal-document parsing and statutory RAG comparison:
ingest the DPDP Act 2023 / Rules 2025 corpus into `legal_embeddings`,
parse a user's uploaded Privacy Policy/DPA transiently in memory, and
extract governance promises (FR-1.1 – FR-1.4).

## Design

No new UI; feeds the "Terminal & AST Agent Logs" panel (Unit 12/14)
with `[policy_agent]` log lines and populates the
`governance_promises` block of `AuditContextState`.

## Implementation

1. One-time corpus ingestion script: chunk the DPDP Act 2023 and
   DPDP Rules 2025 text, embed each chunk with Vertex AI
   `text-embedding-004` (768-dim), and insert into `legal_embeddings` with
   `statute_reference` populated per chunk (e.g. `'DPDP Act Sec 8(7)'`).
2. Set `apps/api/agents/prompts/policy_agent.md` to the exact system
   prompt from `master-prompts-and-ui-ux-v3.md` §2.2, verbatim.
3. Implement transient in-memory upload parsing for Privacy Policy / DPA
   documents (`pypdf` / `pymupdf`): extract text in memory, chunk and
   generate vector embeddings in `legal_embeddings` (linked to `audit_id`),
   and immediately discard the raw binary PDF file (Invariant 2 & Invariant 4).
   Raw PDF files are never persisted to Supabase blob storage.
4. FR-1.1: extract itemised personal-data categories, processing
   purposes, DPO contact.
5. FR-1.2: verify multi-lingual notice availability across the 22
   Eighth Schedule languages (presence/absence check in v1).
6. FR-1.3: extract DPA clauses — erasure requirements, 1-year log
   retention (Rule 6(1)(e)/Rule 8(3)), breach-reporting SLA.
7. FR-1.4: for each extracted claim, run a `pgvector` cosine
   similarity query against `legal_embeddings` and attach the closest
   statutory clause as `act_section`/`rules_clause` before any
   finding is written (Invariant 3 — no ungrounded findings).
8. Write extracted promises into `AuditContextState.governance_promises`
   and emit `GOVERNANCE_RULES_READY` with the real payload.

## Dependencies

- Vertex AI SDK (`google-cloud-aiplatform` / `text-embedding-004` + `gemini-1.5-pro-002` in `asia-south1`).
- PDF text-extraction library (`pypdf` / `pymupdf`).
- `pgvector` client query support in Supabase.

## Verification Checklist

- [ ] The DPDP Act/Rules corpus is fully ingested into `legal_embeddings` with correct `statute_reference` values
- [ ] Sample Privacy Policy upload produces itemised categories, DPO contact, and language-availability findings
- [ ] Sample DPA upload produces erasure/retention/breach-SLA extractions
- [ ] Every extracted claim written to `audit_findings` carries a real `act_section` or `rules_clause`, never null
- [ ] Raw uploaded PDF bytes are purged immediately and never found in any storage bucket or database table
- [ ] `GOVERNANCE_RULES_READY` event emits the structured `governance_promises` payload to the event bus
