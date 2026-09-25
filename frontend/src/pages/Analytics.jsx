import { useEffect, useState } from "react";
import { api, errorMessage } from "../api";

const PANELS = [
  { title: "Severity breakdown", path: "/api/analytics/severity-breakdown/", label: (row) => row.severity, value: (row) => row.count, bars: true },
  { title: "Top indicators", path: "/api/analytics/top-indicators/", label: (row) => row.indicator, value: (row) => row.count, bars: false },
  { title: "Source reliability", path: "/api/analytics/source-reliability/", label: (row) => row.name, value: (row) => row.reliability_score, bars: false },
  { title: "Monthly trend", path: "/api/analytics/monthly-trend/", label: (row) => row.month, value: (row) => row.count, bars: false },
  { title: "Malware families", path: "/api/analytics/malware-families/", label: (row) => row.family, value: (row) => row.count, bars: true },
];

const BAR_COLOR = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-amber-400",
  low: "bg-emerald-400",
};

function formatValue(value) {
  if (!Number.isFinite(value)) return "—";
  if (Number.isInteger(value)) return new Intl.NumberFormat().format(value);
  return value.toFixed(2);
}

function Card({ title, rows, error, bars }) {
  const max = Math.max(...rows.map((row) => row.value), 0.01);
  return (
    <article className="mb-4 break-inside-avoid rounded-xl border border-slate-800 bg-slate-950/75 p-4">
      <h2 className="font-display text-sm uppercase tracking-widest text-cyan-300">{title}</h2>
      {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
      {!error && rows.length === 0 && <p className="mt-3 text-sm text-slate-500">No data.</p>}
      <div className="mt-3 space-y-2.5">
        {rows.map((row) => (
          <div key={row.label}>
            <div className="mb-1 flex items-baseline justify-between gap-3 text-sm">
              <span className="truncate text-slate-300" title={row.label}>{row.label}</span>
              <span className="font-display text-slate-50">{formatValue(row.value)}</span>
            </div>
            {bars && (
              <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                <div className={`h-full rounded-full ${BAR_COLOR[row.label] || "bg-cyan-400"}`} style={{ width: `${(row.value / max) * 100}%` }} />
              </div>
            )}
          </div>
        ))}
      </div>
    </article>
  );
}

export default function Analytics() {
  const [panels, setPanels] = useState(PANELS.map((panel) => ({ ...panel, rows: [], error: "" })));

  useEffect(() => {
    let active = true;
    Promise.all(
      PANELS.map(async (panel) => {
        try {
          const data = await api(panel.path);
          return {
            ...panel,
            error: "",
            rows: data.map((row) => ({ label: String(panel.label(row)), value: Number(panel.value(row)) })),
          };
        } catch (err) {
          return { ...panel, rows: [], error: errorMessage(err) };
        }
      })
    ).then((next) => {
      if (active) setPanels(next);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section>
      <h1 className="font-display text-2xl text-slate-50">Analytics</h1>
      <p className="mt-1 text-sm text-slate-400">Severity, indicators, source reliability, monthly trend, and malware families.</p>
      <div className="mt-5 columns-1 gap-4 md:columns-2">
        {panels.map((panel) => (
          <Card key={panel.title} title={panel.title} rows={panel.rows} error={panel.error} bars={panel.bars} />
        ))}
      </div>
    </section>
  );
}
