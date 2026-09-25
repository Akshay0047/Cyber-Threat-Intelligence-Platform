import { useEffect, useMemo, useState } from "react";
import { api, errorMessage } from "../api";

const COLLECTIONS = [
  {
    key: "incidents",
    label: "Incident reports",
    path: "/api/incidents/",
    idField: "incident_id",
    fields: [
      { name: "incident_id", label: "Incident ID" },
      { name: "source", label: "Source" },
      { name: "severity", label: "Severity", type: "select", options: ["low", "medium", "high", "critical"] },
      { name: "timestamp", label: "Timestamp", type: "datetime-local" },
      { name: "description", label: "Description", type: "textarea" },
      { name: "related_indicators", label: "Related indicators", type: "csv" },
      { name: "reliability", label: "Reliability (0-1)", type: "number" },
    ],
  },
  {
    key: "malware",
    label: "Malware profiles",
    path: "/api/malware/",
    idField: "malware_id",
    fields: [
      { name: "malware_id", label: "Malware ID" },
      { name: "name", label: "Name" },
      { name: "family", label: "Family" },
      { name: "hash", label: "Hash" },
      { name: "behavior_summary", label: "Behavior summary", type: "textarea" },
      { name: "first_seen", label: "First seen", type: "datetime-local" },
    ],
  },
  {
    key: "actors",
    label: "Threat actor profiles",
    path: "/api/actor-profiles/",
    idField: "actor_id",
    fields: [
      { name: "actor_id", label: "Actor ID" },
      { name: "aliases", label: "Aliases", type: "csv" },
      {
        name: "motivation",
        label: "Motivation",
        type: "select",
        options: ["financial", "espionage", "disruption", "hacktivism"],
      },
      { name: "notes", label: "Notes", type: "textarea" },
      { name: "sources", label: "Sources", type: "csv" },
    ],
  },
  {
    key: "feeds",
    label: "Source feeds",
    path: "/api/feeds/",
    idField: "feed_id",
    fields: [
      { name: "feed_id", label: "Feed ID" },
      { name: "name", label: "Name" },
      { name: "type", label: "Type", type: "select", options: ["osint", "commercial", "government", "internal"] },
      { name: "reliability_score", label: "Reliability score", type: "number" },
    ],
  },
  {
    key: "organizations",
    label: "Organizations",
    path: "/api/organizations/",
    idField: "org_id",
    fields: [
      { name: "org_id", label: "Organization ID" },
      { name: "name", label: "Name" },
      {
        name: "sector",
        label: "Sector",
        type: "select",
        options: ["finance", "healthcare", "energy", "government", "telecommunications", "manufacturing", "education"],
      },
      { name: "country", label: "Country" },
    ],
  },
];

function emptyForm(collection) {
  return Object.fromEntries(collection.fields.map((field) => [field.name, field.type === "csv" ? "" : ""]));
}

function toInput(field, value) {
  if (value == null) return "";
  if (field.type === "csv") return Array.isArray(value) ? value.join(", ") : String(value);
  if (field.type === "datetime-local") return String(value).slice(0, 16);
  return String(value);
}

function toPayload(collection, form) {
  const payload = {};
  collection.fields.forEach((field) => {
    const raw = form[field.name] ?? "";
    if (field.type === "csv") {
      payload[field.name] = raw.split(",").map((part) => part.trim()).filter(Boolean);
    } else if (field.type === "number") {
      payload[field.name] = Number(raw);
    } else if (field.type === "datetime-local") {
      payload[field.name] = new Date(raw).toISOString();
    } else {
      payload[field.name] = raw;
    }
  });
  return payload;
}

function cell(value) {
  if (Array.isArray(value)) return value.join(", ");
  if (value == null) return "";
  const text = String(value);
  return text.length > 80 ? `${text.slice(0, 80)}...` : text;
}

export default function EntityList() {
  const [key, setKey] = useState(COLLECTIONS[0].key);
  const collection = useMemo(() => COLLECTIONS.find((item) => item.key === key), [key]);
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState(() => emptyForm(COLLECTIONS[0]));
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load(next = collection) {
    const data = await api(next.path);
    setRows(data);
  }

  useEffect(() => {
    setForm(emptyForm(collection));
    setEditing(false);
    setError("");
    load(collection).catch((err) => setError(errorMessage(err)));
  }, [collection]);

  function editRow(row) {
    const next = {};
    collection.fields.forEach((field) => {
      next[field.name] = toInput(field, row[field.name]);
    });
    setForm(next);
    setEditing(true);
  }

  async function onSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const payload = toPayload(collection, form);
      if (editing) {
        await api(`${collection.path}${encodeURIComponent(payload[collection.idField])}/`, {
          method: "PUT",
          body: payload,
        });
      } else {
        await api(collection.path, { method: "POST", body: payload });
      }
      setForm(emptyForm(collection));
      setEditing(false);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function remove(row) {
    if (!window.confirm(`Delete ${row[collection.idField]}?`)) return;
    setError("");
    try {
      await api(`${collection.path}${encodeURIComponent(row[collection.idField])}/`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <section>
      <h1>Collections</h1>
      <label>
        Collection
        <select
          value={key}
          onChange={(event) => setKey(event.target.value)}
        >
          {COLLECTIONS.map((item) => (
            <option key={item.key} value={item.key}>
              {item.label}
            </option>
          ))}
        </select>
      </label>
      {error && <p className="error">{error}</p>}
      <div className="split">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {collection.fields.map((field) => (
                  <th key={field.name}>{field.label}</th>
                ))}
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row[collection.idField]}>
                  {collection.fields.map((field) => (
                    <td key={field.name} title={String(row[field.name] ?? "")}>
                      {cell(row[field.name])}
                    </td>
                  ))}
                  <td className="actions">
                    <button type="button" onClick={() => editRow(row)}>
                      Edit
                    </button>
                    <button type="button" className="danger" onClick={() => remove(row)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && <p className="muted">No documents.</p>}
        </div>
        <form className="card" onSubmit={onSubmit}>
          <h2>{editing ? "Update" : "Create"}</h2>
          {collection.fields.map((field) => (
            <label key={field.name}>
              {field.label}
              {field.type === "textarea" ? (
                <textarea
                  value={form[field.name] || ""}
                  onChange={(event) => setForm({ ...form, [field.name]: event.target.value })}
                  required
                />
              ) : field.type === "select" ? (
                <select
                  value={form[field.name] || ""}
                  onChange={(event) => setForm({ ...form, [field.name]: event.target.value })}
                  required
                >
                  <option value="">Select</option>
                  {field.options.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.type === "number" ? "number" : field.type === "datetime-local" ? "datetime-local" : "text"}
                  step={field.type === "number" ? "0.01" : undefined}
                  min={field.type === "number" ? "0" : undefined}
                  max={field.type === "number" ? "1" : undefined}
                  value={form[field.name] || ""}
                  onChange={(event) => setForm({ ...form, [field.name]: event.target.value })}
                  readOnly={editing && field.name === collection.idField}
                  required
                />
              )}
            </label>
          ))}
          <div className="row">
            <button type="submit" disabled={busy}>
              {busy ? "Saving..." : editing ? "Update" : "Create"}
            </button>
            {editing && (
              <button
                type="button"
                onClick={() => {
                  setEditing(false);
                  setForm(emptyForm(collection));
                }}
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>
    </section>
  );
}
