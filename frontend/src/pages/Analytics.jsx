import { useEffect, useState } from "react";
import { api, errorMessage } from "../api";

const PANELS = [
  {
    title: "Severity breakdown",
    path: "/api/analytics/severity-breakdown/",
    label: (row) => row.severity,
    value: (row) => row.count,
  },
  {
    title: "Top indicators",
    path: "/api/analytics/top-indicators/",
    label: (row) => row.indicator,
    value: (row) => row.count,
  },
  {
    title: "Source reliability",
    path: "/api/analytics/source-reliability/",
    label: (row) => row.name,
    value: (row) => row.reliability_score,
  },
  {
    title: "Monthly trend",
    path: "/api/analytics/monthly-trend/",
    label: (row) => row.month,
    value: (row) => row.count,
  },
  {
    title: "Malware families",
    path: "/api/analytics/malware-families/",
    label: (row) => row.family,
    value: (row) => row.count,
  },
];

function Bars({ title, rows, error }) {
  const max = Math.max(...rows.map((row) => row.value), 0.01);
  return (
    <article className="card">
      <h2>{title}</h2>
      {error && <p className="error">{error}</p>}
      {!error && rows.length === 0 && <p className="muted">No data.</p>}
      {rows.map((row) => (
        <div className="bar-row" key={row.label}>
          <span className="bar-label" title={row.label}>
            {row.label}
          </span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(row.value / max) * 100}%` }} />
          </div>
          <span className="bar-value">{row.value}</span>
        </div>
      ))}
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
      <h1>Analytics</h1>
      <div className="analytics-grid">
        {panels.map((panel) => (
          <Bars key={panel.title} title={panel.title} rows={panel.rows} error={panel.error} />
        ))}
      </div>
    </section>
  );
}
