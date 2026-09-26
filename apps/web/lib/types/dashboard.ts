import { AgentRole } from "./telemetry";

export type FindingSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type ComplianceBand = "PASS" | "WARN" | "FAIL";

export type FindingActionType =
  | "VIEW_TRACE"
  | "APPLY_PATCH"
  | "GENERATE_SCRIPT"
  | "DOWNLOAD_CLAUSE"
  | "CONFIG_GATEWAY"
  | "SETUP_WEBHOOK"
  | "UPDATE_SLA";

export interface AuditFindingItem {
  id: string;
  audit_id: string;
  agent_role: AgentRole;
  finding_type: string;
  severity: FindingSeverity;
  title: string;
  description: string;
  act_section: string;
  rules_clause?: string;
  evidence_summary?: string;
  evidence_payload?: Record<string, unknown>;
  action_type: FindingActionType;
  action_label: string;
  created_at: string;
}

export interface DomainScoreItem {
  domain: string;
  key: string;
  weight: number; // e.g. 0.25
  score: number;  // 0 - 100
  deductions: number;
  findingCount: number;
}

export interface AuditReportSummary {
  audit_id: string;
  target_url: string;
  framework: string;
  compliance_score: number;
  compliance_band: ComplianceBand;
  status: "COMPLETED" | "RUNNING" | "FAILED";
  created_at: string;
  state_hash: string;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  domain_scores: DomainScoreItem[];
  findings: AuditFindingItem[];
}
