"use client";

import { use } from "react";
import { useJob } from "@/lib/hooks";
import { api } from "@/lib/api";
import { JobStatus } from "@/components/jobs/job-status";
import { TEASummary } from "@/components/tea/tea-summary";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import dynamic from "next/dynamic";

const MermaidViewer = dynamic(
  () =>
    import("@/components/pfd/mermaid-viewer").then((m) => ({
      default: m.MermaidViewer,
    })),
  { ssr: false, loading: () => <p className="text-muted-foreground text-sm">Loading PFD renderer...</p> }
);

export default function JobDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: job, isLoading, error } = useJob(id);

  if (isLoading) return <p className="text-muted-foreground">Loading...</p>;
  if (error) return <p className="text-destructive">Error: {error.message}</p>;
  if (!job) return <p className="text-muted-foreground">Job not found</p>;

  const artifacts = Object.entries(job.artifact_urls);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">
            {job.process_name || "Untitled Process"}
          </h1>
          <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
            <Badge variant="outline">{job.input_type}</Badge>
            <span>{new Date(job.created_at).toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Pipeline status */}
      <JobStatus status={job.status} />

      {/* Error */}
      {job.error_message && (
        <Card className="border-destructive">
          <CardContent className="pt-4">
            <p className="font-medium text-destructive">{job.error_type}: {job.error_message}</p>
          </CardContent>
        </Card>
      )}

      {/* Warnings */}
      {job.validation_warnings && job.validation_warnings.length > 0 && (
        <Card className="border-yellow-500">
          <CardContent className="pt-4">
            <p className="font-medium text-yellow-700 mb-1">Warnings</p>
            <ul className="list-disc list-inside text-sm">
              {job.validation_warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* PFD */}
      {job.mermaid_text && (
        <>
          <Separator />
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Process Flow Diagram</CardTitle>
            </CardHeader>
            <CardContent>
              <MermaidViewer chart={job.mermaid_text} />
            </CardContent>
          </Card>
        </>
      )}

      {/* TEA Metrics */}
      {job.tea && (
        <>
          <Separator />
          <div>
            <h2 className="text-lg font-semibold mb-3">TEA Summary</h2>
            <TEASummary tea={job.tea} />
          </div>
        </>
      )}

      {/* Downloads */}
      {artifacts.length > 0 && (
        <>
          <Separator />
          <div>
            <h2 className="text-lg font-semibold mb-3">Artifacts</h2>
            <div className="flex flex-wrap gap-2">
              {artifacts.map(([name]) => (
                <a
                  key={name}
                  href={api.artifactUrl(job.id, name)}
                  download
                  className={buttonVariants({ variant: "outline", size: "sm" })}
                >
                  {name}
                </a>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
