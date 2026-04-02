"use client";

import { useEffect, useRef, useState } from "react";

export function MermaidViewer({ chart }: { chart: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function render() {
      if (!containerRef.current || !chart) return;
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({ startOnLoad: false, theme: "default" });
        const { svg } = await mermaid.render(
          `mermaid-${Date.now()}`,
          chart
        );
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Mermaid render failed");
        }
      }
    }

    render();
    return () => { cancelled = true; };
  }, [chart]);

  if (error) {
    return (
      <div className="rounded border border-destructive/50 bg-destructive/10 p-4 text-sm">
        <p className="font-medium text-destructive mb-1">PFD render error</p>
        <pre className="text-xs whitespace-pre-wrap">{error}</pre>
        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-muted-foreground">Raw Mermaid</summary>
          <pre className="mt-1 text-xs whitespace-pre-wrap">{chart}</pre>
        </details>
      </div>
    );
  }

  return <div ref={containerRef} className="overflow-x-auto [&_svg]:max-w-full" />;
}
