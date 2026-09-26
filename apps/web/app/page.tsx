import * as React from "react";
import { Header } from "@/components/layout/header";
import { AuditConfigForm } from "@/components/audit/audit-config-form";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <Header />
      <main className="flex flex-1 flex-col items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
        <AuditConfigForm />
      </main>
    </div>
  );
}
