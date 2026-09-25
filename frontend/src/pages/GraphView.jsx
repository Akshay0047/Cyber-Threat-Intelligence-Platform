import { useEffect, useRef, useState } from "react";
import { Network } from "vis-network/standalone";
import { api, errorMessage } from "../api";

const OPTIONS = {
  nodes: { shape: "dot", size: 16, font: { size: 13, color: "#0f172a" } },
  edges: {
    arrows: "to",
    font: { size: 10, align: "middle", strokeWidth: 0 },
    color: { color: "#64748b" },
  },
  physics: { barnesHut: { gravitationalConstant: -9000, springLength: 140 } },
  groups: {
    ThreatActor: { color: "#b91c1c" },
    Malware: { color: "#c2410c" },
    Infrastructure: { color: "#1d4ed8" },
    Vulnerability: { color: "#7c3aed" },
    Campaign: { color: "#0f766e" },
    Organization: { color: "#15803d" },
  },
};

export function NetworkGraph({ nodes, edges }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current) return undefined;
    const network = new Network(ref.current, { nodes: nodes || [], edges: edges || [] }, OPTIONS);
    return () => network.destroy();
  }, [nodes, edges]);
  if (!nodes || nodes.length === 0) return <p className="muted">No graph nodes to draw.</p>;
  return <div ref={ref} className="graph-canvas" />;
}

const QUERIES = [
  {
    key: "actor-malware",
    label: "Actor malware",
    path: (form) => `/api/graph/queries/actor-malware/?actor_id=${encodeURIComponent(form.actor_id)}`,
    fields: ["actor_id"],
  },
  {
    key: "malware-infra",
    label: "Malware infrastructure",
    path: (form) => `/api/graph/queries/malware-infra/?malware_id=${encodeURIComponent(form.malware_id)}`,
    fields: ["malware_id"],
  },
  {
    key: "actor-campaigns",
    label: "Actor campaigns",
    path: (form) => `/api/graph/queries/actor-campaigns/?actor_id=${encodeURIComponent(form.actor_id)}`,
    fields: ["actor_id"],
  },
  {
    key: "shared-infra",
    label: "Shared infrastructure",
    path: () => "/api/graph/queries/shared-infra/",
    fields: [],
  },
  {
    key: "shortest-path",
    label: "Shortest path",
    path: (form) =>
      `/api/graph/queries/shortest-path/?actor_id=${encodeURIComponent(form.actor_id)}&org_id=${encodeURIComponent(form.org_id)}`,
    fields: ["actor_id", "org_id"],
  },
];

export default function GraphView() {
  const [form, setForm] = useState({ actor_id: "TA-01", malware_id: "MW-01", org_id: "ORG-15" });
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [summary, setSummary] = useState("");
  const [error, setError] = useState("");

  async function run(query) {
    setError("");
    try {
      const data = await api(query.path(form));
      setGraph(data.graph || { nodes: [], edges: [] });
      const count = data.graph?.nodes?.length || 0;
      const length = data.path?.length;
      setSummary(
        length == null
          ? `${query.label}: ${count} node${count === 1 ? "" : "s"}`
          : `${query.label}: ${length} hop${length === 1 ? "" : "s"}`
      );
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <section>
      <h1>Graph queries</h1>
      <p className="muted">Each button runs one Cypher query and draws the returned nodes and paths.</p>
      <div className="row">
        <label>
          Actor
          <input value={form.actor_id} onChange={(event) => setForm({ ...form, actor_id: event.target.value })} />
        </label>
        <label>
          Malware
          <input value={form.malware_id} onChange={(event) => setForm({ ...form, malware_id: event.target.value })} />
        </label>
        <label>
          Organization
          <input value={form.org_id} onChange={(event) => setForm({ ...form, org_id: event.target.value })} />
        </label>
      </div>
      <div className="row">
        {QUERIES.map((query) => (
          <button type="button" key={query.key} onClick={() => run(query)}>
            {query.label}
          </button>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      {summary && <p>{summary}</p>}
      <NetworkGraph nodes={graph.nodes} edges={graph.edges} />
    </section>
  );
}
