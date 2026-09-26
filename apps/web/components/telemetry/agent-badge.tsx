import * as React from "react";
import { AgentRole } from "@/lib/types/telemetry";
import { cn } from "@/lib/utils";

interface AgentBadgeProps {
  agent: AgentRole;
  className?: string;
  showDotOnly?: boolean;
}

const AGENT_CONFIG: Record<
  AgentRole,
  { label: string; dotClass: string; badgeClass: string }
> = {
  frontend_agent: {
    label: "frontend_agent",
    dotClass: "bg-sky-400",
    badgeClass: "border-sky-500/30 bg-sky-500/10 text-sky-400",
  },
  backend_agent: {
    label: "backend_agent",
    dotClass: "bg-emerald-400",
    badgeClass: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  },
  policy_agent: {
    label: "policy_agent",
    dotClass: "bg-purple-400",
    badgeClass: "border-purple-500/30 bg-purple-500/10 text-purple-400",
  },
  incident_management_agent: {
    label: "incident_mgmt",
    dotClass: "bg-orange-400",
    badgeClass: "border-orange-500/30 bg-orange-500/10 text-orange-400",
  },
  child_safety_agent: {
    label: "child_safety",
    dotClass: "bg-amber-400",
    badgeClass: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  },
  dpr_portal_agent: {
    label: "dpr_portal",
    dotClass: "bg-teal-400",
    badgeClass: "border-teal-500/30 bg-teal-500/10 text-teal-400",
  },
  synthesis_agent: {
    label: "synthesis_agent",
    dotClass: "bg-blue-400",
    badgeClass: "border-blue-500/30 bg-blue-500/10 text-blue-400",
  },
};

export function AgentBadge({ agent, className, showDotOnly = false }: AgentBadgeProps) {
  const config = AGENT_CONFIG[agent] || {
    label: agent,
    dotClass: "bg-muted",
    badgeClass: "border-border bg-surface-raised text-muted",
  };

  if (showDotOnly) {
    return (
      <span
        className={cn("inline-block h-2 w-2 rounded-full", config.dotClass, className)}
        title={config.label}
      />
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-[11px] font-mono font-medium border",
        config.badgeClass,
        className
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", config.dotClass)} />
      <span>{config.label}</span>
    </span>
  );
}
