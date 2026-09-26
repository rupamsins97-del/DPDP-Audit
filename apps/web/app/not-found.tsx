import Link from "next/link";
import { Header } from "@/components/layout/header";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <Header />
      <main className="flex flex-1 flex-col items-center justify-center p-6 text-center">
        <h2 className="text-2xl font-bold font-mono text-foreground mb-2">404 - Page Not Found</h2>
        <p className="text-xs text-muted mb-6">The requested compliance workspace route does not exist.</p>
        <Link
          href="/"
          className="rounded-md bg-accent px-4 py-2 text-xs font-mono text-white hover:bg-accent/90 transition-colors"
        >
          Return to Audit Configuration
        </Link>
      </main>
    </div>
  );
}
