"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import { isTerminal } from "./types";
import type { JobCreateRequest } from "./types";

export function useTemplates() {
  return useQuery({
    queryKey: ["templates"],
    queryFn: api.templates,
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ["job", id],
    queryFn: () => api.getJob(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && isTerminal(status) ? false : 2000;
    },
  });
}

export function useJobs(page: number) {
  return useQuery({
    queryKey: ["jobs", page],
    queryFn: () => api.listJobs(page),
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (req: JobCreateRequest) => api.createJob(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}
