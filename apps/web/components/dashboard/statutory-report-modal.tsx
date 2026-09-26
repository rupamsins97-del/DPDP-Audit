"use client";

import * as React from "react";
import { AuditReportSummary } from "@/lib/types/dashboard";
import { synthesizeAIComplianceReport, AISynthesizedReport } from "@/lib/report-ai-synthesizer";
import { Button } from "@/components/ui/button";
import {
  ShieldCheck,
  Printer,
  Download,
  X,
  Scale,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Building,
  Calendar,
  Fingerprint,
} from "lucide-react";

interface StatutoryReportModalProps {
  report: AuditReportSummary;
  isOpen: boolean;
  onClose: () => void;
}

export function StatutoryReportModal({ report, isOpen, onClose }: StatutoryReportModalProps) {
  const [aiReport, setAiReport] = React.useState<AISynthesizedReport>(() =>
    synthesizeAIComplianceReport(report)
  );

  React.useEffect(() => {
    setAiReport(synthesizeAIComplianceReport(report));
  }, [report]);

  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadHtml = () => {
    const element = document.getElementById("statutory-report-print-container");
    if (!element) return;

    const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>DPDP Statutory Audit Report - ${report.audit_id}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; color: #111; line-height: 1.5; font-size: 13px; }
    h1 { font-size: 20px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
    .subtitle { color: #555; font-size: 11px; margin-bottom: 20px; font-weight: 600; }
    .badge { display: inline-block; padding: 4px 8px; font-weight: bold; border-radius: 4px; font-size: 11px; font-family: monospace; }
    .badge-fail { background: #fee2e2; color: #991b1b; border: 1px solid #f87171; }
    .badge-warn { background: #fef3c7; color: #92400e; border: 1px solid #fbbf24; }
    .badge-pass { background: #d1fae5; color: #065f46; border: 1px solid #34d399; }
    table { width: 100%; border-collapse: collapse; margin-top: 14px; margin-bottom: 20px; }
    th, td { border: 1px solid #ddd; padding: 8px 10px; text-align: left; font-size: 12px; }
    th { background: #f9fafb; font-weight: 600; }
    .meta-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; margin-bottom: 20px; }
    .section-title { font-size: 14px; font-weight: bold; border-bottom: 2px solid #0284c7; padding-bottom: 4px; margin-top: 24px; text-transform: uppercase; }
    .hash { font-family: monospace; font-size: 10px; word-break: break-all; color: #475569; }
  </style>
</head>
<body>
  ${element.innerHTML}
</body>
</html>
    `;

    const blob = new Blob([htmlContent], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DPDP-Statutory-Audit-Report-${report.audit_id}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-2 sm:p-4 overflow-y-auto">
      {/* Container */}
      <div className="relative w-full max-w-5xl rounded-xl border border-border bg-surface text-foreground shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Action Header Bar (Excluded in Print) */}
        <div className="flex items-center justify-between border-b border-border bg-surface-raised px-4 py-3 print:hidden shrink-0">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded bg-accent/20 text-accent">
              <Scale className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-foreground">
                Official Statutory Audit Report (PDF / Print View)
              </h3>
              <p className="text-[11px] text-muted">
                Synthesized by DPDP 360° AI Multi-Agent Compliance Engine
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="default"
              size="sm"
              onClick={handlePrint}
              className="flex items-center gap-1.5 font-mono text-xs bg-accent text-white"
            >
              <Printer className="h-3.5 w-3.5" />
              <span>Print / Save as PDF</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadHtml}
              className="flex items-center gap-1.5 font-mono text-xs"
            >
              <Download className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Download HTML</span>
            </Button>

            <button
              type="button"
              onClick={onClose}
              className="rounded-md p-1.5 text-muted hover:text-foreground hover:bg-surface transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Scrollable Report Content (Rendered & Printable) */}
        <div className="flex-1 overflow-y-auto p-6 sm:p-10 bg-white text-slate-900 print:p-0 print:overflow-visible">
          <div id="statutory-report-print-container" className="space-y-6 max-w-4xl mx-auto">
            {/* Report Header Block */}
            <div className="border-b-2 border-slate-900 pb-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-900 text-white text-[10px] font-mono uppercase tracking-wider mb-2">
                    <ShieldCheck className="h-3 w-3 text-cyan-400" />
                    <span>Statutory Compliance Memorandum</span>
                  </div>
                  <h1 className="text-2xl font-bold tracking-tight text-slate-950 uppercase">
                    DPDP 360° Statutory Compliance Audit Report
                  </h1>
                  <p className="text-xs font-semibold text-slate-600 mt-1">
                    Pursuant to India&apos;s Digital Personal Data Protection Act, 2023 (Act No. 22 of 2023) &amp; DPDP Rules, 2025
                  </p>
                </div>

                <div className="text-right">
                  <div
                    className={`inline-block px-3 py-1.5 rounded-lg border font-mono font-bold text-sm ${
                      aiReport.statutoryVerdict === "FULLY_COMPLIANT_PASS"
                        ? "bg-emerald-50 text-emerald-800 border-emerald-400"
                        : aiReport.statutoryVerdict === "SUBSTANTIALLY_COMPLIANT_WARNING"
                        ? "bg-amber-50 text-amber-800 border-amber-400"
                        : "bg-red-50 text-red-800 border-red-500"
                    }`}
                  >
                    DPDP INDEX: {report.compliance_score}% ({report.compliance_band})
                  </div>
                  <p className="text-[10px] text-slate-500 font-mono mt-1">
                    Audit ID: {report.audit_id.slice(0, 18)}...
                  </p>
                </div>
              </div>
            </div>

            {/* Audit Metadata Summary Box */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs">
              <div>
                <span className="text-[10px] font-semibold text-slate-500 block uppercase">Target Application</span>
                <span className="font-mono font-medium text-slate-900 truncate block" title={report.target_url}>
                  {report.target_url}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-semibold text-slate-500 block uppercase">Date &amp; Jurisdiction</span>
                <span className="font-mono text-slate-900 block">
                  {new Date().toLocaleDateString("en-IN")} • asia-south1 (India)
                </span>
              </div>
              <div>
                <span className="text-[10px] font-semibold text-slate-500 block uppercase">Violations Found</span>
                <span className="font-mono font-bold text-red-600 block">
                  {report.findings.length} Statutory Finding(s)
                </span>
              </div>
              <div>
                <span className="text-[10px] font-semibold text-slate-500 block uppercase">Statutory Cap</span>
                <span className="font-mono text-slate-900 block">
                  {report.critical_count > 0 ? "Triggered (≤59%)" : "None"}
                </span>
              </div>
            </div>

            {/* AI Executive Summary & Legal Verdict */}
            <div className="space-y-2">
              <h2 className="text-xs font-bold uppercase tracking-wider text-cyan-800 border-b border-slate-200 pb-1 flex items-center gap-1.5">
                <Building className="h-3.5 w-3.5" />
                <span>1. Executive Legal Summary &amp; Statutory Exposure</span>
              </h2>
              <div className="bg-slate-50/80 border border-slate-200 rounded-lg p-4 text-xs text-slate-800 leading-relaxed space-y-2">
                <p>{aiReport.executiveSummary}</p>
                <div className="pt-2 border-t border-slate-200 font-semibold text-red-800">
                  {aiReport.penaltyExposureText}
                </div>
              </div>
            </div>

            {/* 6-Domain Statutory Breakdown Table */}
            <div className="space-y-2">
              <h2 className="text-xs font-bold uppercase tracking-wider text-cyan-800 border-b border-slate-200 pb-1 flex items-center gap-1.5">
                <Scale className="h-3.5 w-3.5" />
                <span>2. 6-Domain Statutory Compliance Breakdown</span>
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-slate-200 text-xs">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 font-semibold">
                      <th className="border border-slate-200 p-2 text-left">Statutory Domain</th>
                      <th className="border border-slate-200 p-2 text-left">Section &amp; Rules</th>
                      <th className="border border-slate-200 p-2 text-center">Weight</th>
                      <th className="border border-slate-200 p-2 text-center">Score</th>
                      <th className="border border-slate-200 p-2 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {aiReport.domainAnalysis.map((d, i) => (
                      <tr key={i} className="hover:bg-slate-50">
                        <td className="border border-slate-200 p-2 font-medium">{d.domainName}</td>
                        <td className="border border-slate-200 p-2 text-slate-600 font-mono text-[11px]">
                          {d.statutorySection}
                        </td>
                        <td className="border border-slate-200 p-2 text-center font-mono">{d.weight}</td>
                        <td className="border border-slate-200 p-2 text-center font-mono font-bold">
                          {d.score}%
                        </td>
                        <td className="border border-slate-200 p-2 text-center">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                              d.status === "PASS"
                                ? "bg-emerald-100 text-emerald-800"
                                : d.status === "WARN"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {d.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Itemized Reconciled Statutory Findings */}
            <div className="space-y-2">
              <h2 className="text-xs font-bold uppercase tracking-wider text-cyan-800 border-b border-slate-200 pb-1 flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" />
                <span>3. Itemized Statutory Non-Compliances &amp; Technical Evidence</span>
              </h2>

              {report.findings.length === 0 ? (
                <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  <span>100% Statutory Alignment — No statutory discrepancies or PII leaks detected.</span>
                </div>
              ) : (
                <div className="space-y-3">
                  {report.findings.map((f, idx) => (
                    <div
                      key={f.id || idx}
                      className="border border-slate-200 rounded-lg p-3 bg-slate-50/50 space-y-1.5 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                              f.severity === "CRITICAL"
                                ? "bg-red-600 text-white"
                                : f.severity === "HIGH"
                                ? "bg-red-100 text-red-800 border border-red-300"
                                : f.severity === "MEDIUM"
                                ? "bg-amber-100 text-amber-800 border border-amber-300"
                                : "bg-blue-100 text-blue-800"
                            }`}
                          >
                            {f.severity}
                          </span>
                          <span className="font-bold text-slate-900">{f.title}</span>
                        </div>

                        <div className="text-[11px] font-mono text-cyan-800 font-semibold">
                          {f.act_section} {f.rules_clause ? `• ${f.rules_clause}` : ""}
                        </div>
                      </div>

                      <p className="text-slate-700 text-[11px] leading-relaxed">{f.description}</p>

                      <div className="bg-slate-100 p-2 rounded text-[11px] font-mono text-slate-800 border border-slate-200">
                        <span className="text-slate-500 font-semibold block mb-0.5">Mandated Action / Evidence:</span>
                        {f.evidence_summary || f.action_label || "Apply recommended statutory remediation."}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* AI Statutory Action Roadmap */}
            <div className="space-y-2">
              <h2 className="text-xs font-bold uppercase tracking-wider text-cyan-800 border-b border-slate-200 pb-1 flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>4. Immediate Statutory Corrective Action Plan</span>
              </h2>
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs space-y-1.5">
                {aiReport.immediateActions.map((action, i) => (
                  <div key={i} className="flex items-start gap-2 text-slate-800">
                    <span className="font-mono text-cyan-700 font-bold">[{i + 1}]</span>
                    <span>{action}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Cryptographic Tamper-Evident Seal & Sign-off */}
            <div className="pt-4 border-t-2 border-slate-300 text-[10px] text-slate-500 font-mono space-y-1">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                <div className="flex items-center gap-1">
                  <Fingerprint className="h-3.5 w-3.5 text-slate-600" />
                  <span>SHA-256 State Hash:</span>
                  <span className="font-semibold text-slate-800 break-all">{aiReport.auditorCertification.stateHash}</span>
                </div>
                <span>Certified: {aiReport.auditorCertification.timestamp}</span>
              </div>
              <p className="text-slate-400">
                Generated by DPDP 360° Multi-Agent Statutory Engine • Ephemeral in-memory execution • asia-south1 (India)
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
