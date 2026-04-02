import { JobForm } from "@/components/jobs/job-form";

export default function NewProcessPage() {
  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">New Process</h1>
      <p className="text-muted-foreground mb-6">
        Describe a chemical process, pick a template, or paste a ProcessSpec JSON to generate a PFD and TEA report.
      </p>
      <JobForm />
    </div>
  );
}
