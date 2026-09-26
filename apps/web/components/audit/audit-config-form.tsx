"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { FileUpload } from "@/components/ui/file-upload";
import { apiClient } from "@/lib/api-client";
import {
  AuditInitiationFormValues,
  FormValidationErrors,
} from "@/lib/types/audit";
import {
  Globe,
  GitBranch,
  FileCheck2,
  ShieldCheck,
  AlertCircle,
  Loader2,
} from "lucide-react";

export function AuditConfigForm() {
  const router = useRouter();

  const [formValues, setFormValues] = React.useState<AuditInitiationFormValues>({
    target_url: "",
    repo_url: "",
    legal_file: null,
    framework: "DPDP_ACT_2023_RULES_2025",
  });

  const [touched, setTouched] = React.useState<{
    target_url?: boolean;
    repo_url?: boolean;
  }>({});

  const [errors, setErrors] = React.useState<FormValidationErrors>({});
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);

  // Validate Target URL
  const validateTargetUrl = (url: string): string | undefined => {
    if (!url || url.trim() === "") {
      return "Target Application URL is required.";
    }
    try {
      const parsed = new URL(url.trim());
      if (!["http:", "https:"].includes(parsed.protocol)) {
        return "Target URL must begin with http:// or https://";
      }
      if (!parsed.hostname || !parsed.hostname.includes(".")) {
        return "Please enter a valid domain name (e.g., https://example.com).";
      }
    } catch {
      return "Please enter a well-formed URL (e.g., https://example.com).";
    }
    return undefined;
  };

  // Validate Repo URL (optional)
  const validateRepoUrl = (url: string): string | undefined => {
    if (!url || url.trim() === "") {
      return undefined;
    }
    const trimmed = url.trim();
    const gitHttpPattern = /^https?:\/\/([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/.*)?$/;
    const gitSshPattern = /^git@[a-zA-Z0-9.-]+:[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+(\.git)?$/;

    if (!gitHttpPattern.test(trimmed) && !gitSshPattern.test(trimmed)) {
      return "Please enter a valid Git repository URL (e.g., https://github.com/org/repo).";
    }
    return undefined;
  };

  // Re-run validation on change
  React.useEffect(() => {
    const newErrors: FormValidationErrors = {};

    if (touched.target_url || formValues.target_url) {
      const targetErr = validateTargetUrl(formValues.target_url);
      if (targetErr) newErrors.target_url = targetErr;
    }

    if (touched.repo_url || formValues.repo_url) {
      const repoErr = validateRepoUrl(formValues.repo_url);
      if (repoErr) newErrors.repo_url = repoErr;
    }

    setErrors((prev) => ({
      ...prev,
      target_url: newErrors.target_url,
      repo_url: newErrors.repo_url,
    }));
  }, [formValues.target_url, formValues.repo_url, touched]);

  // Determine if form is submittable
  const isTargetUrlValid = !validateTargetUrl(formValues.target_url);
  const isRepoUrlValid = !validateRepoUrl(formValues.repo_url);
  const isFileValid = !errors.legal_file;
  const canSubmit =
    formValues.target_url.trim().length > 0 &&
    isTargetUrlValid &&
    isRepoUrlValid &&
    isFileValid &&
    !isSubmitting;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const targetErr = validateTargetUrl(formValues.target_url);
    const repoErr = validateRepoUrl(formValues.repo_url);

    if (targetErr || repoErr || errors.legal_file) {
      setErrors({
        target_url: targetErr,
        repo_url: repoErr,
        legal_file: errors.legal_file,
      });
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    let projectName = "DPDP 360° Audit";
    try {
      projectName = `Audit - ${new URL(formValues.target_url.trim()).hostname}`;
    } catch {
      projectName = "DPDP 360° Audit";
    }

    const requestPayload = {
      project_name: projectName,
      target_url: formValues.target_url.trim(),
      repository_url: formValues.repo_url.trim() || null,
      framework: "BOTH",
      legal_doc_reference: formValues.legal_file?.name || null,
    };

    try {
      const { data, error } = await apiClient<{
        audit_id: string;
        status: string;
        organization_id: string;
      }>("/audits", {
        method: "POST",
        body: JSON.stringify(requestPayload),
      });

      if (error || !data) {
        setSubmitError(error || "Failed to initiate compliance audit. Please verify backend service.");
        setIsSubmitting(false);
        return;
      }

      // Persist active audit ID to localStorage for dashboard retrieval
      try {
        localStorage.setItem("dpdp_latest_audit_id", data.audit_id);
      } catch {
        // ignore
      }

      // Route to real-time telemetry stream upon successful audit enqueue (Invariant 1)
      const auditUrl = `/telemetry?audit_id=${data.audit_id}&target_url=${encodeURIComponent(
        formValues.target_url.trim()
      )}`;
      router.push(auditUrl);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "An unexpected network error occurred.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-2xl">
      <Card className="border-border bg-surface shadow-2xl">
        <CardHeader className="space-y-2 border-b border-border pb-6">
          <div className="inline-flex items-center gap-2 self-start rounded-md bg-surface-raised px-2.5 py-1 text-xs font-mono text-muted border border-border">
            <ShieldCheck className="h-3.5 w-3.5 text-accent" />
            <span>Target Initiation &amp; Configuration</span>
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-foreground">
            Configure 360° Compliance Audit
          </CardTitle>
          <CardDescription className="text-sm text-muted">
            Configure the multi-agent statutory audit parameters for real-time frontend,
            backend, legal governance, and domain verification.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-6 pt-6">
            {submitError && (
              <div className="flex items-start gap-2.5 rounded-lg bg-red-950/40 p-3.5 border border-red-500/40 text-xs text-red-200">
                <AlertCircle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="font-semibold">Audit Initiation Failed</p>
                  <p className="text-[11px] text-red-300">{submitError}</p>
                </div>
              </div>
            )}

            {/* Field 1: Target URL */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="target-url" className="flex items-center gap-1.5">
                  <Globe className="h-3.5 w-3.5 text-accent" />
                  <span>Target Web Application URL</span>
                  <span className="text-accent">*</span>
                </Label>
                <span className="text-[11px] text-muted font-mono">Required</span>
              </div>
              <Input
                id="target-url"
                type="url"
                placeholder="https://app.example.com"
                value={formValues.target_url}
                onChange={(e) =>
                  setFormValues((prev) => ({ ...prev, target_url: e.target.value }))
                }
                onBlur={() => setTouched((prev) => ({ ...prev, target_url: true }))}
                aria-invalid={!!errors.target_url}
                disabled={isSubmitting}
                required
              />
              {errors.target_url ? (
                <div className="flex items-center gap-1.5 text-xs text-red-400">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                  <span>{errors.target_url}</span>
                </div>
              ) : (
                <p className="text-[11px] text-muted">
                  Full public URL of the web application for live Stagehand/CDP consent and tracker analysis.
                </p>
              )}
            </div>

            {/* Field 2: Repository URL */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="repo-url" className="flex items-center gap-1.5">
                  <GitBranch className="h-3.5 w-3.5 text-accent" />
                  <span>Source Code Repository URL</span>
                </Label>
                <span className="text-[11px] text-muted font-mono">Optional</span>
              </div>
              <Input
                id="repo-url"
                type="text"
                placeholder="https://github.com/organization/application-repo"
                value={formValues.repo_url}
                onChange={(e) =>
                  setFormValues((prev) => ({ ...prev, repo_url: e.target.value }))
                }
                onBlur={() => setTouched((prev) => ({ ...prev, repo_url: true }))}
                aria-invalid={!!errors.repo_url}
                disabled={isSubmitting}
              />
              {errors.repo_url ? (
                <div className="flex items-center gap-1.5 text-xs text-red-400">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                  <span>{errors.repo_url}</span>
                </div>
              ) : (
                <p className="text-[11px] text-muted">
                  Ephemeral clone target for Semgrep AST static analysis and unified diff patch generation.
                </p>
              )}
            </div>

            {/* Field 3: Legal Document Upload */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-1.5">
                  <FileCheck2 className="h-3.5 w-3.5 text-accent" />
                  <span>Upload Legal Documents (Privacy Policy / DPA)</span>
                </Label>
                <span className="text-[11px] text-muted font-mono">Optional</span>
              </div>
              <FileUpload
                value={formValues.legal_file}
                onChange={(file) =>
                  setFormValues((prev) => ({ ...prev, legal_file: file }))
                }
                onError={(err) =>
                  setErrors((prev) => ({ ...prev, legal_file: err || undefined }))
                }
                disabled={isSubmitting}
              />
            </div>

            {/* Field 4: Framework Selector */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="framework-select" className="flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-accent" />
                  <span>Regulatory Framework</span>
                </Label>
                <span className="text-[11px] text-muted font-mono">v1 Standard</span>
              </div>
              <Select
                id="framework-select"
                value={formValues.framework}
                disabled={isSubmitting}
                onChange={(e) =>
                  setFormValues((prev) => ({
                    ...prev,
                    framework: e.target.value as AuditInitiationFormValues["framework"],
                  }))
                }
              >
                <option value="DPDP_ACT_2023_RULES_2025">
                  Digital Personal Data Protection (DPDP) Act, 2023 &amp; Rules, 2025
                </option>
              </Select>
              <p className="text-[11px] text-muted">
                Grounds all governance promises and findings against Section 5, 6, 8, 9, 12, 13 &amp; Rules 3–7.
              </p>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-3 border-t border-border pt-6">
            <Button
              type="submit"
              disabled={!canSubmit}
              size="lg"
              className="w-full flex items-center justify-center gap-2 font-semibold"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Enqueuing 360° Audit...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="h-5 w-5" />
                  <span>Start 360° Audit</span>
                </>
              )}
            </Button>
            <p className="text-[11px] text-center text-muted">
              Ephemeral in-memory processing • Zero persistence of raw source code or PII (Invariants 2 &amp; 4)
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
