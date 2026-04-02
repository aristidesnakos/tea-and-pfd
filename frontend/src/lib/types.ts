// Mirrors src/processflow/api/schemas.py

export interface TEASummary {
  mesp_usd_per_gal?: number | null;
  mesp_usd_per_kg?: number | null;
  tci_usd?: number | null;
  aoc_usd_per_yr?: number | null;
  irr?: number | null;
  npv_usd?: number | null;
  product_flow_kg_hr?: number | null;
}

export interface JobResponse {
  id: string;
  status: string;
  input_type: string;
  process_name?: string | null;
  skip_simulation: boolean;
  pfd_format: string;
  validation_errors?: string[] | null;
  validation_warnings?: string[] | null;
  tea?: TEASummary | null;
  error_message?: string | null;
  error_type?: string | null;
  artifact_urls: Record<string, string>;
  mermaid_text?: string | null;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface JobListItem {
  id: string;
  status: string;
  input_type: string;
  process_name?: string | null;
  created_at: string;
  tea?: TEASummary | null;
}

export interface JobListResponse {
  jobs: JobListItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface TemplateListResponse {
  templates: string[];
}

export type JobCreateRequest =
  | { input_type: "nl"; description: string; skip_simulation?: boolean }
  | { input_type: "template"; template_name: string; skip_simulation?: boolean }
  | { input_type: "json"; spec: Record<string, unknown>; skip_simulation?: boolean };

// Pipeline statuses in order
export const PIPELINE_STEPS = [
  "submitted",
  "parsing",
  "validating",
  "rendering",
  "simulating",
  "completed",
] as const;

export type PipelineStatus = (typeof PIPELINE_STEPS)[number] | "failed";

export function isTerminal(status: string): boolean {
  return status === "completed" || status === "failed";
}
