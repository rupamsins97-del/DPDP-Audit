import * as React from "react";
import Link from "next/link";
import { ShieldCheck, Scale, Terminal, SlidersHorizontal, LayoutDashboard } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-surface/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3 group transition-opacity hover:opacity-90">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10 border border-accent/20 text-accent shadow-sm group-hover:bg-accent/20 transition-colors">
            <ShieldCheck className="h-5 w-5 text-accent" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-foreground tracking-tight text-base">
                DPDP 360°
              </span>
              <span className="rounded bg-surface-raised px-1.5 py-0.5 text-[10px] font-mono font-medium text-muted border border-border">
                AI Compliance Auditor
              </span>
            </div>
            <p className="text-[11px] text-muted hidden sm:block">
              Statutory verification for India&apos;s DPDP Act, 2023 &amp; Rules, 2025
            </p>
          </div>
        </Link>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-2">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-mono text-muted hover:text-foreground hover:bg-surface-raised transition-colors"
          >
            <SlidersHorizontal className="h-3.5 w-3.5 text-accent" />
            <span className="hidden sm:inline">Configuration</span>
          </Link>

          <Link
            href="/telemetry"
            className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-mono text-muted hover:text-foreground hover:bg-surface-raised transition-colors"
          >
            <Terminal className="h-3.5 w-3.5 text-emerald-400" />
            <span>Telemetry</span>
          </Link>

          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-mono text-muted hover:text-foreground hover:bg-surface-raised transition-colors"
          >
            <LayoutDashboard className="h-3.5 w-3.5 text-sky-400" />
            <span>Dashboard</span>
          </Link>

          <Link
            href="/login"
            className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface-raised px-2.5 py-1.5 text-xs font-mono text-foreground hover:bg-accent/10 hover:border-accent transition-colors ml-1"
          >
            <span>Account</span>
          </Link>

          <div className="hidden md:inline-flex items-center gap-1.5 rounded-full bg-surface-raised px-3 py-1 text-xs font-mono text-muted border border-border ml-2">
            <Scale className="h-3.5 w-3.5 text-accent" />
            <span className="text-foreground font-medium">DPDP Act 2023</span>
          </div>
        </nav>
      </div>
    </header>
  );
}
