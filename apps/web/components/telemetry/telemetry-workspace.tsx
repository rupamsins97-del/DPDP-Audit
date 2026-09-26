"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { LogPanel } from "@/components/telemetry/log-panel";
import { AgentBadge } from "@/components/telemetry/agent-badge";
import { useTelemetryStream } from "@/lib/hooks/use-telemetry-stream";
import { AgentRole } from "@/lib/types/telemetry";
import { Button } from "@/components/ui/button";
import {
  Play,
  Pause,
  Trash2,
  Globe,
  Radio,
  Filter,
  CheckCircle2,
  ArrowRight,
  Wifi,
  WifiOff,
  RefreshCw,
  Scale,
} from "lucide-react";

interface TelemetryWorkspaceProps {
  auditId?: string;
  targetUrl?: string;
  className?: string;
}

export function TelemetryWorkspace({
  auditId,
  targetUrl = "https://target-app.example.com",
  className,
}: TelemetryWorkspaceProps) {
  const router = useRouter();
  const [selectedAgentFilter, setSelectedAgentFilter] = React.useState<AgentRole | "all">("all");
  const [countdown, setCountdown] = React.useState<number>(4);

  const handleComplete = React.useCallback(
    (completedAuditId: string) => {
      console.log(`[TelemetryWorkspace] Audit ${completedAuditId} finished.`);
      try {
        localStorage.setItem("dpdp_latest_audit_id", completedAuditId);
      } catch {
        // ignore
      }
    },
    []
  );

  const {
    browserLogs,
    terminalLogs,
    isStreaming,
    isConnected,
    isReconnecting,
    isCompleted,
    finalComplianceScore,
    activeAgents,
    pauseStream,
    resumeStream,
    clearLogs,
  } = useTelemetryStream({
    auditId,
    autoStart: true,
    speedMs: 1100,
    onComplete: handleComplete,
  });

  // Countdown auto-redirect to dashboard on completion
  React.useEffect(() => {
    if (!isCompleted || !auditId) return;

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          router.push(`/dashboard?audit_id=${auditId}`);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isCompleted, auditId, router]);

  const filteredBrowserLogs = React.useMemo(() => {
    if (selectedAgentFilter === "all") return browserLogs;
    return browserLogs.filter((log) => log.agent === selectedAgentFilter);
  }, [browserLogs, selectedAgentFilter]);

  const filteredTerminalLogs = React.useMemo(() => {
    if (selectedAgentFilter === "all") return terminalLogs;
    return terminalLogs.filter((log) => log.agent === selectedAgentFilter);
  }, [terminalLogs, selectedAgentFilter]);

  const handleNavigateDashboard = () => {
    if (auditId) {
      router.push(`/dashboard?audit_id=${auditId}`);
    } else {
      router.push("/dashboard");
    }
  };

  return (
    <div className={`flex flex-col h-full w-full max-w-7xl mx-auto space-y-4 ${className || ""}`}>
      {/* Reconnecting State Alert */}
      {isReconnecting && (
        <div className="flex items-center justify-between rounded-lg bg-amber-950/40 p-3.5 border border-amber-500/40 text-amber-200 text-xs font-mono animate-pulse">
          <div className="flex items-center gap-2">
            <WifiOff className="h-4 w-4 text-amber-400" />
            <span>Connection dropped. Reconnecting to live telemetry stream without losing logs...</span>
          </div>
          <RefreshCw className="h-3.5 w-3.5 animate-spin text-amber-400" />
        </div>
      )}

      {/* Audit Completion Banner */}
      {isCompleted && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg bg-emerald-950/50 p-4 border border-emerald-500/40 text-emerald-200 shadow-xl animate-in fade-in">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-emerald-500/20 p-2 text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="h-5 w-5" />
            </div>
            <div>
              <h4 className="font-semibold text-sm text-foreground">
                360° Compliance Audit Completed
              </h4>
              <p className="text-xs text-muted">
                {finalComplianceScore !== undefined
                  ? `Computed DPDP Compliance Index: ${finalComplianceScore}% • Redirecting in ${countdown}s...`
                  : `Audit run finished • Redirecting in ${countdown}s...`}
              </p>
            </div>
          </div>

          <Button
            type="button"
            variant="default"
            size="sm"
            onClick={handleNavigateDashboard}
            className="flex items-center gap-2 font-mono text-xs self-start sm:self-auto"
          >
            <span>View Reconciliation Dashboard</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}

      {/* Telemetry Control Bar */}
      <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-4 shadow-md sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              {isStreaming && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
              )}
              <span
                className={`relative inline-flex rounded-full h-3 w-3 ${
                  isStreaming
                    ? "bg-accent"
                    : isCompleted
                    ? "bg-emerald-500"
                    : isReconnecting
                    ? "bg-amber-400"
                    : "bg-muted"
                }`}
              />
            </span>
            <span className="font-mono text-xs font-semibold text-foreground tracking-tight">
              {isStreaming
                ? "REAL-TIME SSE TELEMETRY STREAM"
                : isCompleted
                ? "AUDIT COMPLETED"
                : isReconnecting
                ? "RECONNECTING..."
                : "STREAM PAUSED"}
            </span>
          </div>

          <div className="hidden md:flex items-center gap-1.5 rounded-md bg-surface-raised px-2.5 py-1 text-xs font-mono text-muted border border-border">
            <Globe className="h-3 w-3 text-accent" />
            <span className="text-foreground truncate max-w-[220px]">{targetUrl}</span>
          </div>

          {auditId && (
            <div className="hidden lg:flex items-center gap-1.5 rounded-md bg-surface-raised px-2.5 py-1 text-xs font-mono text-muted border border-border">
              <Radio className="h-3 w-3 text-emerald-400" />
              <span className="truncate max-w-[180px]">ID: {auditId}</span>
            </div>
          )}

          <div className="flex items-center gap-1 text-[11px] font-mono text-muted">
            {isConnected ? (
              <span title="Connected">
                <Wifi className="h-3 w-3 text-emerald-400" />
              </span>
            ) : (
              <span title="Disconnected">
                <WifiOff className="h-3 w-3 text-muted" />
              </span>
            )}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {isStreaming ? (
            <Button
              variant="outline"
              size="sm"
              onClick={pauseStream}
              className="flex items-center gap-1.5 font-mono text-xs"
            >
              <Pause className="h-3.5 w-3.5 text-amber-400" />
              <span>Pause</span>
            </Button>
          ) : (
            <Button
              variant="default"
              size="sm"
              onClick={resumeStream}
              className="flex items-center gap-1.5 font-mono text-xs"
            >
              <Play className="h-3.5 w-3.5 text-white" />
              <span>Resume</span>
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={clearLogs}
            className="flex items-center gap-1.5 font-mono text-xs hover:text-red-400"
            title="Clear current stream buffer"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Clear</span>
          </Button>

          {isCompleted && (
            <Button
              variant="default"
              size="sm"
              onClick={handleNavigateDashboard}
              className="flex items-center gap-1.5 font-mono text-xs"
            >
              <Scale className="h-3.5 w-3.5" />
              <span>Dashboard</span>
            </Button>
          )}
        </div>
      </div>

      {/* Active Agents Filter Bar */}
      {activeAgents.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-mono text-muted">
          <div className="flex items-center gap-1 shrink-0 text-muted">
            <Filter className="h-3 w-3" />
            <span>Filter Agent:</span>
          </div>
          <button
            type="button"
            onClick={() => setSelectedAgentFilter("all")}
            className={`rounded px-2 py-0.5 text-[11px] font-mono transition-colors border ${
              selectedAgentFilter === "all"
                ? "bg-accent text-white border-accent font-semibold"
                : "bg-surface text-muted border-border hover:bg-surface-raised"
            }`}
          >
            All Agents ({browserLogs.length + terminalLogs.length})
          </button>
          {activeAgents.map((agent) => (
            <button
              key={agent}
              type="button"
              onClick={() =>
                setSelectedAgentFilter((prev) => (prev === agent ? "all" : agent))
              }
              className={`rounded px-2 py-0.5 text-[11px] font-mono transition-colors border ${
                selectedAgentFilter === agent
                  ? "bg-accent/20 border-accent text-accent font-semibold"
                  : "bg-surface text-muted border-border hover:bg-surface-raised"
              }`}
            >
              <AgentBadge agent={agent} />
            </button>
          ))}
        </div>
      )}

      {/* Dual-Pane Side-by-Side Viewport */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 h-[calc(100vh-14rem)] min-h-[550px]">
        {/* Left Panel: Live Browser Execution */}
        <LogPanel
          title="Live Browser Execution"
          subtitle="Stagehand + Scrapfly Stealth CDP"
          iconType="browser"
          logs={filteredBrowserLogs}
          emptyMessage="Awaiting Stagehand CDP browser events..."
          className="h-full"
        />

        {/* Right Panel: Terminal & AST Agent Logs */}
        <LogPanel
          title="Terminal & AST Agent Logs"
          subtitle="backend_agent • policy_agent • domain_agents"
          iconType="terminal"
          logs={filteredTerminalLogs}
          emptyMessage="Awaiting static analysis AST & legal reasoning logs..."
          className="h-full"
        />
      </div>
    </div>
  );
}
