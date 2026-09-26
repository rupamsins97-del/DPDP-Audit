"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { TelemetryWorkspace } from "@/components/telemetry/telemetry-workspace";
import { Loader2 } from "lucide-react";

function TelemetryContent() {
  const searchParams = useSearchParams();
  const auditId = searchParams.get("audit_id") || undefined;
  const targetUrl = searchParams.get("target_url") || "https://target-app.example.com";

  return <TelemetryWorkspace auditId={auditId} targetUrl={targetUrl} />;
}

export default function TelemetryPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <Header />
      <main className="flex flex-1 flex-col p-4 sm:p-6 lg:p-8">
        <React.Suspense
          fallback={
            <div className="flex h-96 items-center justify-center text-muted font-mono text-xs gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-accent" />
              <span>Loading telemetry session...</span>
            </div>
          }
        >
          <TelemetryContent />
        </React.Suspense>
      </main>
    </div>
  );
}
