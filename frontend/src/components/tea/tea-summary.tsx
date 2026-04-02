import { Card, CardContent } from "@/components/ui/card";
import type { TEASummary as TEAData } from "@/lib/types";

interface MetricDef {
  key: keyof TEAData;
  label: string;
  format: (v: number) => string;
}

const METRICS: MetricDef[] = [
  { key: "mesp_usd_per_gal", label: "MESP", format: (v) => `$${v.toFixed(2)}/gal` },
  { key: "mesp_usd_per_kg", label: "MESP", format: (v) => `$${v.toFixed(2)}/kg` },
  { key: "tci_usd", label: "Total Capital", format: (v) => `$${(v / 1e6).toFixed(1)}M` },
  { key: "aoc_usd_per_yr", label: "Annual OpEx", format: (v) => `$${(v / 1e6).toFixed(1)}M/yr` },
  { key: "irr", label: "IRR", format: (v) => `${(v * 100).toFixed(1)}%` },
  { key: "npv_usd", label: "NPV", format: (v) => `$${(v / 1e6).toFixed(1)}M` },
  { key: "product_flow_kg_hr", label: "Product Flow", format: (v) => `${v.toFixed(0)} kg/hr` },
];

export function TEASummary({ tea }: { tea: TEAData }) {
  const available = METRICS.filter((m) => tea[m.key] != null);
  if (available.length === 0) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
      {available.map((m) => (
        <Card key={m.key}>
          <CardContent className="pt-4 pb-3">
            <p className="text-xs text-muted-foreground">{m.label}</p>
            <p className="text-lg font-semibold">{m.format(tea[m.key]!)}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
