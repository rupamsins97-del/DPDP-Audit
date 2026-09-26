"use client";

import * as React from "react";
import Link from "next/link";
import { Header } from "@/components/layout/header";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <Header />
      <main className="flex flex-1 flex-col items-center justify-center p-6 text-center">
        <h2 className="text-2xl font-bold font-mono text-red-400 mb-2">Compliance Gateway Error</h2>
        <p className="text-xs text-muted mb-6">{error.message || "An unexpected error occurred."}</p>
        <div className="flex gap-3">
          <button
            onClick={() => reset()}
            className="rounded-md border border-border bg-surface px-4 py-2 text-xs font-mono text-foreground hover:bg-surface-raised transition-colors"
          >
            Try Again
          </button>
          <Link
            href="/"
            className="rounded-md bg-accent px-4 py-2 text-xs font-mono text-white hover:bg-accent/90 transition-colors"
          >
            Back to Home
          </Link>
        </div>
      </main>
    </div>
  );
}
