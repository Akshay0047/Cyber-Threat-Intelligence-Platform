import { useEffect, useState } from "react";
import { api, errorMessage } from "../api";
import { NetworkGraph } from "./GraphView";

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

  async function onSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api(`/api/search/?q=${encodeURIComponent(query.trim())}`);
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

  useEffect(() => {
    setSelected("");
  }, [query]);

  return (
    <section>
      <h1>Indicator search</h1>
      <p className="muted">
        Matches incident indicators in MongoDB and Infrastructure values in Neo4j.
      </p>
      <form className="row" onSubmit={onSubmit}>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="IP, domain, hash, or INF-01"
          required
        />
        <button type="submit" disabled={busy}>
          {busy ? "Searching..." : "Search"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {result && (
        <div className="split">
          <div>
            <h2>Incidents ({result.incidents.length})</h2>
            {result.incidents.length === 0 && <p className="muted">No incident documents.</p>}
            {result.incidents.map((incident) => (
              <article className="card" key={incident.incident_id}>
                <header className="card-head">
                  <strong>{incident.incident_id}</strong>
                  <span className={`badge severity-${incident.severity}`}>{incident.severity}</span>
                </header>
                <p>{incident.description}</p>
                <pre>{JSON.stringify(incident, null, 2)}</pre>
              </article>
            ))}
            <h2>Infrastructure ({result.infrastructure.length})</h2>
            {result.infrastructure.length === 0 && <p className="muted">No infrastructure nodes.</p>}
            {result.infrastructure.map((node) => {
              const id = node.properties.indicator_id;
              return (
                <button
                  type="button"
                  className={selected === id ? "card selectable active" : "card selectable"}
                  key={id}
                  onClick={() => loadNeighborhood(id).catch((err) => setError(errorMessage(err)))}
                >
                  <strong>{id}</strong>
                  <span>{node.properties.value}</span>
                  <span className="muted">{node.properties.indicator_type}</span>
                </button>
              );
            })}
          </div>
          <div>
            <h2>Neighborhood</h2>
            <NetworkGraph nodes={graph.nodes} edges={graph.edges} />
          </div>
        </div>
      )}
    </section>
  );
}
