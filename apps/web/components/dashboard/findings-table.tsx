"use client";

import * as React from "react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AgentBadge } from "@/components/telemetry/agent-badge";
import { FindingActionModal } from "@/components/dashboard/finding-action-modal";
import {
  AuditFindingItem,
  FindingSeverity,
} from "@/lib/types/dashboard";
import {
  ArrowUpDown,
  Search,
  Scale,
  ExternalLink,
  Globe,
  FileCode,
  Database,
  Download,
  ShieldAlert,
} from "lucide-react";

interface FindingsTableProps {
  findings: AuditFindingItem[];
  className?: string;
}

type SortField = "severity" | "title" | "act_section";
type SortDirection = "asc" | "desc";

const SEVERITY_ORDER: Record<FindingSeverity, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
};

export function FindingsTable({ findings, className }: FindingsTableProps) {
  const [activeFinding, setActiveFinding] = React.useState<AuditFindingItem | null>(null);
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [patchStatuses, setPatchStatuses] = React.useState<Record<string, string>>({});

  const [sortField, setSortField] = React.useState<SortField>("severity");
  const [sortDirection, setSortDirection] = React.useState<SortDirection>("asc");
  const [severityFilter, setSeverityFilter] = React.useState<FindingSeverity | "ALL">("ALL");
  const [searchQuery, setSearchQuery] = React.useState("");

  const handlePatchStatusChange = (findingId: string, newStatus: string) => {
    setPatchStatuses((prev) => ({ ...prev, [findingId]: newStatus }));
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const filteredAndSortedFindings = React.useMemo(() => {
    return [...findings]
      .filter((item) => {
        if (severityFilter !== "ALL" && item.severity !== severityFilter) {
          return false;
        }
        if (searchQuery.trim() !== "") {
          const q = searchQuery.toLowerCase();
          const matchTitle = item.title.toLowerCase().includes(q);
          const matchSection = item.act_section.toLowerCase().includes(q);
          const matchDesc = item.description.toLowerCase().includes(q);
          return matchTitle || matchSection || matchDesc;
        }
        return true;
      })
      .sort((a, b) => {
        let comp = 0;
        if (sortField === "severity") {
          comp = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
        } else if (sortField === "title") {
          comp = a.title.localeCompare(b.title);
        } else if (sortField === "act_section") {
          comp = a.act_section.localeCompare(b.act_section);
        }
        return sortDirection === "asc" ? comp : -comp;
      });
  }, [findings, severityFilter, searchQuery, sortField, sortDirection]);

  const handleOpenAction = (finding: AuditFindingItem) => {
    setActiveFinding(finding);
    setIsModalOpen(true);
  };

  const getActionIcon = (actionType: AuditFindingItem["action_type"], findingId?: string) => {
    if (findingId && patchStatuses[findingId] === "APPLIED") {
      return <FileCode className="h-3.5 w-3.5 text-emerald-400" />;
    }
    if (findingId && patchStatuses[findingId] === "REJECTED") {
      return <FileCode className="h-3.5 w-3.5 text-red-400" />;
    }

    switch (actionType) {
      case "VIEW_TRACE":
        return <Globe className="h-3.5 w-3.5 text-sky-400" />;
      case "APPLY_PATCH":
        return <FileCode className="h-3.5 w-3.5 text-emerald-400" />;
      case "GENERATE_SCRIPT":
        return <Database className="h-3.5 w-3.5 text-amber-400" />;
      case "DOWNLOAD_CLAUSE":
        return <Download className="h-3.5 w-3.5 text-purple-400" />;
      default:
        return <ExternalLink className="h-3.5 w-3.5 text-accent" />;
    }
  };

  const getSeverityBadgeVariant = (s: FindingSeverity) => {
    switch (s) {
      case "CRITICAL":
        return "critical" as const;
      case "HIGH":
        return "high" as const;
      case "MEDIUM":
        return "medium" as const;
      case "LOW":
      default:
        return "low" as const;
    }
  };

  return (
    <div className={`space-y-3 ${className || ""}`}>
      {/* Table Toolbar / Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        {/* Severity Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 font-mono text-xs">
          <button
            type="button"
            onClick={() => setSeverityFilter("ALL")}
            className={`rounded-md px-2.5 py-1 transition-colors border ${
              severityFilter === "ALL"
                ? "bg-accent text-white border-accent font-semibold"
                : "bg-surface text-muted border-border hover:bg-surface-raised"
            }`}
          >
            All ({findings.length})
          </button>
          {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as FindingSeverity[]).map((sev) => {
            const count = findings.filter((f) => f.severity === sev).length;
            if (count === 0) return null;
            return (
              <button
                key={sev}
                type="button"
                onClick={() => setSeverityFilter(sev)}
                className={`rounded-md px-2.5 py-1 transition-colors border ${
                  severityFilter === sev
                    ? "bg-surface-raised text-foreground border-accent font-semibold"
                    : "bg-surface text-muted border-border hover:bg-surface-raised"
                }`}
              >
                {sev} ({count})
              </button>
            );
          })}
        </div>

        {/* Search Filter */}
        <div className="relative w-full sm:w-64">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
          <input
            type="text"
            placeholder="Search findings or section..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 w-full rounded-md border border-border bg-surface-raised pl-8 pr-3 text-xs font-mono text-foreground placeholder:text-muted focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
          />
        </div>
      </div>

      {/* Styled Findings Table */}
      <div className="rounded-lg border border-border bg-surface shadow-md overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[45%]">
                <button
                  type="button"
                  onClick={() => handleSort("title")}
                  className="flex items-center gap-1.5 font-mono text-xs hover:text-foreground transition-colors"
                >
                  <span>Violation Title</span>
                  <ArrowUpDown className="h-3 w-3" />
                </button>
              </TableHead>

              <TableHead className="w-[15%]">
                <button
                  type="button"
                  onClick={() => handleSort("severity")}
                  className="flex items-center gap-1.5 font-mono text-xs hover:text-foreground transition-colors"
                >
                  <span>Severity</span>
                  <ArrowUpDown className="h-3 w-3" />
                </button>
              </TableHead>

              <TableHead className="w-[20%]">
                <button
                  type="button"
                  onClick={() => handleSort("act_section")}
                  className="flex items-center gap-1.5 font-mono text-xs hover:text-foreground transition-colors"
                >
                  <span>Section</span>
                  <ArrowUpDown className="h-3 w-3" />
                </button>
              </TableHead>

              <TableHead className="w-[20%] text-right font-mono text-xs">
                Action
              </TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {findings.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="py-12 text-center">
                  <div className="flex flex-col items-center justify-center space-y-3 max-w-md mx-auto">
                    <div className="rounded-full bg-emerald-500/10 p-3 border border-emerald-500/30 text-emerald-400">
                      <ShieldAlert className="h-8 w-8 text-emerald-400" />
                    </div>
                    <div className="space-y-1">
                      <h4 className="font-semibold text-sm font-mono text-foreground">
                        Zero Statutory Violations Detected
                      </h4>
                      <p className="text-xs text-muted leading-relaxed">
                        All statutory domains (Frontend Consent, Backend Plaintext Logging, DPA Alignment, Child Safety VPC, 72h Webhooks, and DPR SLAs) are fully compliant under the DPDP Act, 2023 &amp; Rules, 2025.
                      </p>
                    </div>
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-mono font-medium text-emerald-400 border border-emerald-500/30">
                      100% Statutory Compliance
                    </span>
                  </div>
                </TableCell>
              </TableRow>
            ) : filteredAndSortedFindings.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="h-32 text-center text-muted font-mono text-xs">
                  No compliance findings matched the active filter or search query.
                </TableCell>
              </TableRow>
            ) : (
              filteredAndSortedFindings.map((finding) => {
                const currentStatus = patchStatuses[finding.id];
                const actionLabel =
                  currentStatus === "APPLIED"
                    ? "Applied ✓"
                    : currentStatus === "REJECTED"
                    ? "Rejected ✕"
                    : finding.action_label;

                return (
                  <TableRow key={finding.id} className="hover:bg-surface-raised/60">
                    {/* Column 1: Violation Title */}
                    <TableCell className="align-top py-3.5">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-foreground text-sm">
                            {finding.title}
                          </span>
                          <AgentBadge agent={finding.agent_role} showDotOnly />
                        </div>
                        <p className="text-xs text-muted leading-relaxed line-clamp-2">
                          {finding.description}
                        </p>
                      </div>
                    </TableCell>

                    {/* Column 2: Severity */}
                    <TableCell className="align-top py-3.5">
                      <Badge variant={getSeverityBadgeVariant(finding.severity)}>
                        {finding.severity}
                      </Badge>
                    </TableCell>

                    {/* Column 3: Section */}
                    <TableCell className="align-top py-3.5">
                      <div className="inline-flex items-center gap-1.5 rounded bg-surface-raised px-2 py-1 text-xs font-mono text-muted border border-border">
                        <Scale className="h-3 w-3 text-accent shrink-0" />
                        <span className="text-foreground font-medium">{finding.act_section}</span>
                      </div>
                    </TableCell>

                    {/* Column 4: Action */}
                    <TableCell className="align-top py-3.5 text-right">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenAction(finding)}
                        className={`inline-flex items-center gap-1.5 font-mono text-xs border-border bg-surface-raised hover:bg-surface hover:text-accent hover:border-accent/40 ${
                          currentStatus === "APPLIED"
                            ? "border-emerald-500/40 text-emerald-400 bg-emerald-950/20"
                            : currentStatus === "REJECTED"
                            ? "border-red-500/40 text-red-400 bg-red-950/20"
                            : ""
                        }`}
                      >
                        {getActionIcon(finding.action_type, finding.id)}
                        <span>{actionLabel}</span>
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* Action Modal Dialog */}
      <FindingActionModal
        finding={activeFinding}
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        onPatchStatusChange={handlePatchStatusChange}
      />
    </div>
  );
}
