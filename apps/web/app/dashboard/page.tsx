import * as React from "react";
import { Header } from "@/components/layout/header";
import { ReconciliationDashboard } from "@/components/dashboard/reconciliation-dashboard";
import { Loader2 } from "lucide-react";

export const metadata = {
  title: "Reconciliation Dashboard | DPDP 360° Auditor",
  description: "Reconciliation Dashboard and DPDP Compliance Index with grounded statutory findings table.",
};

function DashboardFallback() {
  return (
    <div className="flex flex-col items-center justify-center py-24 space-y-4 rounded-xl border border-border bg-surface shadow-md w-full max-w-7xl mx-auto">
      <Loader2 className="h-8 w-8 animate-spin text-accent" />
      <p className="text-sm font-mono text-muted">Loading 360° Reconciliation Dashboard...</p>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <Header />
      <main className="flex flex-1 flex-col p-4 sm:p-6 lg:p-8">
        <React.Suspense fallback={<DashboardFallback />}>
          <ReconciliationDashboard />
        </React.Suspense>
      </main>
    </div>
  );
}
