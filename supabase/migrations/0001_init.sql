-- ==============================================================================
-- DPDP 360° AI Compliance Auditor — Initial Production Migration (0001_init.sql)
-- Stack: Supabase PostgreSQL 16 + pgvector + pg_cron + RLS
-- Region: asia-south1 / asia-south2 (Mandatory Data Residency SR-1)
-- ==============================================================================

-- 1. Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- 2. Organizations Table (Multi-Tenancy)
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Organization Members Table
CREATE TABLE IF NOT EXISTS public.organization_members (
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'ADMIN' CHECK (role IN ('ADMIN', 'MEMBER', 'VIEWER')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (organization_id, user_id)
);

-- 4. Audits Table
CREATE TABLE IF NOT EXISTS public.audits (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    project_name TEXT NOT NULL,
    target_url TEXT NOT NULL,
    repository_url TEXT,
    status TEXT NOT NULL DEFAULT 'QUEUED' CHECK (status IN ('QUEUED', 'IN_PROGRESS', 'COMPLETED', 'FAILED')),
    compliance_score INTEGER CHECK (compliance_score IS NULL OR (compliance_score >= 0 AND compliance_score <= 100)),
    state_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. Audit Findings Table
CREATE TABLE IF NOT EXISTS public.audit_findings (
    finding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL REFERENCES public.audits(audit_id) ON DELETE CASCADE,
    agent_role TEXT NOT NULL,
    act_section TEXT NOT NULL,
    rules_clause TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    evidence_snippet TEXT NOT NULL,
    remediation_suggestion TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 6. Code Patches Table
CREATE TABLE IF NOT EXISTS public.code_patches (
    patch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id UUID NOT NULL REFERENCES public.audit_findings(finding_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    original_code TEXT NOT NULL,
    patched_code TEXT NOT NULL,
    diff_content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING_REVIEW' CHECK (status IN ('PENDING_REVIEW', 'APPLIED', 'REJECTED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 7. Legal Embeddings Table (Vector store for DPDP Act/Rules and transient documents)
CREATE TABLE IF NOT EXISTS public.legal_embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
    audit_id UUID REFERENCES public.audits(audit_id) ON DELETE CASCADE,
    document_name TEXT NOT NULL,
    statute_reference TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 8. Performance & Search Indexes
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON public.organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_audits_org_id ON public.audits(organization_id);
CREATE INDEX IF NOT EXISTS idx_audits_status ON public.audits(status);
CREATE INDEX IF NOT EXISTS idx_audits_created_at ON public.audits(created_at);
CREATE INDEX IF NOT EXISTS idx_findings_audit_id ON public.audit_findings(audit_id);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON public.audit_findings(severity);
CREATE INDEX IF NOT EXISTS idx_findings_agent_role ON public.audit_findings(agent_role);
CREATE INDEX IF NOT EXISTS idx_patches_finding_id ON public.code_patches(finding_id);
CREATE INDEX IF NOT EXISTS idx_patches_status ON public.code_patches(status);
CREATE INDEX IF NOT EXISTS idx_legal_embeddings_statute ON public.legal_embeddings(statute_reference);
CREATE INDEX IF NOT EXISTS idx_legal_embeddings_org ON public.legal_embeddings(organization_id);
CREATE INDEX IF NOT EXISTS idx_legal_embeddings_audit ON public.legal_embeddings(audit_id);

-- HNSW Vector Index for 768-dim embeddings (Vertex AI text-embedding-004)
CREATE INDEX IF NOT EXISTS idx_legal_embeddings_vec ON public.legal_embeddings USING hnsw (embedding vector_cosine_ops);

-- 9. Updated At Trigger Function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at Triggers
DROP TRIGGER IF EXISTS tr_organizations_updated_at ON public.organizations;
CREATE TRIGGER tr_organizations_updated_at
    BEFORE UPDATE ON public.organizations
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS tr_audits_updated_at ON public.audits;
CREATE TRIGGER tr_audits_updated_at
    BEFORE UPDATE ON public.audits
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS tr_code_patches_updated_at ON public.code_patches;
CREATE TRIGGER tr_code_patches_updated_at
    BEFORE UPDATE ON public.code_patches
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 10. User Auto-Provisioning Trigger on auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    new_org_id UUID;
    org_name TEXT;
BEGIN
    org_name := COALESCE(
        NEW.raw_user_meta_data->>'organization_name',
        split_part(NEW.email, '@', 1) || '''s Organization'
    );

    INSERT INTO public.organizations (name)
    VALUES (org_name)
    RETURNING id INTO new_org_id;

    INSERT INTO public.organization_members (organization_id, user_id, role)
    VALUES (new_org_id, NEW.id, 'ADMIN');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 11. Row Level Security (RLS) Policies
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.code_patches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.legal_embeddings ENABLE ROW LEVEL SECURITY;

-- Organizations RLS
CREATE POLICY "Users can view member organizations"
    ON public.organizations FOR SELECT
    TO authenticated
    USING (
        id IN (SELECT organization_id FROM public.organization_members WHERE user_id = auth.uid())
    );

CREATE POLICY "Admins can update their organization"
    ON public.organizations FOR UPDATE
    TO authenticated
    USING (
        id IN (SELECT organization_id FROM public.organization_members WHERE user_id = auth.uid() AND role = 'ADMIN')
    );

-- Organization Members RLS
CREATE POLICY "Users can view members of their organizations"
    ON public.organization_members FOR SELECT
    TO authenticated
    USING (
        organization_id IN (SELECT om.organization_id FROM public.organization_members om WHERE om.user_id = auth.uid())
    );

CREATE POLICY "Admins can manage organization members"
    ON public.organization_members FOR ALL
    TO authenticated
    USING (
        organization_id IN (SELECT om.organization_id FROM public.organization_members om WHERE om.user_id = auth.uid() AND om.role = 'ADMIN')
    );

-- Audits RLS
CREATE POLICY "Organization members can access audits"
    ON public.audits FOR ALL
    TO authenticated
    USING (
        organization_id IN (SELECT organization_id FROM public.organization_members WHERE user_id = auth.uid())
    );

-- Audit Findings RLS
CREATE POLICY "Organization members can access findings"
    ON public.audit_findings FOR ALL
    TO authenticated
    USING (
        audit_id IN (
            SELECT a.audit_id FROM public.audits a
            JOIN public.organization_members om ON om.organization_id = a.organization_id
            WHERE om.user_id = auth.uid()
        )
    );

-- Code Patches RLS
CREATE POLICY "Organization members can access code patches"
    ON public.code_patches FOR ALL
    TO authenticated
    USING (
        finding_id IN (
            SELECT f.finding_id FROM public.audit_findings f
            JOIN public.audits a ON a.audit_id = f.audit_id
            JOIN public.organization_members om ON om.organization_id = a.organization_id
            WHERE om.user_id = auth.uid()
        )
    );

-- Legal Embeddings RLS (Global statutory corpus is readable by all authenticated users; org uploads restricted to org members)
CREATE POLICY "Access legal embeddings"
    ON public.legal_embeddings FOR SELECT
    TO authenticated
    USING (
        organization_id IS NULL OR
        organization_id IN (SELECT organization_id FROM public.organization_members WHERE user_id = auth.uid())
    );

CREATE POLICY "Insert org legal embeddings"
    ON public.legal_embeddings FOR INSERT
    TO authenticated
    WITH CHECK (
        organization_id IN (SELECT organization_id FROM public.organization_members WHERE user_id = auth.uid())
    );

-- 12. 365-Day Data Retention Job (SR-4 / pg_cron)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        -- Remove existing job if already scheduled
        PERFORM cron.unschedule('purge-old-audit-logs')
        WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'purge-old-audit-logs');

        -- Schedule daily purge at midnight
        PERFORM cron.schedule(
            'purge-old-audit-logs',
            '0 0 * * *',
            $cmd$
                DELETE FROM public.audits
                WHERE created_at < now() - INTERVAL '365 days';
            $cmd$
        );
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pg_cron job scheduling skipped or deferred: %', SQLERRM;
END
$$;
