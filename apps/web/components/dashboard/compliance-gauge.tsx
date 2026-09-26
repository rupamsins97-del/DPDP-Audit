import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { ComplianceBand, DomainScoreItem } from "@/lib/types/dashboard";
import { cn } from "@/lib/utils";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Lock,
  Hash,
  Activity,
  Layers,
} from "lucide-react";

interface ComplianceGaugeProps {
  score: number;
  band: ComplianceBand;
  stateHash: string;
  criticalCount: number;
  domainScores: DomainScoreItem[];
  className?: string;
}

export function ComplianceGauge({
  score,
  band,
  stateHash,
  criticalCount,
  domainScores,
  className,
}: ComplianceGaugeProps) {
  const getBandConfig = (b: ComplianceBand) => {
    switch (b) {
      case "PASS":
        return {
          label: "PASS",
          badgeVariant: "pass" as const,
          textColor: "text-compliance-pass",
          bgColor: "bg-compliance-pass/10",
          borderColor: "border-compliance-pass/30",
          icon: <ShieldCheck className="h-6 w-6 text-compliance-pass" />,
          summary: "Statutory requirements satisfied. All high-risk thresholds met.",
        };
      case "WARN":
        return {
          label: "WARN",
          badgeVariant: "warn" as const,
          textColor: "text-compliance-warn",
          bgColor: "bg-compliance-warn/10",
          borderColor: "border-compliance-warn/30",
          icon: <AlertTriangle className="h-6 w-6 text-compliance-warn" />,
          summary: "Moderate statutory compliance risks detected. Remediation recommended.",
        };
      case "FAIL":
      default:
        return {
          label: "FAIL",
          badgeVariant: "fail" as const,
          textColor: "text-compliance-fail",
          bgColor: "bg-compliance-fail/10",
          borderColor: "border-compliance-fail/30",
          icon: <ShieldAlert className="h-6 w-6 text-compliance-fail" />,
          summary: "Critical statutory non-compliance detected. Mandatory Zero-Tolerance Cap active.",
        };
    }
  };

  const config = getBandConfig(band);

  return (
    <div className={cn("space-y-4", className)}>
      {/* Primary Compliance Gauge Banner */}
      <div
        className={cn(
          "rounded-xl border p-6 shadow-xl transition-all",
          config.bgColor,
          config.borderColor
        )}
      >
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="rounded-xl bg-surface p-3 border border-border shrink-0 shadow-inner">
              {config.icon}
            </div>
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-foreground">
                  Overall DPDP Compliance Index:{" "}
                  <span className={config.textColor}>{score}%</span>
                </h2>
                <Badge variant={config.badgeVariant} className="text-xs px-2.5 py-1">
                  [{config.label}]
                </Badge>
              </div>
              <p className="text-xs text-muted leading-relaxed max-w-2xl">
                {config.summary}
              </p>
            </div>
          </div>

          {/* Tamper-evident State Hash (NFR-3) */}
          <div className="flex flex-col items-start md:items-end justify-center rounded-lg bg-surface/80 p-3.5 border border-border shrink-0 font-mono">
            <div className="flex items-center gap-1.5 text-[11px] text-muted mb-1">
              <Hash className="h-3 w-3 text-accent" />
              <span className="font-semibold text-foreground">SHA-256 State Hash</span>
              <span className="rounded bg-surface-raised px-1 py-0.2 text-[9px] text-accent border border-accent/20">
                NFR-3
              </span>
            </div>
            <span
              className="text-[11px] text-muted select-all hover:text-foreground transition-colors max-w-[200px] truncate"
              title={stateHash}
            >
              {stateHash.substring(0, 16)}...{stateHash.substring(stateHash.length - 8)}
            </span>
          </div>
        </div>

        {/* Critical Cap Warning Callout */}
        {criticalCount > 0 && score <= 59 && (
          <div className="mt-4 flex items-center gap-2 rounded-lg bg-red-950/40 p-3 border border-red-500/40 text-xs text-red-200">
            <ShieldAlert className="h-4 w-4 text-red-400 shrink-0" />
            <span>
              <strong>Zero-Tolerance Critical Cap Active:</strong> {criticalCount} CRITICAL finding(s) detected. Final Compliance Index is hard-capped at &le;59% (FAIL) under DPDP statutory rules.
            </span>
          </div>
        )}
      </div>

      {/* Domain Score Breakdown Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {domainScores.map((domain) => (
          <div
            key={domain.key}
            className="rounded-lg border border-border bg-surface p-3 space-y-1.5 shadow-sm"
          >
            <div className="flex items-center justify-between text-[11px] text-muted">
              <span className="font-mono">{(domain.weight * 100).toFixed(0)}% Weight</span>
              {domain.deductions > 0 ? (
                <span className="text-red-400 font-mono font-medium">
                  -{domain.deductions} pts
                </span>
              ) : (
                <span className="text-emerald-400 font-mono font-medium">Clean</span>
              )}
            </div>
            <p className="text-xs font-semibold text-foreground truncate" title={domain.domain}>
              {domain.domain}
            </p>
            <div className="flex items-center justify-between pt-1">
              <span className="text-base font-bold font-mono text-foreground">
                {domain.score}%
              </span>
              <span className="text-[10px] text-muted font-mono">
                {domain.findingCount} finding{domain.findingCount !== 1 ? "s" : ""}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
