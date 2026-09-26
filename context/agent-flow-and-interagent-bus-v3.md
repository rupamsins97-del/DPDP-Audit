# Agent Flow & Inter-Agent Execution Protocol v3
## DPDP 360° AI Compliance Auditor

### 1. Step-by-Step Execution Lifecycle

```
[Phase 1: Ingestion & Task Decomposition]
  User submits URL, Code Repo, Privacy Policy PDF
  └─► synthesis_agent creates Audit Context & dispatches worker tasks

[Phase 2: Governance Extraction (policy_agent)]
  policy_agent parses Privacy Policy & Vendor DPAs via Vertex AI RAG
  ├─► Queries legal_embeddings (DPDP Act & Rules) in Supabase pgvector
  ├─► Extracts declared retention rules, processing purposes, DPO contacts
  └─► Emits Event: GOVERNANCE_RULES_READY to Shared Event Bus

[Phase 3: Parallel Execution (frontend_agent & backend_agent)]
  ├── frontend_agent reads GOVERNANCE_RULES_READY
  │     ├─► Launches Stagehand (Chromium via CDP)
  │     ├─► Attaches Scrapfly Unblocker proxy if anti-bot protection detected
  │     ├─► Intercepts network tracking requests, verifies pre-consent pixels
  │     └─► Audits DOM consent banners, language toggles, withdrawal flows
  │
  └── backend_agent reads GOVERNANCE_RULES_READY
        ├─► Clones codebase into ephemeral tmpfs sandbox
        ├─► Runs Tree-sitter & Semgrep SAST scans targeting API routes & loggers
        ├─► Identifies unencrypted PII logs & non-compliant retention timers
        ├─► Generates auto-remediation Git patches (Unified Diffs) via Gemini 3.5 Flash
        └─► Purges temporary codebase directory (shutil.rmtree)

[Phase 4: Domain Extensions Audit]
  ├── incident_management_agent: Audits breach response playbooks & 72h pipelines
  ├── child_safety_agent: Audits age-gating & minor tracking exclusion
  └── dpr_portal_agent: Audits grievance SLA timers (<90 days) & nomination flows

[Phase 5: Synthesis & Reconciliation]
  synthesis_agent aggregates findings from all agents
  ├─► Reconciles promises (policy) vs realities (web/code)
  ├─► Generates Compliance Scorecard & Unified Executive Audit Report
  └─► Streams results to UI Dashboard via WebSockets / Server-Sent Events
```

---

### 2. Inter-Agent Event Bus & Shared Memory Protocol

Agents communicate asynchronously via a shared event bus (`GCloud Pub/Sub` / `Redis`) and an immutable event log (`AuditContextState` in LangGraph).

#### State Schema (`AuditContextState`)
```json
{
  "audit_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "organization_id": "e8f7a6b5-1234-5678-90ab-cdef12345678",
  "status": "RUNNING",
  "governance_promises": {
    "data_retention_days": 365,
    "declared_trackers": ["Google Analytics", "Meta Pixel"],
    "dpo_email": "privacy@company.com",
    "supported_languages": ["en", "hi", "bn", "ta"]
  },
  "findings": {
    "policy": [],
    "frontend": [],
    "backend": [],
    "incident": [],
    "child_safety": [],
    "dpr_portal": []
  },
  "generated_patches": []
}
```

---

### 3. Deep-Dive: `frontend_agent` Web Navigation & Anti-Bot Bypass Protocol

The `frontend_agent` utilizes **Stagehand** on top of Playwright and Chrome DevTools Protocol (CDP) to interact with dynamic web pages:

1. **Anti-Bot Protection Detection & Bypass Routing**:
   * Inspects response headers (`CF-RAY`, `Server: DataDome`, `X-Akamai`).
   * If anti-bot protection is detected, Stagehand connects its CDP driver through **Scrapfly Unblocker** or **Browserbase Stealth Proxies**, solving JavaScript challenges and spoofing TLS/JA3 fingerprints seamlessly.
2. **Network Stream Interception (Pre-Consent Check)**:
   ```typescript
   // Stagehand CDP network hook before user clicks consent
   page.on('request', request => {
     const url = request.url();
     if (isTrackerDomain(url) && !userHasConsented) {
       findings.push({
         rule: 'Section 6(1)',
         severity: 'CRITICAL',
         title: 'Pre-Consent Data Transmission',
         description: `Tracking request sent to ${url} before user gave affirmative consent.`
       });
     }
   });
   ```
3. **Accessibility Tree (AXTree) Trimming**:
   * Extracts the accessibility tree instead of raw HTML DOM, reducing LLM token consumption by up to 90%.
   * Identifies ARIA roles (`button`, `checkbox`, `dialog`).
4. **Autonomous Navigation Actions**:
   * `observe("Identify language selector and privacy notice banner")`: Locates multi-lingual toggles.
   * `act("Click 'Reject All' cookies")`: Tests if rejection is treated as affirmative opt-out.
   * `extract("Extract items listed in consent popup")`: Verifies itemised disclosures under Section 5(1).

---

### 4. Deep-Dive: `backend_agent` Static Analysis & Memory Optimization

The `backend_agent` performs static code analysis and auto-generates fixes without executing untrusted code:

1. **Memory-Optimized AST Construction (Tree-sitter + `.semgrepignore`)**:
   * Applies strict `.semgrepignore` files excluding `node_modules/`, `vendor/`, `.git/`, and static assets.
   * Scans only route handlers, API controllers, logger statements, and ORM database schemas, keeping memory usage **under 2GB**.
2. **Taint Analysis & Deterministic SAST (Semgrep Rule Example)**:
   ```yaml
   rules:
     - id: dpdp-plaintext-pii-logging
       patterns:
         - pattern: logger.$LOG(..., $PII_VAR, ...)
         - metavariable-regex:
             metavariable: '$PII_VAR'
             regex: '(?i)(aadhaar|pan|email|phone|password|ssn)'
       message: "DPDP Section 8(5) Violation: Unencrypted PII variable logged to console."
       severity: ERROR
   ```
3. **Gemini 3.5 Flash Remediation & Git Patch Generation**:
   * Feeds the flagged function context to Gemini 3.5 Flash and prompts for a security patch.
   * **Sample Output Patch (`.patch`)**:
     ```diff
     --- a/app/controllers/user_controller.py
     +++ b/app/controllers/user_controller.py
     @@ -14,3 +14,3 @@
     - logger.info(f"User login attempt: {user.email}, phone: {user.phone}")
     + logger.info(f"User login attempt: {user.id}, email_hash: {hash_pii(user.email)}")
     ```
