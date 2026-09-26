"use client";

import * as React from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ComplianceGauge } from "@/components/dashboard/compliance-gauge";
import { FindingsTable } from "@/components/dashboard/findings-table";
import { StatutoryReportModal } from "@/components/dashboard/statutory-report-modal";
import { getMockAuditReport } from "@/lib/mock/audit-dashboard-mock";
import { ComplianceBand, AuditReportSummary } from "@/lib/types/dashboard";
import { apiClient } from "@/lib/api-client";
import {
  BackendAuditContextResponse,
  transformBackendAuditToSummary,
} from "@/lib/transformers/audit-report";
import { Button } from "@/components/ui/button";
import {
  ShieldCheck,
  Globe,
  Radio,
  Download,
  RotateCcw,
  Sparkles,
  AlertCircle,
  Loader2,
  PlusCircle,
  FileText,
  History,
  CheckCircle2,
} from "lucide-react";

interface AuditHistoryItem {
  id: string;
  name: string;
  target_url: string;
  score?: number;
  timestamp: string;
}

interface ReconciliationDashboardProps {
  initialScenario?: ComplianceBand;
  className?: string;
}

export function ReconciliationDashboard({
  initialScenario = "WARN",
  className,
}: ReconciliationDashboardProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const auditIdParam = searchParams.get("audit_id");

  const [scenario, setScenario] = React.useState<ComplianceBand>(initialScenario);
  const [liveReport, setLiveReport] = React.useState<AuditReportSummary | null>(null);
  const [isLoading, setIsLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);
  const [isReportModalOpen, setIsReportModalOpen] = React.useState<boolean>(false);
  const [auditHistory, setAuditHistory] = React.useState<AuditHistoryItem[]>([]);

  // Load audit history from localStorage
  React.useEffect(() => {
    try {
      const savedHistory = localStorage.getItem("dpdp_audit_history");
      if (savedHistory) {
        const parsed: AuditHistoryItem[] = JSON.parse(savedHistory);
        setAuditHistory(parsed);
      }
    } catch {
      // ignore
    }
  }, []);

  // Fetch real audit report if audit_id is present or retrieved from storage
  const fetchLiveAudit = React.useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const { data, error: apiError } = await apiClient<BackendAuditContextResponse>(
        `/audits/${id}`
      );

      if (apiError || !data) {
        setError(
          apiError ||
            "Unable to retrieve audit report. The audit may not exist or belongs to another organization under multi-tenant isolation."
        );
        setLiveReport(null);
      } else {
        const transformed = transformBackendAuditToSummary(data);
        setLiveReport(transformed);

        // Save active audit ID and update history in localStorage
        try {
          localStorage.setItem("dpdp_latest_audit_id", id);
          const historyItem: AuditHistoryItem = {
            id,
            name: transformed.target_url || "Personal Gemini Journal",
            target_url: transformed.target_url,
            score: transformed.compliance_score,
            timestamp: new Date().toISOString(),
          };

          const raw = localStorage.getItem("dpdp_audit_history");
          let history: AuditHistoryItem[] = raw ? JSON.parse(raw) : [];
          history = [historyItem, ...history.filter((h) => h.id !== id)].slice(0, 10);
          localStorage.setItem("dpdp_audit_history", JSON.stringify(history));
          setAuditHistory(history);
        } catch {
          // ignore
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit findings.");
      setLiveReport(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial load: check query param first, then fallback to latest stored audit
  React.useEffect(() => {
    if (auditIdParam) {
      fetchLiveAudit(auditIdParam);
    } else {
      const storedId = localStorage.getItem("dpdp_latest_audit_id");
      if (storedId) {
        fetchLiveAudit(storedId);
      } else {
        setLiveReport(null);
        setIsLoading(false);
        setError(null);
      }
    }
  }, [auditIdParam, fetchLiveAudit]);

  // If live data is available, use it; otherwise fallback to scenario mock
  const activeReport = React.useMemo(() => {
    if (liveReport) return liveReport;
    return getMockAuditReport(scenario);
  }, [liveReport, scenario]);

  const handleExportJson = () => {
    const reportData = {
      export_timestamp: new Date().toISOString(),
      statute: "Digital Personal Data Protection Act, 2023 & DPDP Rules, 2025",
      compliance_index: activeReport.compliance_score,
      compliance_status: activeReport.compliance_band,
      tamper_evident_state_hash: activeReport.state_hash,
      audit_metadata: {
        audit_id: activeReport.audit_id,
        target_url: activeReport.target_url,
        created_at: activeReport.created_at,
      },
      domain_breakdown: activeReport.domain_scores,
      findings_count: activeReport.findings.length,
      findings: activeReport.findings,
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `DPDP-360-Audit-Report-${activeReport.audit_id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleSelectPastAudit = (id: string) => {
    router.push(`/dashboard?audit_id=${id}`);
    fetchLiveAudit(id);
  };

  return (
    <div className={`space-y-6 w-full max-w-7xl mx-auto ${className || ""}`}>
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-xl border border-border bg-surface p-4 shadow-md">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded bg-surface-raised px-2 py-0.5 text-xs font-mono text-muted border border-border">
              <Radio className="h-3 w-3 text-emerald-400" />
              <span>ID: {activeReport.audit_id.slice(0, 12)}...</span>
            </span>
            <span className="inline-flex items-center gap-1.5 rounded bg-surface-raised px-2 py-0.5 text-xs font-mono text-muted border border-border">
              <Globe className="h-3 w-3 text-accent" />
              <span className="text-foreground max-w-[240px] truncate">
                {activeReport.target_url}
              </span>
            </span>
            {liveReport && (
              <span className="inline-flex items-center gap-1 rounded bg-emerald-500/10 px-2 py-0.5 text-xs font-mono text-emerald-400 border border-emerald-500/30">
                <ShieldCheck className="h-3 w-3" />
                <span>Live Audit Data</span>
              </span>
            )}
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
            360° Statutory Reconciliation Dashboard
          </h1>
        </div>

        {/* Controls: Audit Actions, PDF Report Modal, Test Scenario Switcher */}
        <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
          {/* AI Statutory PDF Report Trigger */}
          <Button
            variant="default"
            size="sm"
            onClick={() => setIsReportModalOpen(true)}
            className="flex items-center gap-1.5 font-mono text-xs bg-accent text-white shadow-sm hover:bg-accent/90"
          >
            <FileText className="h-3.5 w-3.5" />
            <span>AI Statutory PDF Report</span>
          </Button>

          {/* Audit History Selector if available */}
          {auditHistory.length > 0 && (
            <div className="relative inline-block">
              <select
                aria-label="Select past audit"
                onChange={(e) => {
                  if (e.target.value) handleSelectPastAudit(e.target.value);
                }}
                value={activeReport.audit_id}
                className="rounded-md border border-border bg-surface-raised px-2.5 py-1.5 text-xs font-mono text-muted hover:text-foreground focus:outline-none focus:border-accent"
              >
                <option value="" disabled>
                  Audit History ({auditHistory.length})
                </option>
                {auditHistory.map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.score !== undefined ? `[${h.score}%] ` : ""}
                    {h.name.replace("https://", "").replace("http://", "").slice(0, 20)} ({h.id.slice(0, 8)})
                  </option>
                ))}
              </select>
            </div>
          )}

          {auditIdParam || liveReport ? (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchLiveAudit(activeReport.audit_id)}
                disabled={isLoading}
                className="flex items-center gap-1.5 text-xs font-mono"
              >
                <RotateCcw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
                <span>Refresh</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push("/")}
                className="flex items-center gap-1.5 text-xs font-mono"
              >
                <PlusCircle className="h-3.5 w-3.5" />
                <span>New Audit</span>
              </Button>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
              <div className="flex items-center gap-1 text-muted text-[11px]">
                <Sparkles className="h-3.5 w-3.5 text-accent" />
                <span>Test Bands:</span>
              </div>
              <div className="inline-flex rounded-lg border border-border bg-surface-raised p-1">
                <button
                  type="button"
                  onClick={() => setScenario("PASS")}
                  className={`rounded px-2.5 py-1 text-xs font-semibold transition-colors ${
                    scenario === "PASS"
                      ? "bg-compliance-pass/20 text-compliance-pass border border-compliance-pass/40"
                      : "text-muted hover:text-foreground"
                  }`}
                >
                  PASS (94%)
                </button>
                <button
                  type="button"
                  onClick={() => setScenario("WARN")}
                  className={`rounded px-2.5 py-1 text-xs font-semibold transition-colors ${
                    scenario === "WARN"
                      ? "bg-compliance-warn/20 text-compliance-warn border border-compliance-warn/40"
                      : "text-muted hover:text-foreground"
                  }`}
                >
                  WARN (72%)
                </button>
                <button
                  type="button"
                  onClick={() => setScenario("FAIL")}
                  className={`rounded px-2.5 py-1 text-xs font-semibold transition-colors ${
                    scenario === "FAIL"
                      ? "bg-compliance-fail/20 text-compliance-fail border border-compliance-fail/40"
                      : "text-muted hover:text-foreground"
                  }`}
                >
                  FAIL (58%)
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error Banner when Audit Query Fails */}
      {error && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg bg-red-950/40 p-4 border border-red-500/40 text-red-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="font-semibold text-sm">Failed to Load Audit Findings</h4>
              <p className="text-xs text-red-300 leading-relaxed">{error}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-auto font-mono text-xs">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchLiveAudit(activeReport.audit_id)}
              className="border-red-500/40 text-red-200 hover:bg-red-950"
            >
              Try Again
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={() => router.push("/")}
              className="font-mono text-xs"
            >
              Start New Audit
            </Button>
          </div>
        </div>
      )}

      {/* Loading State Spinner */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-24 space-y-4 rounded-xl border border-border bg-surface shadow-md">
          <Loader2 className="h-8 w-8 animate-spin text-accent" />
          <div className="space-y-1 text-center font-mono">
            <p className="text-sm font-semibold text-foreground">
              Retrieving Reconciled Statutory Findings...
            </p>
            <p className="text-xs text-muted">
              Querying organization-scoped audit records and tamper-evident state hash.
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Primary Compliance Gauge and Domain Breakdown */}
          <ComplianceGauge
            score={activeReport.compliance_score}
            band={activeReport.compliance_band}
            stateHash={activeReport.state_hash}
            criticalCount={activeReport.critical_count}
            domainScores={activeReport.domain_scores}
          />

          {/* Findings Table Section */}
          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="text-lg font-bold font-mono tracking-tight text-foreground">
                  Statutory Compliance Findings ({activeReport.findings.length})
                </h3>
                <p className="text-xs text-muted">
                  Reconciled discrepancies between policy claims and technical observations.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => setIsReportModalOpen(true)}
                  className="flex items-center gap-1.5 font-mono text-xs bg-accent text-white"
                >
                  <FileText className="h-3.5 w-3.5" />
                  <span>Download PDF Report</span>
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExportJson}
                  className="flex items-center gap-1.5 font-mono text-xs"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Export JSON</span>
                </Button>
              </div>
            </div>

            <FindingsTable findings={activeReport.findings} />
          </div>
        </>
      )}

      {/* AI Statutory Audit Report Modal / Printable View */}
      <StatutoryReportModal
        report={activeReport}
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
      />
    </div>
  );
}
