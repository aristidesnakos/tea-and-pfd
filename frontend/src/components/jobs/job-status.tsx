"use client";

import { PIPELINE_STEPS } from "@/lib/types";
import { cn } from "@/lib/utils";

export function JobStatus({ status }: { status: string }) {
  if (status === "failed") {
    return (
      <div className="flex items-center gap-2 text-destructive font-medium">
        <span className="inline-block w-3 h-3 rounded-full bg-destructive" />
        Failed
      </div>
    );
  }

  const currentIdx = PIPELINE_STEPS.indexOf(
    status as (typeof PIPELINE_STEPS)[number]
  );

  return (
    <div className="flex items-center gap-1">
      {PIPELINE_STEPS.map((step, i) => {
        const done = i < currentIdx || status === "completed";
        const active = i === currentIdx && status !== "completed";
        return (
          <div key={step} className="flex items-center gap-1">
            <div
              className={cn(
                "flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium transition-colors",
                done && "bg-primary text-primary-foreground",
                active && "bg-primary/20 text-primary animate-pulse",
                !done && !active && "bg-muted text-muted-foreground"
              )}
            >
              {step}
            </div>
            {i < PIPELINE_STEPS.length - 1 && (
              <div
                className={cn(
                  "w-4 h-0.5",
                  i < currentIdx ? "bg-primary" : "bg-muted"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
