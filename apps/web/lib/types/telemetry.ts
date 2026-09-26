export type AgentRole =
  | "frontend_agent"
  | "backend_agent"
  | "policy_agent"
  | "incident_management_agent"
  | "child_safety_agent"
  | "dpr_portal_agent"
  | "synthesis_agent";

export type TelemetryPanel = "browser" | "terminal";

export type TelemetryLogLevel = "info" | "warn" | "error" | "action" | "success";

export interface TelemetryLogEntry {
  id: string;
  timestamp: string;
  agent: AgentRole;
  panel: TelemetryPanel;
  level: TelemetryLogLevel;
  message: string;
  details?: string;
  metadata?: Record<string, unknown>;
}

export interface TelemetryStreamState {
  logs: TelemetryLogEntry[];
  browserLogs: TelemetryLogEntry[];
  terminalLogs: TelemetryLogEntry[];
  isConnected: boolean;
  isStreaming: boolean;
  isCompleted: boolean;
  activeAgents: AgentRole[];
  pauseStream: () => void;
  resumeStream: () => void;
  clearLogs: () => void;
}
