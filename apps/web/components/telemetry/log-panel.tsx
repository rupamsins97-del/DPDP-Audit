"use client";

import * as React from "react";
import { TelemetryLogEntry } from "@/lib/types/telemetry";
import { AgentBadge } from "@/components/telemetry/agent-badge";
import { cn } from "@/lib/utils";
import {
  ArrowDownCircle,
  Terminal,
  Compass,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Info,
  ChevronRight,
} from "lucide-react";

interface LogPanelProps {
  title: string;
  subtitle?: string;
  iconType: "browser" | "terminal";
  logs: TelemetryLogEntry[];
  emptyMessage?: string;
  className?: string;
}

export function LogPanel({
  title,
  subtitle,
  iconType,
  logs,
  emptyMessage = "Awaiting execution telemetry...",
  className,
}: LogPanelProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [isAutoScrollPaused, setIsAutoScrollPaused] = React.useState(false);
  const isAutoScrollPausedRef = React.useRef(isAutoScrollPaused);
  isAutoScrollPausedRef.current = isAutoScrollPaused;

  const SCROLL_THRESHOLD_PX = 32;

  // Handle scroll events to detect user manual scroll-up
  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;

    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    if (distanceFromBottom > SCROLL_THRESHOLD_PX) {
      if (!isAutoScrollPausedRef.current) {
        setIsAutoScrollPaused(true);
      }
    } else {
      if (isAutoScrollPausedRef.current) {
        setIsAutoScrollPaused(false);
      }
    }
  };

  // Auto-scroll on new logs if not paused
  React.useEffect(() => {
    if (isAutoScrollPaused) return;
    const el = containerRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [logs, isAutoScrollPaused]);

  // Jump to bottom handler
  const scrollToBottom = () => {
    const el = containerRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
      setIsAutoScrollPaused(false);
    }
  };

  const getLevelIcon = (level: TelemetryLogEntry["level"]) => {
    switch (level) {
      case "error":
        return <AlertCircle className="h-3.5 w-3.5 text-red-400 shrink-0 mt-0.5" />;
      case "warn":
        return <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0 mt-0.5" />;
      case "success":
        return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />;
      case "action":
        return <ChevronRight className="h-3.5 w-3.5 text-sky-400 shrink-0 mt-0.5" />;
      default:
        return <Info className="h-3.5 w-3.5 text-muted shrink-0 mt-0.5" />;
    }
  };

  const getLevelStyles = (level: TelemetryLogEntry["level"]) => {
    switch (level) {
      case "error":
        return "bg-red-500/10 text-red-300 border-l-2 border-red-500 font-medium";
      case "warn":
        return "bg-amber-500/10 text-amber-200 border-l-2 border-amber-500";
      case "success":
        return "bg-emerald-500/10 text-emerald-300 border-l-2 border-emerald-500";
      case "action":
        return "text-sky-200";
      default:
        return "text-foreground/90";
    }
  };

  return (
    <div
      className={cn(
        "relative flex flex-col rounded-lg border border-border bg-surface shadow-lg overflow-hidden h-full min-h-[400px]",
        className
      )}
    >
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-border bg-surface-raised px-4 py-3 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="rounded p-1.5 bg-surface text-muted border border-border">
            {iconType === "browser" ? (
              <Compass className="h-4 w-4 text-sky-400" />
            ) : (
              <Terminal className="h-4 w-4 text-emerald-400" />
            )}
          </div>
          <div>
            <h3 className="font-mono text-sm font-semibold text-foreground tracking-tight flex items-center gap-2">
              <span>{title}</span>
              <span className="rounded bg-surface px-2 py-0.5 text-[10px] text-muted border border-border">
                {logs.length} events
              </span>
            </h3>
            {subtitle && <p className="text-[11px] text-muted font-mono">{subtitle}</p>}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-muted">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                isAutoScrollPaused ? "bg-amber-400" : "bg-emerald-400 animate-pulse"
              )}
            />
            <span>{isAutoScrollPaused ? "Scroll Paused" : "Live Streaming"}</span>
          </div>
        </div>
      </div>

      {/* Log Output Stream Container */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-2 select-text"
      >
        {logs.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center p-8 text-muted">
            <div className="rounded-full bg-surface-raised p-3 mb-2 border border-border">
              {iconType === "browser" ? (
                <Compass className="h-6 w-6 text-muted" />
              ) : (
                <Terminal className="h-6 w-6 text-muted" />
              )}
            </div>
            <p className="text-xs font-medium text-foreground">{emptyMessage}</p>
            <p className="text-[11px] text-muted mt-1">
              Events will appear as worker agents execute tasks in real time.
            </p>
          </div>
        ) : (
          logs.map((log, idx) => (
            <div
              key={log.id || `log-${idx}`}
              className={cn(
                "rounded p-2 transition-colors flex flex-col gap-1 border border-transparent hover:border-border/60 hover:bg-surface-raised/40",
                getLevelStyles(log.level)
              )}
            >
              <div className="flex items-center justify-between gap-2 text-[11px] text-muted">
                <div className="flex items-center gap-2">
                  {getLevelIcon(log.level)}
                  <AgentBadge agent={log.agent} />
                </div>
                <span className="text-[10px] font-mono text-muted shrink-0">
                  {log.timestamp}
                </span>
              </div>

              <div className="pl-5 text-xs whitespace-pre-wrap break-words leading-relaxed">
                {log.message}
              </div>

              {log.details && (
                <div className="pl-5 text-[11px] text-muted whitespace-pre-wrap break-words border-l border-border/50 ml-2 mt-0.5 pl-2 italic">
                  {log.details}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Floating Resume Auto-Scroll Pill */}
      {isAutoScrollPaused && (
        <button
          type="button"
          onClick={scrollToBottom}
          className="absolute bottom-4 left-1/2 -translate-x-1/2 inline-flex items-center gap-1.5 rounded-full bg-accent px-3 py-1 text-xs font-mono font-medium text-white shadow-lg transition-transform hover:scale-105 active:scale-95"
        >
          <ArrowDownCircle className="h-3.5 w-3.5" />
          <span>Auto-scroll paused • Jump to latest</span>
        </button>
      )}
    </div>
  );
}
