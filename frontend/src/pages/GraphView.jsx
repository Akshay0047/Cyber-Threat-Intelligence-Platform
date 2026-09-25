import { useEffect, useRef, useState } from "react";
import { Network } from "vis-network/standalone";
import { api, errorMessage } from "../api";

const OPTIONS = {
  nodes: {
    shape: "dot",
    size: 18,
    borderWidth: 1,
    font: { size: 13, color: "#f8fafc", strokeWidth: 0 },
  },
  edges: {
    arrows: "to",
    font: { size: 11, color: "#cbd5e1", strokeWidth: 0, align: "middle" },
    color: { color: "#94a3b8", highlight: "#e2e8f0" },
  },
  physics: { barnesHut: { gravitationalConstant: -9000, springLength: 140 } },
  groups: {
    ThreatActor: { color: { background: "#ef4444", border: "#fecaca" } },
    Malware: { color: { background: "#f97316", border: "#ffedd5" } },
    Infrastructure: { color: { background: "#3b82f6", border: "#dbeafe" } },
    Vulnerability: { color: { background: "#a855f7", border: "#f3e8ff" } },
    Campaign: { color: { background: "#14b8a6", border: "#ccfbf1" } },
    Organization: { color: { background: "#22c55e", border: "#dcfce7" } },
  },
};

const LEGEND = [
  ["Threat actor", "bg-red-500"],
  ["Malware", "bg-orange-500"],
  ["Infrastructure", "bg-blue-500"],
  ["Victim org", "bg-green-500"],
];

export function NetworkGraph({ nodes, edges }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current) return undefined;
    const network = new Network(ref.current, { nodes: nodes || [], edges: edges || [] }, OPTIONS);
    return () => network.destroy();
  }, [nodes, edges]);

  return (
    <div className="overflow-hidden rounded-xl border border-slate-700 bg-slate-950">
      <div className="flex flex-wrap gap-3 border-b border-slate-800 px-3 py-2 text-xs text-slate-400">
        {LEGEND.map(([label, color]) => (
          <span key={label} className="inline-flex items-center gap-1.5">
            <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
            {label}
          </span>
        ))}
      </div>
      {!nodes || nodes.length === 0 ? (
        <p className="grid h-[520px] place-items-center text-sm text-slate-500">No graph nodes to draw.</p>
      ) : (
        <div ref={ref} className="h-[520px] bg-slate-950" />
      )}
    </div>
  );
}

const QUERIES = [
  { key: "actor-malware", label: "Actor malware", path: (form) => `/api/graph/queries/actor-malware/?actor_id=${encodeURIComponent(form.actor_id)}` },
  { key: "malware-infra", label: "Malware infrastructure", path: (form) => `/api/graph/queries/malware-infra/?malware_id=${encodeURIComponent(form.malware_id)}` },
  { key: "actor-campaigns", label: "Actor campaigns", path: (form) => `/api/graph/queries/actor-campaigns/?actor_id=${encodeURIComponent(form.actor_id)}` },
  { key: "shared-infra", label: "Shared infrastructure", path: () => "/api/graph/queries/shared-infra/" },
  {
    key: "shortest-path",
    label: "Shortest path",
    path: (form) => `/api/graph/queries/shortest-path/?actor_id=${encodeURIComponent(form.actor_id)}&org_id=${encodeURIComponent(form.org_id)}`,
  },
];

const inputClass =
  "mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 shadow-inset outline-none focus:border-cyan-400";

export default function GraphView() {
  const [form, setForm] = useState({ actor_id: "TA-01", malware_id: "MW-01", org_id: "ORG-15" });
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [summary, setSummary] = useState("Choose a query to draw the neighborhood.");
  const [error, setError] = useState("");

  async function run(query) {
    setError("");
    try {
      const data = await api(query.path(form));
      setGraph(data.graph || { nodes: [], edges: [] });
      const count = data.graph?.nodes?.length || 0;
      const length = data.path?.length;
      setSummary(length == null ? `${query.label}: ${count} node${count === 1 ? "" : "s"}` : `${query.label}: ${length} hop${length === 1 ? "" : "s"}`);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <section>
      <h1 className="font-display text-2xl text-slate-50">Graph queries</h1>
      <p className="mt-1 text-sm text-slate-400">Run a relationship query and draw the matching nodes and paths.</p>
      <div className="mt-5 grid items-start gap-5 xl:grid-cols-2">
        <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            {["actor_id", "malware_id", "org_id"].map((name) => (
              <label key={name} className="text-xs uppercase tracking-wide text-slate-400">
                {name.replace("_", " ")}
                <input className={inputClass} value={form[name]} onChange={(event) => setForm({ ...form, [name]: event.target.value })} />
              </label>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            {QUERIES.map((query) => (
              <button key={query.key} type="button" onClick={() => run(query)} className="rounded-md border border-cyan-400/40 px-3 py-1.5 text-sm text-cyan-200 hover:bg-cyan-400/10">
                {query.label}
              </button>
            ))}
          </div>
          {error && <p className="rounded-md border border-red-500/40 bg-red-950/70 px-3 py-2 text-sm text-red-200">{error}</p>}
          <p className="text-sm text-emerald-300">{summary}</p>
        </div>
        <NetworkGraph nodes={graph.nodes} edges={graph.edges} />
      </div>
    </section>
  );
}
