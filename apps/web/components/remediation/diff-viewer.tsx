"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { Copy, Check, FileCode } from "lucide-react";

interface DiffViewerProps {
  filePath?: string;
  diffContent: string;
  status?: string;
  className?: string;
}

export function DiffViewer({
  filePath = "apps/api/controllers/user_controller.py",
  diffContent,
  status = "PENDING_REVIEW",
  className,
}: DiffViewerProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(diffContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = React.useMemo(() => {
    return diffContent.split("\n");
  }, [diffContent]);

  const getLineStyle = (line: string) => {
    if (line.startsWith("+") && !line.startsWith("+++")) {
      return "bg-emerald-950/40 text-emerald-300 border-l-2 border-emerald-500";
    }
    if (line.startsWith("-") && !line.startsWith("---")) {
      return "bg-red-950/40 text-red-300 border-l-2 border-red-500";
    }
    if (line.startsWith("@@")) {
      return "bg-sky-950/30 text-sky-300 font-bold border-l-2 border-sky-500/40";
    }
    if (line.startsWith("diff --git") || line.startsWith("---") || line.startsWith("+++")) {
      return "bg-surface-raised text-muted font-semibold";
    }
    return "text-foreground/80";
  };

  const getStatusBadgeVariant = (s: string) => {
    switch (s) {
      case "APPLIED":
        return "pass" as const;
      case "REJECTED":
        return "fail" as const;
      case "PENDING_REVIEW":
      default:
        return "warn" as const;
    }
  };

  return (
    <div
      className={`rounded-lg border border-border bg-[#0d1117] font-mono text-xs overflow-hidden shadow-inner ${
        className || ""
      }`}
    >
      {/* Diff Header */}
      <div className="flex items-center justify-between border-b border-border/80 bg-surface-raised px-4 py-2.5">
        <div className="flex items-center gap-2 overflow-hidden">
          <FileCode className="h-4 w-4 text-accent shrink-0" />
          <span className="font-semibold text-foreground truncate">{filePath}</span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Badge variant={getStatusBadgeVariant(status)} className="text-[10px] px-2 py-0.5">
            {status}
          </Badge>

          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1 rounded bg-surface px-2 py-1 text-[11px] text-muted hover:text-foreground transition-colors border border-border"
            title="Copy diff to clipboard"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                <span>Copy Diff</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Diff Line-by-Line Viewer */}
      <div className="overflow-x-auto max-h-[380px] p-3 text-[12px] leading-relaxed select-text space-y-0.5 font-mono">
        {lines.map((line, idx) => (
          <div
            key={idx}
            className={`flex items-start px-2 py-0.5 rounded-sm transition-colors ${getLineStyle(
              line
            )}`}
          >
            <span className="w-8 shrink-0 text-right pr-3 select-none text-[10px] text-muted/60">
              {idx + 1}
            </span>
            <span className="whitespace-pre font-mono flex-1">{line || " "}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
