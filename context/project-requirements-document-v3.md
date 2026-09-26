# Project Requirements Document (PRD) v3
## DPDP 360° AI Compliance Auditor

### 1. Executive Summary & Vision
The **DPDP 360° AI Compliance Auditor** is an enterprise-grade, open-source compliance engine designed to verify whether an organization's actual digital infrastructure, data pipelines, frontend tracking practices, and vendor contracts align strictly with their statutory obligations under India's **Digital Personal Data Protection (DPDP) Act, 2023** and the **DPDP Rules, 2025**.

Utilizing a multi-agent orchestration pattern powered by **Google Cloud Vertex AI (Gemini 3.5 Flash & 3.1 Pro)**, **Stagehand CDP Browser Automation**, **Semgrep AST Static Analysis**, and **Supabase PostgreSQL**, the system bridges the gap between legal policy promises (Data Processing Agreements, Privacy Notices) and technical reality (frontend JavaScript tags, backend application code, database retention policies).

---

### 2. Legal & Regulatory Mapping Matrix

| Act / Rule Provision | Statutory Mandate | Auditing Agent Role | Technical Verification Target |
| :--- | :--- | :--- | :--- |
| **Section 5(1), 5(2) & Rule 3** | Itemised Notice in 22 Eighth Schedule languages | `policy_agent` & `frontend_agent` | Legal document parsing, multi-lingual notice UI DOM elements |
| **Section 6(1) & Rule 3(c)** | Unambiguous, affirmative, and unbundled consent | `frontend_agent` | Network traffic analysis (pre-consent pixel firing), DOM checkbox state |
| **Section 6(5) & Rule 3(c)(i)** | Withdrawal of consent as easy as giving consent | `frontend_agent` | Web form navigation & workflow path complexity comparison |
| **Section 8(2) & Rule 6(1)** | Valid Data Processing Agreement (DPA) with processors | `policy_agent` | Extraction of mandatory DPA fields (erasure clauses, 1-yr log retention) |
| **Section 8(5) & Rule 6(1)(a)** | Reasonable security safeguards to prevent breach | `backend_agent` | Codebase scan for plain-text PII logging & unencrypted DB fields |
| **Section 8(6) & Rule 7** | Immediate breach notification to Board & Principals | `incident_management_agent` | SIEM alert playbooks & 72-hour automated notification pipelines |
| **Section 8(7) & Section 8(8)** | Storage limitation & mandatory data erasure | `backend_agent` | DB retention cron jobs, `ON DELETE CASCADE` triggers, soft deletes |
| **Section 9 & Rule 10** | Verifiable parental consent & child tracking prohibition | `child_safety_agent` | Age-gating UI, DigiLocker integration, ad-tech pipeline filtering |
| **Sections 11–14 & Rule 14** | Data Principal Rights (DPR) & Grievance Redressal | `dpr_portal_agent` | Self-service portal SLA timers (<90 days response), nomination flows |
| **Section 16 & Rule 13** | Cross-Border Data Transfer & Data Sovereignty | `policy_agent` & `backend_agent` | Regional hosting verification (`asia-south1`), restricted country transfer checks |

---

### 3. Detailed Functional Requirements

#### 3.1 Legal & Governance Vector (`policy_agent`)
* **FR-1.1 (Notice Parsing):** Extract itemised personal data categories, processing purposes, and DPO contact details from Privacy Policies.
* **FR-1.2 (Multi-lingual Audit):** Verify availability and equivalence of notices across English and all 22 Eighth Schedule languages listed in the Constitution of India.
* **FR-1.3 (DPA Extraction):** Extract vendor binding clauses, cascading deletion requirements, mandatory 1-year log retention obligations (Rule 6(1)(e) & Rule 8(3)), and breach reporting SLAs from uploaded contracts.
* **FR-1.4 (Statutory RAG Comparison):** Compare extracted contractual terms against `legal_embeddings` chunked from the DPDP Act 2023 and DPDP Rules 2025 using Vertex AI `text-embedding-004` and Supabase `pgvector` cosine similarity.

#### 3.2 Frontend Web Behavior Vector (`frontend_agent`)
* **FR-2.1 (Pre-Consent Network Interception):** Intercept Chrome DevTools Protocol (CDP) network requests during initial page load to ensure third-party trackers (Meta Pixel, Google Analytics, ByteDance) do not execute before affirmative consent.
* **FR-2.2 (DOM Consent Form Verification):** Verify via Accessibility Tree (AXTree) Trimming that consent options are unbundled, contain no pre-checked boxes, and present explicit opt-in toggles.
* **FR-2.3 (Consent Withdrawal Parity):** Measure user clicks/steps required to withdraw consent versus giving consent, enforcing parity per Rule 3(c)(i).
* **FR-2.4 (Anti-Bot Bypass Routing):** Route headless browser CDP sessions through Scrapfly Unblocker / Browserbase proxies when auditing enterprise websites protected by Cloudflare, DataDome, or Akamai.

#### 3.3 Backend Infrastructure & Code Vector (`backend_agent`)
* **FR-3.1 (PII Static Analysis):** Construct ASTs via Tree-sitter and execute Semgrep SAST rules to identify plain-text PII logging (Aadhaar, PAN, Phone, Email, Financial Data) in application logs across Python, JS/TS, Go, and Java.
* **FR-3.2 (Targeted Code Base Scanning):** Target application route handlers, ORM models, and logging functions with strict `.semgrepignore` rules to maintain container memory below 2GB.
* **FR-3.3 (Database Schema Audit):** Verify field-level encryption on PII database columns and check for mandatory `created_at`/`updated_at`/`deleted_at` timestamps.
* **FR-3.4 (Erasure Mechanics Audit):** Audit scheduled background tasks (`cron`) and database triggers to confirm automated data purging upon consent withdrawal or account deletion.
* **FR-3.5 (Automated Code Remediation):** Generate reviewable Git diff patches (Unified Format `.patch`) using Gemini 3.5 Flash to fix detected non-compliance issues in codebases.

#### 3.4 Incident & Breach Management Vector (`incident_management_agent`)
* **FR-4.1 (Breach Playbook Verification):** Audit incident response workflows to ensure compliance with Rule 7 breach notification templates.
* **FR-4.2 (72-Hour DPB Pipeline):** Verify automated alert integrations capable of notifying the Data Protection Board within 72 hours of incident confirmation.

#### 3.5 Child Safety Vector (`child_safety_agent`)
* **FR-5.1 (Verifiable Parental Consent - VPC):** Audit age-gating mechanisms and integration with approved identity verification tokens under Rule 10 (DigiLocker / virtual tokens).
* **FR-5.2 (Behavioral Profiling Exclusion):** Scan ad-tech and analytics scripts to ensure users identified as minors (<18 years) are completely excluded from targeted advertising or behavioral tracking.

#### 3.6 Data Principal Rights & Consent Manager Vector (`dpr_portal_agent`)
* **FR-6.1 (DPR SLA Tracking):** Audit grievance portal database models to enforce a maximum 90-day resolution timer (Rule 14(3)).
* **FR-6.2 (Consent Manager Interoperability):** Audit API hooks for integration with registered Consent Managers under Section 6(7)–(9) and Rule 4.

---

### 4. Application Self-Compliance Requirements (DPDP Security for the Auditor)

Since the Auditor App processes third-party code and privacy documents, it must strictly comply with the DPDP Act itself:
* **SR-1 (Data Residency - Section 16):** All GCP services (Cloud Run, Vertex AI) and Supabase database instances must be provisioned strictly in the `asia-south1` (Mumbai) or `asia-south2` (Delhi) region.
* **SR-2 (Ephemeral Code Processing - Section 8(7)):** Cloned user source code repositories are held in memory/tmpfs and **immediately deleted (`shutil.rmtree`)** after AST parsing. Source code is never persisted to databases.
* **SR-3 (PII Masking - Section 8(5)):** All PII snippets detected in evidence logs must be hashed (SHA-256) or masked (`Aadhaar: XXXX-XXXX-1234`) before saving to Supabase.
* **SR-4 (1-Year Security Log Retention - Rule 6(1)(e) & Rule 8(3)):** Audit execution logs and system access metadata are retained in Supabase for exactly 365 days using `pg_cron` automated retention triggers, then purged.
* **SR-5 (Multi-Tenant RLS Isolation):** PostgreSQL Row Level Security (RLS) policies enforce organization-level data isolation across all audit tables.

---

### 5. Non-Functional Requirements (NFRs)

* **NFR-1 (Zero Hallucination Grounding):** Statutory findings must be tied directly to explicit legal clauses and static analysis AST rules; LLMs must operate under strict JSON schemas and anti-hallucination guardrails.
* **NFR-2 (Execution Latency):** Full 360° compliance audit across web, legal, and backend must complete in under 3 minutes for standard web applications.
* **NFR-3 (Audit Trail & Reproducibility):** Every audit report must yield a cryptographically hashed, immutable JSON execution log for legal defense.
* **NFR-4 (Cost Optimization):** System operates within GCP $300 credit and Always Free Tier allowances across Cloud Run, Vertex AI, and Supabase.
