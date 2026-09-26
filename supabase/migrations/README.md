# Supabase Migrations

This directory contains SQL migrations, RLS policies, `pg_cron` jobs, and `legal_embeddings` seed scripts for the DPDP 360° AI Compliance Auditor.

## Rules & Invariants
- SQL migrations in this folder are **append-only** once applied.
- RLS policies are never rewritten in place. Any access rule updates must ship as a new migration.
- All persistent relational data (`audits`, `audit_findings`, `code_patches`, `legal_embeddings`) resides in Supabase PostgreSQL in `asia-south1`.
- Ephemeral data (cloned repos, live browser traces) is never stored here.
