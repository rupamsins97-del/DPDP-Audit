export type SupportedFramework = "DPDP_ACT_2023_RULES_2025";

export interface AuditInitiationFormValues {
  target_url: string;
  repo_url: string;
  legal_file: File | null;
  framework: SupportedFramework;
}

export interface AuditInitiationPayload {
  target_url: string;
  repo_url?: string;
  legal_doc_name?: string;
  framework: string;
  initiated_at: string;
}

export interface FormValidationErrors {
  target_url?: string;
  repo_url?: string;
  legal_file?: string;
}
