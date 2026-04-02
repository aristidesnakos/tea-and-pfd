"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useTemplates, useCreateJob } from "@/lib/hooks";

export function JobForm() {
  const router = useRouter();
  const { data: templateData } = useTemplates();
  const createJob = useCreateJob();

  const [tab, setTab] = useState("template");
  const [description, setDescription] = useState("");
  const [template, setTemplate] = useState("");
  const [jsonText, setJsonText] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit() {
    setError("");
    try {
      let job;
      if (tab === "nl") {
        if (!description.trim()) { setError("Enter a process description."); return; }
        job = await createJob.mutateAsync({ input_type: "nl", description });
      } else if (tab === "template") {
        if (!template) { setError("Select a template."); return; }
        job = await createJob.mutateAsync({ input_type: "template", template_name: template });
      } else {
        if (!jsonText.trim()) { setError("Paste a ProcessSpec JSON."); return; }
        const spec = JSON.parse(jsonText);
        job = await createJob.mutateAsync({ input_type: "json", spec });
      }
      router.push(`/jobs/${job.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Submission failed");
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="mb-4">
            <TabsTrigger value="template">Template</TabsTrigger>
            <TabsTrigger value="nl">Describe</TabsTrigger>
            <TabsTrigger value="json">JSON</TabsTrigger>
          </TabsList>

          <TabsContent value="nl">
            <Textarea
              placeholder="Describe your process in natural language..."
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </TabsContent>

          <TabsContent value="template">
            <Select value={template} onValueChange={(v) => setTemplate(v ?? "")}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a template..." />
              </SelectTrigger>
              <SelectContent>
                {templateData?.templates.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t.replace(/_/g, " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </TabsContent>

          <TabsContent value="json">
            <Textarea
              placeholder='Paste a ProcessSpec JSON...'
              rows={10}
              className="font-mono text-sm"
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
            />
          </TabsContent>
        </Tabs>

        {error && (
          <p className="text-sm text-destructive mt-3">{error}</p>
        )}

        <Button
          className="mt-4 w-full"
          onClick={handleSubmit}
          disabled={createJob.isPending}
        >
          {createJob.isPending ? "Submitting..." : "Generate PFD + TEA"}
        </Button>
      </CardContent>
    </Card>
  );
}
