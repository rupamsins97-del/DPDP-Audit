# System Architecture & Tech Stack v3
## DPDP 360° AI Compliance Auditor

### 1. High-Level System Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │                    User Interface                      │
                               │        (Next.js 15 App Router + Tailwind CSS)          │
                               │             Hosted on Vercel / Netlify                 │
                               └───────────────────────────┬────────────────────────────┘
                                                           │ (REST / SSE Telemetry)
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │               API Gateway & Orchestrator               │
                               │    (FastAPI + Python 3.12 on GCP Cloud Run - Mumbai)   │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │            LangGraph Agent State Machine               │
                               │          (Vertex AI Gemini 3.5 Flash / 3.1 Pro)        │
                               └───────┬───────────────┬───────────────┬────────────────┘
                                       │               │               │
            ┌──────────────────────────┘               │               └──────────────────────────┐
            ▼                                          ▼                                          ▼
┌───────────────────────┐                  ┌───────────────────────┐                  ┌───────────────────────┐
│     policy_agent      │                  │    frontend_agent     │                  │    backend_agent      │
│(Vertex RAG + pgvector)│                  │(Stagehand CDP+Scrapfl)│                  │(Tree-sitter / Semgrep)│
└───────────┬───────────┘                  └───────────┬───────────┘                  └───────────┬───────────┘
            │                                          │                                          │
            ▼                                          ▼                                          ▼
┌───────────────────────┐                  ┌───────────────────────┐                  ┌───────────────────────┐
│ legal_docs / DPA PDFs │                  │ Live Web Browser / CDP│                  │ Application Codebase  │
└───────────────────────┘                  └───────────────────────┘                  └───────────────────────┘
                                                           │
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │                   Shared Event Bus                     │
                               │             (GCloud Pub/Sub / Redis Bus)               │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │                    Storage Layer                       │
                               │       (Supabase PostgreSQL 16 + pgvector + RLS)        │
                               │            Hosted in Mumbai (asia-south1)              │
                               └────────────────────────────────────────────────────────┘
```

---

### 2. Comprehensive Tech Stack Specification

| Component Layer | Technology Selected | Justification & Role |
| :--- | :--- | :--- |
| **LLM & Reasoning Engine** | **Google Cloud Vertex AI (Gemini 3.5 Flash & Gemini 3.1 Pro)** | Gemini 3.5 Flash drives agentic navigation and AST code fixes; Gemini 3.1 Pro executes deep legal RAG reasoning. Native 1M+ context window. |
| **Embeddings Model** | **`text-embedding-004` (Vertex AI)** | High-speed, 768/1536-dim vector generation for legal statutory chunk indexing. |
| **Frontend UI** | **Next.js 15 (React 19, Tailwind CSS)** | Modern server components, dual-pane telemetry stream, deployed on Vercel/Netlify. |
| **Backend Gateway** | **FastAPI (Python 3.12)** | Asynchronous execution, native Pydantic validation, deployed on Google Cloud Run (`asia-south1`). |
| **Agent Framework** | **LangGraph (Python)** | State-machine based DAG orchestration allowing parallel execution, looping, state persistence, and inter-agent communication. |
| **Browser Agent Engine** | **Stagehand + Scrapfly Unblocker** | Hybrid AI-driven web navigation with accessibility tree trimming (AXTree), CDP network interception, and Cloudflare/DataDome anti-bot bypass. |
| **Static Analysis Engine** | **Semgrep + Tree-sitter** | High-speed AST construction, taint tracking, and deterministic SAST rule evaluation with strict `.semgrepignore` memory bounds (<2GB). |
| **Database & Vector Store** | **Supabase PostgreSQL 16 (`pgvector`)** | Combined relational database and vector store with Row-Level Security (RLS) and `pg_cron` automated 1-year log retention. |
| **Build & Deployment IDE** | **Google Antigravity Agentic IDE + MCPs** | Build-time environment connecting Supabase MCP, Netlify/Vercel MCP, and Cloud Run MCP to autonomously assemble and deploy the application. |

---

### 3. Agentic Architecture & Orchestration Model

The system employs a **Leader-Worker DAG Orchestration Pattern**:

1. **`synthesis_agent` (Leader/Orchestrator)**:
   * Initializes the audit execution context.
   * Dispatches parallel tasks to specialized worker agents based on user input (URL, code repo, legal files).
   * Aggregates worker outputs, resolves conflicting findings, and computes the composite DPDP Compliance Index (0–100%).
2. **Specialized Worker Agents (Parallel Execution)**:
   * **`policy_agent`**: Evaluates legal compliance vectors using Vertex AI RAG.
   * **`frontend_agent`**: Controls headless browser via Stagehand CDP and evaluates UI/network vectors.
   * **`backend_agent`**: Evaluates codebase and database schemas via Tree-sitter & Semgrep AST analysis.
   * **`incident_management_agent`**: Evaluates breach readiness and 72-hour notification pipelines.
   * **`child_safety_agent`**: Evaluates minor protection & age-gating.
   * **`dpr_portal_agent`**: Evaluates Data Principal Rights workflows and SLA timers.

---

### 4. Build-Time MCP Agentic IDE vs Autonomous Runtime Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      BUILD-TIME ENVIRONMENT (Antigravity IDE)                    │
│                                                                                  │
│  Developer Prompts Antigravity IDE -> IDE invokes Connected MCP Servers:          │
│  ├─► Supabase MCP: Executes schema migrations (`schema.sql`) & RLS policies      │
│  ├─► Cloud Run MCP: Containerizes FastAPI app & deploys to GCP (`asia-south1`)   │
│  └─► Vercel / Netlify MCP: Builds & deploys Next.js 15 UI frontend               │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼ (Deploys Production Artifacts)
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     AUTONOMOUS PRODUCTION RUNTIME (100% Cloud)                   │
│                                                                                  │
│  Next.js 15 Frontend (Vercel) ──REST/SSE──► FastAPI Backend (GCP Cloud Run)      │
│                                                   │                              │
│                                                   ▼                              │
│                                       LangGraph Orchestrator                     │
│                                 (Vertex AI Gemini 3.5 Flash)                     │
│                                                   │                              │
│                                                   ▼                              │
│                                    Supabase PostgreSQL (`pgvector`)              │
│                                                                                  │
│  *Runs completely standalone 24/7 without requiring Antigravity IDE or local PC. │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

### 5. Production Database Schema (Supabase PostgreSQL 16)

```sql
-- Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- 1. Audits Table
CREATE TABLE audits (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL, -- For multi-tenant RLS
    project_name VARCHAR(255) NOT NULL,
    target_url VARCHAR(512),
    status VARCHAR(50) DEFAULT 'IN_PROGRESS', -- IN_PROGRESS, COMPLETED, FAILED
    compliance_score NUMERIC(5,2), -- Overall score 0.00 - 100.00
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable Row Level Security (RLS)
ALTER TABLE audits ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Org Isolation Policy for Audits" ON audits
    FOR ALL USING (auth.uid() = organization_id);

-- 2. Audit Findings / Violations Table
CREATE TABLE audit_findings (
    finding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID REFERENCES audits(audit_id) ON DELETE CASCADE,
    agent_role VARCHAR(50) NOT NULL, -- policy_agent, frontend_agent, backend_agent, etc.
    act_section VARCHAR(100) NOT NULL, -- e.g., 'Section 8(5)', 'Section 6(1)'
    rules_clause VARCHAR(100), -- e.g., 'Rule 6(1)(a)'
    severity VARCHAR(20) NOT NULL, -- CRITICAL, HIGH, MEDIUM, LOW
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    evidence_snippet TEXT, -- Masked PII / Network Log / Code Snippet
    remediation_suggestion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE audit_findings ENABLE ROW LEVEL SECURITY;

-- 3. Code Patches Table (Generated by backend_agent)
CREATE TABLE code_patches (
    patch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id UUID REFERENCES audit_findings(finding_id) ON DELETE CASCADE,
    file_path VARCHAR(512) NOT NULL,
    original_code TEXT NOT NULL,
    patched_code TEXT NOT NULL,
    diff_content TEXT NOT NULL, -- Unified diff format (.patch)
    status VARCHAR(50) DEFAULT 'PENDING_REVIEW', -- PENDING_REVIEW, APPLIED, REJECTED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Legal Document Embeddings (for RAG in policy_agent)
CREATE TABLE legal_embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_name VARCHAR(255) NOT NULL,
    statute_reference VARCHAR(100) NOT NULL, -- e.g. 'DPDP Act Sec 8(7)', 'DPDP Rule 6'
    chunk_text TEXT NOT NULL,
    embedding vector(768), -- Vertex AI text-embedding-004 vector
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexing for performance
CREATE INDEX idx_findings_audit_id ON audit_findings(audit_id);
CREATE INDEX idx_findings_severity ON audit_findings(severity);
CREATE INDEX idx_legal_embeddings_vec ON legal_embeddings USING ivfflat (embedding vector_cosine_ops);

-- 5. Automated 1-Year Log Retention Cleanup Job (Rule 6(1)(e) & Rule 8(3))
SELECT cron.schedule(
    'purge-old-audit-logs',
    '0 0 * * *', -- Daily at midnight
    $$ DELETE FROM audits WHERE created_at < NOW() - INTERVAL '365 days'; $$
);
```
