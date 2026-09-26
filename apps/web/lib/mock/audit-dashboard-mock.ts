import {
  AuditFindingItem,
  AuditReportSummary,
  ComplianceBand,
  DomainScoreItem,
} from "@/lib/types/dashboard";

export const MOCK_FINDINGS_WARN: AuditFindingItem[] = [
  {
    id: "finding-001",
    audit_id: "audit-dpdp-360-live",
    agent_role: "frontend_agent",
    finding_type: "PRE_CONSENT_TRACKER_FIRE",
    severity: "CRITICAL",
    title: "Pre-Consent Meta Pixel Fire",
    description:
      "Third-party tracking beacon (https://connect.facebook.net/en_US/fbevents.js) executed network calls before user consent modal interaction.",
    act_section: "Sec 6(1)",
    rules_clause: "Rule 3(2)",
    evidence_summary: "CDP network request logged at t=320ms before DOM consent click.",
    evidence_payload: {
      url: "https://connect.facebook.net/en_US/fbevents.js",
      method: "GET",
      tracker_domain: "facebook.net",
      cookies_set: ["_fbp"],
    },
    action_type: "VIEW_TRACE",
    action_label: "View Network Trace",
    created_at: "2026-09-26T16:40:00Z",
  },
  {
    id: "finding-002",
    audit_id: "audit-dpdp-360-live",
    agent_role: "backend_agent",
    finding_type: "PLAINTEXT_PII_LOGGING",
    severity: "HIGH",
    title: "Plaintext PII Logging",
    description:
      "Raw Aadhaar numbers and phone numbers logged in plain text without cryptographic masking in user_controller.py:14.",
    act_section: "Sec 8(5)",
    rules_clause: "Rule 4(2)",
    evidence_summary: "AST Semgrep match on logger.info() with sensitive Aadhaar variable identifier.",
    evidence_payload: {
      file_path: "apps/api/controllers/user_controller.py",
      line_number: 14,
      code_snippet: 'logger.info("User KYC submitted: aadhaar=%s", user.aadhaar)',
    },
    action_type: "APPLY_PATCH",
    action_label: "Apply Auto-Fix PR",
    created_at: "2026-09-26T16:40:05Z",
  },
  {
    id: "finding-003",
    audit_id: "audit-dpdp-360-live",
    agent_role: "backend_agent",
    finding_type: "MISSING_ERASURE_CRON",
    severity: "HIGH",
    title: "Missing Erasure Cron Job",
    description:
      "Database models lack cascade purge triggers or scheduled pg_cron retention jobs upon consent withdrawal.",
    act_section: "Sec 8(7)",
    rules_clause: "Rule 4(5)",
    evidence_summary: "No SQL DELETE trigger attached to revoked user_consent events in Prisma schema.",
    evidence_payload: {
      table_name: "user_consents",
      missing_trigger: "trg_purge_on_withdrawal",
    },
    action_type: "GENERATE_SCRIPT",
    action_label: "Generate DB Script",
    created_at: "2026-09-26T16:40:10Z",
  },
  {
    id: "finding-004",
    audit_id: "audit-dpdp-360-live",
    agent_role: "policy_agent",
    finding_type: "DPA_RETENTION_MISALIGNMENT",
    severity: "CRITICAL",
    title: "DPA 60-day Retention Term",
    description:
      "Data Processor Agreement (DPA) stipulates 60-day data retention post-contract termination exceeding statutory purpose limitation requirements.",
    act_section: "Rule 6(1)(e)",
    rules_clause: "DPDP Rules 2025 Schedule II",
    evidence_summary: "Extracted legal clause from uploaded vendor DPA PDF Page 4.",
    evidence_payload: {
      clause_text: "Vendor shall retain customer data for sixty (60) days following termination.",
      recommended_clause: "Vendor shall immediately permanently erase customer data upon termination.",
    },
    action_type: "DOWNLOAD_CLAUSE",
    action_label: "Download DPA Clause",
    created_at: "2026-09-26T16:40:15Z",
  },
  {
    id: "finding-005",
    audit_id: "audit-dpdp-360-live",
    agent_role: "child_safety_agent",
    finding_type: "MISSING_VPC_INTEGRATION",
    severity: "MEDIUM",
    title: "Verifiable Parental Consent Gap",
    description:
      "Age-gated onboarding flow lacks government-recognized tokenized ID (DigiLocker / Aadhaar XML) for minor parental consent.",
    act_section: "Sec 9(1)",
    rules_clause: "Rule 5(1)",
    evidence_summary: "AXTree scan identified self-declaration checkbox without cryptographic VPC verification.",
    action_type: "CONFIG_GATEWAY",
    action_label: "Configure VPC Gateway",
    created_at: "2026-09-26T16:40:20Z",
  },
  {
    id: "finding-006",
    audit_id: "audit-dpdp-360-live",
    agent_role: "incident_management_agent",
    finding_type: "MISSING_72H_WEBHOOK",
    severity: "HIGH",
    title: "Missing 72h DPB Incident Webhook",
    description:
      "Data breach escalation pipeline lacks automated notification dispatch to the Data Protection Board of India within 72 hours.",
    act_section: "Rule 7(1)",
    rules_clause: "DPDP Act Sec 8(6)",
    evidence_summary: "No incident webhook endpoint configured in organization security settings.",
    action_type: "SETUP_WEBHOOK",
    action_label: "Setup Webhook Endpoint",
    created_at: "2026-09-26T16:40:25Z",
  },
];

export const MOCK_DOMAIN_SCORES_WARN: DomainScoreItem[] = [
  {
    domain: "Frontend Consent & Tracking",
    key: "frontend",
    weight: 0.25,
    score: 70,
    deductions: 30,
    findingCount: 1,
  },
  {
    domain: "Backend PII Security & Logging",
    key: "backend",
    weight: 0.25,
    score: 70,
    deductions: 30,
    findingCount: 2,
  },
  {
    domain: "Legal Governance & DPA",
    key: "policy",
    weight: 0.20,
    score: 70,
    deductions: 30,
    findingCount: 1,
  },
  {
    domain: "Children's Data Protection",
    key: "child_safety",
    weight: 0.10,
    score: 92,
    deductions: 8,
    findingCount: 1,
  },
  {
    domain: "Incident Management & 72h SLA",
    key: "incident",
    weight: 0.10,
    score: 85,
    deductions: 15,
    findingCount: 1,
  },
  {
    domain: "DPR & Grievance Redressal",
    key: "dpr",
    weight: 0.10,
    score: 100,
    deductions: 0,
    findingCount: 0,
  },
];

export function getMockAuditReport(
  scenario: "PASS" | "WARN" | "FAIL" = "WARN"
): AuditReportSummary {
  switch (scenario) {
    case "PASS":
      return {
        audit_id: "audit-pass-clean-94",
        target_url: "https://secure-bank.example.in",
        framework: "DPDP Act, 2023 & DPDP Rules, 2025",
        compliance_score: 94,
        compliance_band: "PASS",
        status: "COMPLETED",
        created_at: "2026-09-26T16:45:00Z",
        state_hash: "a4f78e91c3d28b14e9f7432098bcadfe1234567890abcdef1234567890abcdef",
        critical_count: 0,
        high_count: 0,
        medium_count: 1,
        low_count: 1,
        domain_scores: [
          { domain: "Frontend Consent & Tracking", key: "frontend", weight: 0.25, score: 97, deductions: 3, findingCount: 1 },
          { domain: "Backend PII Security & Logging", key: "backend", weight: 0.25, score: 92, deductions: 8, findingCount: 1 },
          { domain: "Legal Governance & DPA", key: "policy", weight: 0.20, score: 100, deductions: 0, findingCount: 0 },
          { domain: "Children's Data Protection", key: "child_safety", weight: 0.10, score: 100, deductions: 0, findingCount: 0 },
          { domain: "Incident Management & 72h SLA", key: "incident", weight: 0.10, score: 100, deductions: 0, findingCount: 0 },
          { domain: "DPR & Grievance Redressal", key: "dpr", weight: 0.10, score: 100, deductions: 0, findingCount: 0 },
        ],
        findings: [
          {
            id: "finding-pass-001",
            audit_id: "audit-pass-clean-94",
            agent_role: "backend_agent",
            finding_type: "REDUNDANT_COMMENT_AST",
            severity: "LOW",
            title: "Redundant Debug Comments in Auth Module",
            description: "Developer comments contain obsolete field mappings without sensitive data.",
            act_section: "Sec 8(5)",
            rules_clause: "Best Practice",
            action_type: "APPLY_PATCH",
            action_label: "Apply Auto-Fix PR",
            created_at: "2026-09-26T16:45:10Z",
          },
        ],
      };

    case "FAIL":
      return {
        audit_id: "audit-fail-statutory-cap-58",
        target_url: "https://ad-tracker-app.example.com",
        framework: "DPDP Act, 2023 & DPDP Rules, 2025",
        compliance_score: 58,
        compliance_band: "FAIL",
        status: "COMPLETED",
        created_at: "2026-09-26T16:30:00Z",
        state_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        critical_count: 2,
        high_count: 3,
        medium_count: 1,
        low_count: 0,
        domain_scores: MOCK_DOMAIN_SCORES_WARN,
        findings: MOCK_FINDINGS_WARN,
      };

    case "WARN":
    default:
      return {
        audit_id: "audit-dpdp-360-live",
        target_url: "https://target-app.example.com",
        framework: "DPDP Act, 2023 & DPDP Rules, 2025",
        compliance_score: 72,
        compliance_band: "WARN",
        status: "COMPLETED",
        created_at: "2026-09-26T16:40:00Z",
        state_hash: "f7c3bc1d9e284a5690b8f1a2e3d4c5b6a78901234567890abcdef1234567890a",
        critical_count: 1,
        high_count: 3,
        medium_count: 2,
        low_count: 0,
        domain_scores: MOCK_DOMAIN_SCORES_WARN,
        findings: MOCK_FINDINGS_WARN,
      };
  }
}
