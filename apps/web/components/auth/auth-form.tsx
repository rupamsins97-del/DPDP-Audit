"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { ShieldCheck, Lock, Mail, Building, ArrowRight, Loader2 } from "lucide-react";

interface AuthFormProps {
  onSuccess?: () => void;
}

export function AuthForm({ onSuccess }: AuthFormProps) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [orgName, setOrgName] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const supabase = createClient();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      if (isSignUp) {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              organization_name: orgName.trim() || undefined,
            },
          },
        });
        if (error) throw error;
        setSuccessMsg("Account created! Check your email or sign in directly.");
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        setSuccessMsg("Signed in successfully.");
        if (onSuccess) onSuccess();
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto rounded-lg border border-border bg-surface p-6 shadow-xl">
      <div className="flex items-center gap-2 mb-6">
        <div className="h-8 w-8 rounded-md bg-accent/10 border border-accent/30 flex items-center justify-center text-accent">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">
            {isSignUp ? "Create Auditor Account" : "DPDP Auditor Login"}
          </h2>
          <p className="text-xs text-muted">
            {isSignUp
              ? "Register to provision your organization's compliance workspace"
              : "Sign in with your organization credentials"}
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="mb-4 rounded-md border border-severity-critical/30 bg-severity-critical/10 p-3 text-xs text-severity-critical">
          {errorMsg}
        </div>
      )}

      {successMsg && (
        <div className="mb-4 rounded-md border border-compliance-pass/30 bg-compliance-pass/10 p-3 text-xs text-compliance-pass">
          {successMsg}
        </div>
      )}

      <form onSubmit={handleAuth} className="space-y-4">
        {isSignUp && (
          <div>
            <label className="block text-xs font-medium text-muted mb-1">
              Organization / Company Name
            </label>
            <div className="relative">
              <Building className="absolute left-3 top-2.5 h-4 w-4 text-muted" />
              <input
                type="text"
                required
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                placeholder="Acme Privacy Corp"
                className="w-full rounded-md border border-border bg-surface-raised pl-9 pr-3 py-2 text-sm text-foreground placeholder:text-muted/60 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
            </div>
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-muted mb-1">Email Address</label>
          <div className="relative">
            <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="dpo@company.com"
              className="w-full rounded-md border border-border bg-surface-raised pl-9 pr-3 py-2 text-sm text-foreground placeholder:text-muted/60 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-muted mb-1">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted" />
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full rounded-md border border-border bg-surface-raised pl-9 pr-3 py-2 text-sm text-foreground placeholder:text-muted/60 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90 disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              {isSignUp ? "Sign Up & Provision Org" : "Sign In"}
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </button>
      </form>

      <div className="mt-6 pt-4 border-t border-border text-center">
        <button
          type="button"
          onClick={() => {
            setIsSignUp(!isSignUp);
            setErrorMsg(null);
            setSuccessMsg(null);
          }}
          className="text-xs text-muted hover:text-foreground transition-colors"
        >
          {isSignUp
            ? "Already have an account? Sign in"
            : "Need an account? Register and provision an organization"}
        </button>
      </div>
    </div>
  );
}
