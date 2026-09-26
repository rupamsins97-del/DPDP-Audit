"use client";

import * as React from "react";
import { createClient } from "@/lib/supabase/client";
import {
  AgentRole,
  TelemetryLogEntry,
  TelemetryLogLevel,
  TelemetryPanel,
  TelemetryStreamState,
} from "@/lib/types/telemetry";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const MOCK_FALLBACK_LOGS: Array<{
  agent: AgentRole;
  panel: TelemetryPanel;
  level: TelemetryLogLevel;
  message: string;
  details?: string;
}> = [
  {
    agent: "synthesis_agent",
    panel: "terminal",
    level: "info",
    message: "[synthesis_agent] Initializing DPDP 360° multi-agent audit orchestrator...",
    details: "Framework: DPDP Act, 2023 & DPDP Rules, 2025. Dispatching LangGraph StateGraph DAG.",
  },
  {
    agent: "policy_agent",
    panel: "terminal",
    level: "info",
    message: "[policy_agent] Ingesting Privacy Policy & DPA in-memory stream...",
    details: "Parsing legal PDF text chunks with zero persistent storage (Invariant 2).",
  },
  {
    agent: "frontend_agent",
    panel: "browser",
    level: "info",
    message: "[Stagehand + Scrapfly CDP] Launching headless browser with stealth proxy...",
    details: "Attaching CDP Network.requestWillBeSent pre-consent interception hook.",
  },
  {
    agent: "frontend_agent",
    panel: "browser",
    level: "error",
    message: "⚠️ PRE-CONSENT VIOLATION: Intercepted third-party request to connect.facebook.net before consent modal!",
    details: "Target: https://connect.facebook.net/en_US/fbevents.js. DPDP Act Sec 6(1).",
  },
  {
    agent: "backend_agent",
    panel: "terminal",
    level: "error",
    message: "⚠️ PLAINTEXT PII LOGGING DETECTED: Line 14 logger.info('User KYC: aadhaar=%s')",
    details: "Semgrep match on dpdp.pii.plaintext_logger rule. DPDP Act Sec 8(5).",
  },
  {
    agent: "synthesis_agent",
    panel: "terminal",
    level: "error",
    message: "🚨 STATUTORY MISREPRESENTATION: Policy claim 'No sharing' contradicted by pre-consent Meta Pixel!",
    details: "Escalated to CRITICAL Statutory Misrepresentation under DPDP Act Section 6(1) / Rule 3(2).",
  },
  {
    agent: "synthesis_agent",
    panel: "terminal",
    level: "success",
    message: "[synthesis_agent] Audit synthesis completed. Status: COMPLETED, Index: 58% [FAIL]",
    details: "Generated canonical SHA-256 state hash for immutable audit trail (NFR-3).",
  },
];

export interface UseTelemetryStreamOptions {
  auditId?: string;
  autoStart?: boolean;
  speedMs?: number;
  onComplete?: (auditId: string) => void;
}

export interface ExtendedTelemetryStreamState extends TelemetryStreamState {
  isReconnecting: boolean;
  finalComplianceScore?: number;
  stateHash?: string;
}

export function useTelemetryStream({
  auditId,
  autoStart = true,
  speedMs = 1200,
  onComplete,
}: UseTelemetryStreamOptions = {}): ExtendedTelemetryStreamState {
  const [logs, setLogs] = React.useState<TelemetryLogEntry[]>([]);
  const [isStreaming, setIsStreaming] = React.useState<boolean>(autoStart);
  const [isConnected, setIsConnected] = React.useState<boolean>(false);
  const [isReconnecting, setIsReconnecting] = React.useState<boolean>(false);
  const [isCompleted, setIsCompleted] = React.useState<boolean>(false);
  const [finalComplianceScore, setFinalComplianceScore] = React.useState<number | undefined>(undefined);
  const [stateHash, setStateHash] = React.useState<string | undefined>(undefined);

  const eventSourceRef = React.useRef<EventSource | null>(null);
  const mockIndexRef = React.useRef<number>(0);
  const retryTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  const formatTimestamp = (date: Date): string => {
    const pad = (n: number) => n.toString().padStart(2, "0");
    const ms = date.getMilliseconds().toString().padStart(3, "0");
    return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${ms}`;
  };

  // Helper to map incoming backend agent_role to panel and defaults
  const mapAgentToPanel = (agent: AgentRole): TelemetryPanel => {
    if (agent === "frontend_agent") return "browser";
    return "terminal";
  };

  // Real SSE Stream Connection
  React.useEffect(() => {
    if (!auditId) {
      // Fallback to local mock stream if no auditId provided
      if (!isStreaming) return;
      const interval = setInterval(() => {
        if (mockIndexRef.current >= MOCK_FALLBACK_LOGS.length) {
          setIsStreaming(false);
          setIsCompleted(true);
          return;
        }
        const item = MOCK_FALLBACK_LOGS[mockIndexRef.current];
        const newEntry: TelemetryLogEntry = {
          id: `mock-log-${Date.now()}-${mockIndexRef.current}`,
          timestamp: formatTimestamp(new Date()),
          agent: item.agent,
          panel: item.panel,
          level: item.level,
          message: item.message,
          details: item.details,
        };
        setLogs((prev) => [...prev, newEntry]);
        mockIndexRef.current += 1;
      }, speedMs);

      setIsConnected(true);
      return () => clearInterval(interval);
    }

    // Connect to real SSE stream
    let isCancelled = false;

    const connectSSE = async () => {
      try {
        const supabase = createClient();
        const {
          data: { session },
        } = await supabase.auth.getSession();

        const tokenParam = session?.access_token
          ? `?token=${encodeURIComponent(session.access_token)}`
          : "?token=demo-auditor-token";
        const sseUrl = `${API_BASE_URL}/audits/${auditId}/stream${tokenParam}`;


        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }

        const es = new EventSource(sseUrl);
        eventSourceRef.current = es;

        es.onopen = () => {
          if (isCancelled) return;
          setIsConnected(true);
          setIsReconnecting(false);
          setIsStreaming(true);
        };

        // Handle telemetry events
        es.addEventListener("telemetry", (event: MessageEvent) => {
          if (isCancelled) return;
          try {
            const data = JSON.parse(event.data);
            const agentRole: AgentRole = data.agent_role || "synthesis_agent";
            const panel: TelemetryPanel = data.panel || mapAgentToPanel(agentRole);
            const level: TelemetryLogLevel = data.level || "info";

            const newEntry: TelemetryLogEntry = {
              id: data.id || `telemetry-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
              timestamp: data.timestamp ? formatTimestamp(new Date(data.timestamp)) : formatTimestamp(new Date()),
              agent: agentRole,
              panel,
              level,
              message: data.message || "",
              details: data.details,
              metadata: data.metadata,
            };

            setLogs((prev) => [...prev, newEntry]);
          } catch (e) {
            console.error("Failed to parse telemetry event frame:", e);
          }
        });

        // Handle status update / terminal events
        es.addEventListener("status", (event: MessageEvent) => {
          if (isCancelled) return;
          try {
            const data = JSON.parse(event.data);
            if (data.compliance_score !== undefined) {
              setFinalComplianceScore(data.compliance_score);
            }
            if (data.state_hash) {
              setStateHash(data.state_hash);
            }

            if (data.status === "COMPLETED" || data.status === "FAILED") {
              setIsStreaming(false);
              setIsCompleted(true);
              es.close();
              if (onComplete) {
                onComplete(auditId);
              }
            }
          } catch (e) {
            console.error("Failed to parse status event frame:", e);
          }
        });

        // Handle ping
        es.addEventListener("ping", () => {
          if (!isCancelled) {
            setIsConnected(true);
          }
        });

        es.onerror = () => {
          if (isCancelled) return;
          setIsConnected(false);
          setIsReconnecting(true);
          es.close();

          // Attempt reconnect after 3 seconds without losing existing logs buffer
          retryTimeoutRef.current = setTimeout(() => {
            if (!isCancelled && !isCompleted) {
              connectSSE();
            }
          }, 3000);
        };
      } catch (err) {
        console.error("Error setting up EventSource connection:", err);
        setIsReconnecting(true);
      }
    };

    connectSSE();

    return () => {
      isCancelled = true;
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [auditId, isStreaming, speedMs, onComplete, isCompleted]);

  const browserLogs = React.useMemo(
    () => logs.filter((log) => log.panel === "browser"),
    [logs]
  );

  const terminalLogs = React.useMemo(
    () => logs.filter((log) => log.panel === "terminal"),
    [logs]
  );

  const activeAgents = React.useMemo(() => {
    const set = new Set<AgentRole>();
    logs.forEach((log) => set.add(log.agent));
    return Array.from(set);
  }, [logs]);

  const pauseStream = () => setIsStreaming(false);
  const resumeStream = () => setIsStreaming(true);
  const clearLogs = () => {
    setLogs([]);
    mockIndexRef.current = 0;
    setIsCompleted(false);
  };

  return {
    logs,
    browserLogs,
    terminalLogs,
    isConnected,
    isReconnecting,
    isStreaming,
    isCompleted,
    finalComplianceScore,
    stateHash,
    activeAgents,
    pauseStream,
    resumeStream,
    clearLogs,
  };
}
