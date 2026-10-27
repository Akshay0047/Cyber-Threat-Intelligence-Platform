import { useEffect, useState } from "react";
import { api, errorMessage } from "../api";
import { incidentIndicatorLabel, infrastructureDetail, infrastructureTitle } from "../indicatorDisplay";
import { NetworkGraph } from "./GraphView";

const SEVERITY = {
  critical: "bg-red-500/20 text-red-300 ring-red-500/50",
  high: "bg-orange-500/20 text-orange-300 ring-orange-500/50",
  medium: "bg-amber-400/15 text-amber-200 ring-amber-400/40",
  low: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/40",
};

function Badge({ children, className = "" }) {
  return <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ${className}`}>{children}</span>;
}

function display(value) {
  if (Array.isArray(value)) return value.join(", ");
  if (value == null || value === "") return "—";
  return String(value);
}

const SUGGESTIONS = [
  { term: "INF-01", hint: "First infrastructure record — good demo for incidents and the neighborhood graph" },
  { term: "INF-11", hint: "Domain-type indicator" },
  { term: "INF-21", hint: "Hash-type indicator" },
];

function IncidentCard({ incident }) {
  const fields = [
    ["Source", incident.source],
    ["Timestamp", incident.timestamp],
    ["Reliability", incident.reliability],
    ["Description", incident.description],
  ];
  return (
    <article className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <header className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500">Incident</p>
          <h3 className="font-display text-lg text-slate-50">{incident.incident_id}</h3>
        </div>
        <Badge className={SEVERITY[incident.severity] || "bg-slate-800 text-slate-300 ring-slate-600"}>{incident.severity}</Badge>
      </header>
      <div className="mb-3">
        <p className="text-xs uppercase tracking-widest text-cyan-400">Indicators</p>
        <div className="mt-1 flex flex-wrap gap-1.5">
          {(incident.related_indicators || []).map((indicator) => (
            <Badge key={indicator} className="bg-cyan-400/10 font-mono normal-case tracking-normal text-cyan-200 ring-cyan-400/40">
              {incidentIndicatorLabel(indicator)}
            </Badge>
          ))}
        </div>
      </div>
      <dl className="space-y-2 text-sm">
        {fields.map(([label, value]) => (
          <div key={label} className="grid grid-cols-[110px_1fr] gap-2">
            <dt className="text-slate-500">{label}</dt>
            <dd className="text-slate-200">{display(value)}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}

export default function Search() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function loadNeighborhood(id) {
    if (!id) {
      setGraph({ nodes: [], edges: [] });
      return;
    }
    const neighborhood = await api(`/api/graph/neighborhood/?id=${encodeURIComponent(id)}`);
    setGraph(neighborhood);
    setSelected(id);
  }

  async function runSearch(term) {
    const trimmed = term.trim();
    if (!trimmed) return;
    setQuery(trimmed);
    setBusy(true);
    setError("");
    try {
      const data = await api(`/api/search/?q=${encodeURIComponent(trimmed)}`);
      setResult(data);
      const first = data.infrastructure[0];
      const id = first?.properties?.indicator_id || first?.properties?.value || "";
      await loadNeighborhood(id);
    } catch (err) {
      setError(errorMessage(err));
      setResult(null);
      setGraph({ nodes: [], edges: [] });
    } finally {
      setBusy(false);
    }
  }

  async function onSubmit(event) {
    event.preventDefault();
    await runSearch(query);
  }

  useEffect(() => {
    setSelected("");
  }, [query]);

  return (
    <section>
      <h1 className="font-display text-2xl text-slate-50">Indicator search</h1>
      <p className="mt-1 text-sm text-slate-400">
        Look up an IP, domain, file hash, or indicator code such as INF-01. Pick a suggestion below to run a sample search.
      </p>
      <form className="mt-4 flex flex-wrap gap-2" onSubmit={onSubmit}>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="IP, domain, hash, or INF-01"
          required
          className="min-w-[240px] flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 shadow-inset outline-none focus:border-cyan-400"
        />
        <button type="submit" disabled={busy} className="rounded-md bg-cyan-400 px-4 py-2 font-semibold text-slate-950 hover:bg-cyan-300 disabled:opacity-60">
          {busy ? "Searching..." : "Search"}
        </button>
      </form>
      <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
        <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">Try a sample search</p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          {SUGGESTIONS.map((item) => (
            <button
              key={item.term}
              type="button"
              disabled={busy}
              onClick={() => runSearch(item.term)}
              className="rounded-lg border border-cyan-400/30 bg-slate-900/80 px-4 py-3 text-left transition hover:border-cyan-400/60 hover:bg-cyan-400/5 disabled:opacity-60"
            >
              <span className="font-mono text-sm font-semibold text-cyan-200">{item.term}</span>
              <span className="mt-1 block text-xs text-slate-400">{item.hint}</span>
            </button>
          ))}
        </div>
      </div>
      {error && <p className="mt-3 rounded-md border border-red-500/40 bg-red-950/70 px-3 py-2 text-sm text-red-200">{error}</p>}
      {!result && !busy && !error && (
        <p className="mt-6 text-center text-sm text-slate-500">No results yet. Click a suggestion above or type an indicator and press Search.</p>
      )}
      {result && (
        <div className="mt-5 grid min-w-0 items-start gap-5 min-[1400px]:grid-cols-2">
          <div className="space-y-3">
            <h2 className="text-sm uppercase tracking-widest text-slate-400">Incidents ({result.incidents.length})</h2>
            {result.incidents.length === 0 && <p className="text-sm text-slate-500">No incident documents.</p>}
            {result.incidents.map((incident) => (
              <IncidentCard key={incident.incident_id} incident={incident} />
            ))}
            <h2 className="pt-2 text-sm uppercase tracking-widest text-slate-400">Infrastructure ({result.infrastructure.length})</h2>
            {result.infrastructure.length === 0 && <p className="text-sm text-slate-500">No infrastructure nodes.</p>}
            {result.infrastructure.map((node) => {
              const id = node.properties.indicator_id;
              const active = selected === id;
              return (
                <button
                  type="button"
                  key={id}
                  onClick={() => loadNeighborhood(id).catch((err) => setError(errorMessage(err)))}
                  className={`flex w-full items-center justify-between rounded-xl border px-4 py-3 text-left ${
                    active ? "border-cyan-400 bg-cyan-400/10 shadow-glow" : "border-slate-800 bg-slate-950/70 hover:border-slate-600"
                  }`}
                >
                  <span>
                    <span className="block font-mono text-sm font-semibold text-cyan-100">{infrastructureTitle(node.properties)}</span>
                    <span className="text-xs text-slate-500">{infrastructureDetail(node.properties)}</span>
                  </span>
                  <Badge className="bg-blue-500/15 text-blue-200 ring-blue-400/40">{node.properties.indicator_type}</Badge>
                </button>
              );
            })}
          </div>
          <div>
            <h2 className="mb-3 text-sm uppercase tracking-widest text-slate-400">Neighborhood</h2>
            <NetworkGraph nodes={graph.nodes} edges={graph.edges} />
          </div>
        </div>
      )}
    </section>
  );
}
