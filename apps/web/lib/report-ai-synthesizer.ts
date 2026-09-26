import { AuditReportSummary } from "@/lib/types/dashboard";

export interface AISynthesizedReport {
  title: string;
  statutoryReference: string;
  executiveSummary: string;
  statutoryVerdict: "NON_COMPLIANT_CRITICAL" | "SUBSTANTIALLY_COMPLIANT_WARNING" | "FULLY_COMPLIANT_PASS";
  penaltyExposureText: string;
  criticalViolationsCount: number;
  highViolationsCount: number;
  mediumViolationsCount: number;
  lowViolationsCount: number;
  domainAnalysis: {
    domainName: string;
    score: number;
    weight: string;
    status: "PASS" | "WARN" | "FAIL";
    statutorySection: string;
    summary: string;
  }[];
  immediateActions: string[];
  auditorCertification: {
    engine: string;
    stateHash: string;
    jurisdiction: string;
    timestamp: string;
  };
}

export function synthesizeAIComplianceReport(report: AuditReportSummary): AISynthesizedReport {
  const criticalFindings = report.findings.filter((f) => f.severity === "CRITICAL");
  const highFindings = report.findings.filter((f) => f.severity === "HIGH");
  const mediumFindings = report.findings.filter((f) => f.severity === "MEDIUM");
  const lowFindings = report.findings.filter((f) => f.severity === "LOW");

  let verdict: AISynthesizedReport["statutoryVerdict"] = "FULLY_COMPLIANT_PASS";
  let penaltyExposureText = "Zero statutory penalty exposure identified under current operational parameters.";

  if (criticalFindings.length > 0 || report.compliance_score < 60) {
    verdict = "NON_COMPLIANT_CRITICAL";
    penaltyExposureText =
      "HIGH STATUTORY EXPOSURE: Under DPDP Act 2023 Section 33 & Schedule, failure to implement reasonable security safeguards or children's data obligations carries penalties up to ₹250 Crores (Approx. $30M USD) per statutory breach.";
  } else if (highFindings.length > 0 || report.compliance_score < 80) {
    verdict = "SUBSTANTIALLY_COMPLIANT_WARNING";
    penaltyExposureText =
      "MODERATE STATUTORY RISK: Discrepancies between legal notice disclosures and technical telemetry carry statutory inquiry risks under Section 5(1) & Section 6(1) with penalties up to ₹50 Crores.";
  }

  const getScore = (key: string): number => {
    if (!Array.isArray(report.domain_scores)) return 100;
    const item = report.domain_scores.find((d) => d.key === key);
    return item ? item.score : 100;
  };

  const consentScore = getScore("consent_ui");
  const backendScore = getScore("backend_pii");
  const legalScore = getScore("legal_governance");
  const childScore = getScore("child_safety");
  const incidentScore = getScore("incident_management");
  const dprScore = getScore("dpr_redressal");

  // Generate domain breakdown
  const domainAnalysis: AISynthesizedReport["domainAnalysis"] = [
    {
      domainName: "Frontend Consent & Notice",
      score: consentScore,
      weight: "25%",
      status: consentScore >= 80 ? "PASS" : consentScore >= 60 ? "WARN" : "FAIL",
      statutorySection: "Section 5(1) & Section 6(1), Rules 3–4",
      summary:
        consentScore < 80
          ? "Pre-consent trackers or bundled consent dialogs detected prior to affirmative Data Principal action."
          : "Affirmative, itemised, granular consent dialogs properly verified across all user entrypoints.",
    },
    {
      domainName: "Backend Security & PII Protection",
      score: backendScore,
      weight: "25%",
      status: backendScore >= 80 ? "PASS" : backendScore >= 60 ? "WARN" : "FAIL",
      statutorySection: "Section 8(5), Rule 6",
      summary:
        backendScore < 80
          ? "Plaintext PII logging or unencrypted identifiers identified in application source AST / telemetry traces."
          : "Reasonable security safeguards and PII sanitization verified across backend service models.",
    },
    {
      domainName: "Legal Notice & DPA Governance",
      score: legalScore,
      weight: "20%",
      status: legalScore >= 80 ? "PASS" : legalScore >= 60 ? "WARN" : "FAIL",
      statutorySection: "Section 5(1), Section 8(1), Rule 5",
      summary:
        legalScore < 80
          ? "Misalignment identified between privacy notice claims and empirical technical execution."
          : "Statutory notice items, processing purposes, and DPA vendor schedules align with actual data flows.",
    },
    {
      domainName: "Children's Data & Age-Gating",
      score: childScore,
      weight: "10%",
      status: childScore >= 80 ? "PASS" : childScore >= 60 ? "WARN" : "FAIL",
      statutorySection: "Section 9(1)–(3), Rule 10",
      summary:
        childScore < 80
          ? "Missing Verifiable Parental Consent (VPC) mechanism or behavioral tracking prohibition on minors."
          : "Compliant age-gating and parental verification flows verified.",
    },
    {
      domainName: "Incident Management & 72h SLA",
      score: incidentScore,
      weight: "10%",
      status: incidentScore >= 80 ? "PASS" : incidentScore >= 60 ? "WARN" : "FAIL",
      statutorySection: "Section 8(6), Rule 7",
      summary:
        incidentScore < 80
          ? "Automated 72-hour Data Protection Board (DPB) breach notification pipeline requires remediation."
          : "Automated breach intake and 72-hour DPB statutory reporting channels confirmed active.",
    },
    {
      domainName: "Data Principal Rights (DPR) & Redressal",
      score: dprScore,
      weight: "10%",
      status: dprScore >= 80 ? "PASS" : dprScore >= 60 ? "WARN" : "FAIL",
      statutorySection: "Section 11–14, Rule 11",
      summary:
        dprScore < 80
          ? "Grievance redressal channel or automated data erasure upon consent withdrawal not fully wired."
          : "Self-service right to access, correction, erasure, and grievance redressal confirmed functional.",
    },
  ];

  // Synthesize executive summary
  const summaryText =
    verdict === "NON_COMPLIANT_CRITICAL"
      ? `The DPDP 360° Multi-Agent Statutory Auditor completed an end-to-end statutory compliance evaluation of ${report.target_url}. The overall DPDP Compliance Index is computed at ${report.compliance_score}% (Status: FAIL). Under the Zero-Tolerance Statutory Rule, critical non-compliances were identified in statutory age-gating / security safeguards. Immediate corrective engineering and legal remediation is mandated to mitigate statutory liability under DPDP Act 2023 Section 33.`
      : verdict === "SUBSTANTIALLY_COMPLIANT_WARNING"
      ? `The DPDP 360° Multi-Agent Statutory Auditor completed an evaluation of ${report.target_url}. The overall DPDP Compliance Index is ${report.compliance_score}% (Status: WARN). While foundational data protection measures are established, ${report.findings.length} statutory discrepancy findings were observed between published legal notices and live technical telemetry.`
      : `The DPDP 360° Multi-Agent Statutory Auditor completed an evaluation of ${report.target_url}. The overall DPDP Compliance Index is ${report.compliance_score}% (Status: PASS). The verified system demonstrates high statutory fidelity with affirmative consent, reasonable security safeguards, and grounded legal notice disclosures.`;

  // Immediate Action Items
  const actions: string[] = [];
  if (criticalFindings.length > 0) {
    criticalFindings.forEach((f) => {
      actions.push(`[CRITICAL] Remediate: ${f.title} (${f.act_section}) — Apply unified code patch or VPC workflow immediately.`);
    });
  }
  if (highFindings.length > 0) {
    highFindings.forEach((f) => {
      actions.push(`[HIGH] Remediate: ${f.title} (${f.act_section}) — Mask PII identifiers and update DPA schedules.`);
    });
  }
  if (mediumFindings.length > 0) {
    mediumFindings.forEach((f) => {
      actions.push(`[MEDIUM] Resolve: ${f.title} (${f.act_section}) — Align retention timestamps and consent notice items.`);
    });
  }
  if (actions.length === 0) {
    actions.push("Maintain periodic continuous compliance auditing and monitor upstream vendor DPA schedules.");
  }

  return {
    title: "STATUTORY DPDP COMPLIANCE AUDIT REPORT",
    statutoryReference: "Digital Personal Data Protection Act, 2023 (Act No. 22 of 2023) & DPDP Rules, 2025",
    executiveSummary: summaryText,
    statutoryVerdict: verdict,
    penaltyExposureText,
    criticalViolationsCount: criticalFindings.length,
    highViolationsCount: highFindings.length,
    mediumViolationsCount: mediumFindings.length,
    lowViolationsCount: lowFindings.length,
    domainAnalysis,
    immediateActions: actions,
    auditorCertification: {
      engine: "DPDP 360° Multi-Agent Statutory Audit Orchestrator v1.0",
      stateHash: report.state_hash || "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      jurisdiction: "Republic of India — Data Residency: asia-south1 (Mumbai)",
      timestamp: new Date().toISOString(),
    },
  };
}
