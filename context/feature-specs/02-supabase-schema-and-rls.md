# Unit 02 — Supabase Schema & RLS

## Goal

Create the full production database schema — `organizations`,
`organization_members`, `audits`, `audit_findings`, `code_patches`,
`legal_embeddings` — with `pgvector`/`pg_cron` enabled, RLS applied,
user-org bootstrap trigger configured, and the 365-day retention job
scheduled.

## Design

No UI. This is the Storage Model section of `architecture.md` made
real.

## Implementation

1. New migration `supabase/migrations/0001_init.sql`:
   - `CREATE EXTENSION IF NOT EXISTS vector;`
   - `CREATE EXTENSION IF NOT EXISTS pg_cron;`
2. Create `organizations` (`id UUID PRIMARY KEY DEFAULT gen_random_uuid()`,
   `name TEXT NOT NULL`, `created_at TIMESTAMPTZ DEFAULT now()`).
3. Create `organization_members` (`organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE`,
   `user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE`,
   `role TEXT NOT NULL DEFAULT 'ADMIN'`, `created_at TIMESTAMPTZ DEFAULT now()`,
   `PRIMARY KEY (organization_id, user_id)`).
4. Create `audits` (`audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid()`,
   `organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE`,
   `project_name TEXT NOT NULL`, `target_url TEXT NOT NULL`,
   `repository_url TEXT`, `status TEXT NOT NULL DEFAULT 'QUEUED'`,
   `compliance_score INTEGER`, `state_hash TEXT`,
   `created_at TIMESTAMPTZ DEFAULT now()`, `updated_at TIMESTAMPTZ DEFAULT now()`).
5. Create `audit_findings` (`finding_id UUID PRIMARY KEY DEFAULT gen_random_uuid()`,
   `audit_id UUID REFERENCES audits(audit_id) ON DELETE CASCADE`,
   `agent_role TEXT NOT NULL`, `act_section TEXT NOT NULL`,
   `rules_clause TEXT NOT NULL`, `severity TEXT NOT NULL`, `title TEXT NOT NULL`,
   `description TEXT NOT NULL`, `evidence_snippet TEXT NOT NULL`,
   `remediation_suggestion TEXT NOT NULL`, `created_at TIMESTAMPTZ DEFAULT now()`).
6. Create `code_patches` (`patch_id UUID PRIMARY KEY DEFAULT gen_random_uuid()`,
   `finding_id UUID REFERENCES audit_findings(finding_id) ON DELETE CASCADE`,
   `file_path TEXT NOT NULL`, `original_code TEXT NOT NULL`,
   `patched_code TEXT NOT NULL`, `diff_content TEXT NOT NULL`,
   `status TEXT NOT NULL DEFAULT 'PENDING_REVIEW'`,
   `created_at TIMESTAMPTZ DEFAULT now()`).
7. Create `legal_embeddings` (`embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid()`,
   `organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE`,
   `audit_id UUID REFERENCES audits(audit_id) ON DELETE CASCADE`,
   `document_name TEXT NOT NULL`, `statute_reference TEXT NOT NULL`,
   `chunk_text TEXT NOT NULL`, `embedding vector(768)`,
   `metadata JSONB DEFAULT '{}'::jsonb`, `created_at TIMESTAMPTZ DEFAULT now()`)
   with an `ivfflat` cosine index.
8. Enable RLS on all tenant tables (`organizations`, `organization_members`,
   `audits`, `audit_findings`, `code_patches`, `legal_embeddings`).
   Apply the organization-isolation membership policy:
   `organization_id IN (SELECT organization_id FROM organization_members WHERE user_id = auth.uid())`.
9. Create PostgreSQL trigger on `auth.users` (`on_auth_user_created`) to
   automatically insert a default organization and assign the new user as `ADMIN`.
10. Schedule the `purge-old-audit-logs` `pg_cron` job (daily at midnight,
    365-day cutoff on `audits.created_at`).
11. Add performance indexes: `idx_findings_audit_id`, `idx_findings_severity`,
    `idx_audits_org_id`, `idx_patches_finding_id`, `idx_legal_embeddings_vec`.

## Dependencies

- Supabase project provisioned in `asia-south1` (SR-1).
- Supabase CLI or Supabase MCP for applying migrations.

## Verification Checklist

- [ ] All tables exist with the exact columns, primary keys, and foreign keys
- [ ] `pgvector` and `pg_cron` extensions are enabled
- [ ] RLS is enabled on all tables, and cross-organization queries return zero rows for non-members
- [ ] User bootstrap trigger creates an organization upon `auth.users` insert
- [ ] Retention `pg_cron` job is scheduled and active
- [ ] Supabase project region is verified `asia-south1` (or `asia-south2`)
- [ ] `code_patches.status` defaults to `PENDING_REVIEW`
