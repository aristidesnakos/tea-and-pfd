"use client";

import { useState } from "react";
import Link from "next/link";
import { useJobs } from "@/lib/hooks";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  completed: "default",
  failed: "destructive",
};

export default function JobsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useJobs(page);

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">Job History</h1>

      {isLoading && <p className="text-muted-foreground">Loading...</p>}

      {data && data.jobs.length === 0 && (
        <p className="text-muted-foreground">
          No jobs yet. <Link href="/new" className="underline">Create one</Link>.
        </p>
      )}

      <div className="space-y-2">
        {data?.jobs.map((job) => (
          <Link key={job.id} href={`/jobs/${job.id}`}>
            <Card className="hover:bg-accent/50 transition-colors cursor-pointer">
              <CardContent className="py-3 flex items-center justify-between">
                <div>
                  <p className="font-medium">
                    {job.process_name || "Untitled"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(job.created_at).toLocaleString()} &middot; {job.input_type}
                    {job.tea?.mesp_usd_per_gal != null && ` · MESP $${job.tea.mesp_usd_per_gal.toFixed(2)}/gal`}
                  </p>
                </div>
                <Badge variant={STATUS_VARIANT[job.status] ?? "secondary"}>
                  {job.status}
                </Badge>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Pagination */}
      {data && data.total > data.per_page && (
        <div className="flex justify-center gap-2 mt-6">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span className="flex items-center text-sm text-muted-foreground">
            Page {data.page} of {Math.ceil(data.total / data.per_page)}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= Math.ceil(data.total / data.per_page)}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
