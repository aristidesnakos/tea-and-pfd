import type {
  JobCreateRequest,
  JobListResponse,
  JobResponse,
  TemplateListResponse,
} from "./types";

const BASE = "/api";

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  health: () => fetchJSON<{ status: string; version: string }>("/health"),

  templates: () => fetchJSON<TemplateListResponse>("/templates"),

  getTemplate: (name: string) => fetchJSON<Record<string, unknown>>(`/templates/${name}`),

  createJob: (req: JobCreateRequest) =>
    fetchJSON<JobResponse>("/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    }),

  getJob: (id: string) => fetchJSON<JobResponse>(`/jobs/${id}`),

  listJobs: (page = 1, perPage = 20) =>
    fetchJSON<JobListResponse>(`/jobs?page=${page}&per_page=${perPage}`),

  deleteJob: (id: string) =>
    fetchJSON<{ detail: string }>(`/jobs/${id}`, { method: "DELETE" }),

  getSpec: (id: string) => fetchJSON<Record<string, unknown>>(`/jobs/${id}/spec`),

  artifactUrl: (id: string, filename: string) => `${BASE}/jobs/${id}/artifacts/${filename}`,
};
