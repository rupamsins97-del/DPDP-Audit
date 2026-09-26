-- ==============================================================================
-- DPDP 360° AI Compliance Auditor — Migration 0002 (0002_legal_embeddings_policy.sql)
-- Add explicit policy for global statutory RAG corpus (organization_id IS NULL)
-- ==============================================================================

-- 1. Allow reading global statutory corpus by all roles (anon and authenticated)
CREATE POLICY "Public read global legal embeddings"
    ON public.legal_embeddings FOR SELECT
    TO anon, authenticated
    USING (organization_id IS NULL);

-- 2. Allow ingestion of global statutory corpus where organization_id IS NULL
CREATE POLICY "Insert global legal embeddings"
    ON public.legal_embeddings FOR INSERT
    TO anon, authenticated
    WITH CHECK (organization_id IS NULL);
