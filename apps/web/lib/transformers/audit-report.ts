import { AgentRole } from "@/lib/types/telemetry";
import {
  AuditFindingItem,
  AuditReportSummary,
  ComplianceBand,
  DomainScoreItem,
  FindingActionType,
  FindingSeverity,
} from "@/lib/types/dashboard";

export interface BackendAuditFinding {
  finding_id: string;
  audit_id: string;
  agent_role: string;
  act_section: string;
  rules_clause: string;
  severity: FindingSeverity;
  title: string;
  description: string;
  evidence_snippet: string;
  remediation_suggestion: string;
  created_at: string;
}

export interface BackendAuditRecord {
  audit_id: string;
  organization_id: string;
  project_name: string;
  target_url: string;
  repository_url?: string | null;
  status: "QUEUED" | "IN_PROGRESS" | "COMPLETED" | "FAILED";
  compliance_score?: number | null;
  state_hash?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendCodePatch {
  patch_id: string;
  finding_id: string;
  file_path: string;
  original_code: string;
  patched_code: string;
  diff_content: string;
  status: string;
  created_at: string;
}

export interface BackendAuditContextResponse {
  audit: BackendAuditRecord;
  governance_promises: Array<Record<string, unknown>>;
  findings: BackendAuditFinding[];
  generated_patches: BackendCodePatch[];
}

export const STATUTORY_DOMAINS: Array<{
  key: string;
  domain: string;
  weight: number;
  matchingRoles: string[];
}> = [
  {
    key: "frontend",
    domain: "Frontend Consent & Tracking",
    weight: 0.25,
    matchingRoles: ["frontend_agent", "frontend"],
  },
  {
    key: "backend",
    domain: "Backend PII Security & Logging",
    weight: 0.25,
    matchingRoles: ["backend_agent", "backend"],
  },
  {
    key: "policy",
    domain: "Legal Governance & DPA Alignment",
    weight: 0.2,
    matchingRoles: ["policy_agent", "policy", "synthesis_agent"],
  },
  {
    key: "child_safety",
    domain: "Children's Data Protection",
    weight: 0.1,
    matchingRoles: ["child_safety_agent", "child_safety"],
  },
  {
    key: "incident",
    domain: "Incident Management & 72h SLA",
    weight: 0.1,
    matchingRoles: ["incident_management_agent", "incident"],
  },
  {
    key: "dpr_portal",
    domain: "DPR & Grievance Redressal",
    weight: 0.1,
    matchingRoles: ["dpr_portal_agent", "dpr_portal"],
  },
];

const SEVERITY_DEDUCTIONS: Record<FindingSeverity, number> = {
  CRITICAL: 30.0,
  HIGH: 15.0,
  MEDIUM: 8.0,
  LOW: 3.0,
};

export function mapAgentRoleToAction(
  agentRole: string
): { action_type: FindingActionType; action_label: string } {
  const role = agentRole.toLowerCase();
  switch (role) {
    case "frontend_agent":
    case "frontend":
      return { action_type: "VIEW_TRACE", action_label: "View Trace" };
    case "backend_agent":
    case "backend":
      return { action_type: "APPLY_PATCH", action_label: "Review Patch" };
    case "policy_agent":
    case "policy":
      return { action_type: "DOWNLOAD_CLAUSE", action_label: "Download Clause" };
    case "child_safety_agent":
    case "child_safety":
      return { action_type: "CONFIG_GATEWAY", action_label: "Configure VPC Gateway" };
    case "incident_management_agent":
    case "incident":
      return { action_type: "SETUP_WEBHOOK", action_label: "Setup Webhook" };
    case "dpr_portal_agent":
    case "dpr_portal":
      return { action_type: "UPDATE_SLA", action_label: "Configure SLA Timer" };
    case "synthesis_agent":
    default:
      return { action_type: "VIEW_TRACE", action_label: "View Trace" };
  }
}

export function computeDomainScores(findings: BackendAuditFinding[]): DomainScoreItem[] {
  return STATUTORY_DOMAINS.map((domainDef) => {
    const domainFindings = findings.filter((f) =>
      domainDef.matchingRoles.includes(f.agent_role.toLowerCase())
    );

    const deductions = domainFindings.reduce(
      (sum, f) => sum + (SEVERITY_DEDUCTIONS[f.severity] || 0),
      0
    );

    const rawScore = Math.max(0, Math.min(100, 100 - deductions));

    return {
      domain: domainDef.domain,
      key: domainDef.key,
      weight: domainDef.weight,
      score: Math.round(rawScore),
      deductions: Math.round(deductions),
      findingCount: domainFindings.length,
    };
  });
}

export function getComplianceBand(score: number): ComplianceBand {
  if (score >= 80) return "PASS";
  if (score >= 60) return "WARN";
  return "FAIL";
}

export function transformBackendAuditToSummary(
  response: BackendAuditContextResponse
): AuditReportSummary {
  const { audit, findings, generated_patches } = response;

  const transformedFindings: AuditFindingItem[] = (findings || []).map((f) => {
    const { action_type, action_label } = mapAgentRoleToAction(f.agent_role);
    const matchingPatch = (generated_patches || []).find(
      (p) => p.finding_id === f.finding_id
    );

    return {
      id: f.finding_id,
      audit_id: f.audit_id,
      agent_role: f.agent_role as AgentRole,
      finding_type: f.title.toUpperCase().replace(/\s+/g, "_"),
      severity: f.severity,
      title: f.title,
      description: f.description,
      act_section: f.act_section,
      rules_clause: f.rules_clause,
      evidence_summary: f.evidence_snippet,
      evidence_payload: matchingPatch
        ? {
            file_path: matchingPatch.file_path,
            diff_content: matchingPatch.diff_content,
            patch_status: matchingPatch.status,
          }
        : {
            evidence: f.evidence_snippet,
            remediation: f.remediation_suggestion,
          },
      action_type,
      action_label,
      created_at: f.created_at,
    };
  });

  const domainScores = computeDomainScores(findings || []);

  const criticalCount = transformedFindings.filter((f) => f.severity === "CRITICAL").length;
  const highCount = transformedFindings.filter((f) => f.severity === "HIGH").length;
  const mediumCount = transformedFindings.filter((f) => f.severity === "MEDIUM").length;
  const lowCount = transformedFindings.filter((f) => f.severity === "LOW").length;

  let complianceScore = audit.compliance_score;
  if (complianceScore === null || complianceScore === undefined) {
    const weightedSum = domainScores.reduce((sum, d) => sum + d.score * d.weight, 0);
    const rawScore = Math.round(weightedSum);
    if (criticalCount > 0 && rawScore > 59) {
      complianceScore = 59;
    } else {
      complianceScore = rawScore;
    }
  }

  const complianceBand = getComplianceBand(complianceScore);

  return {
    audit_id: audit.audit_id,
    target_url: audit.target_url,
    framework: "DPDP Act, 2023 & DPDP Rules, 2025",
    compliance_score: complianceScore,
    compliance_band: complianceBand,
    status: audit.status === "COMPLETED" ? "COMPLETED" : audit.status === "FAILED" ? "FAILED" : "RUNNING",
    created_at: audit.created_at,
    state_hash: audit.state_hash || "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    critical_count: criticalCount,
    high_count: highCount,
    medium_count: mediumCount,
    low_count: lowCount,
    domain_scores: domainScores,
    findings: transformedFindings,
  };
}
