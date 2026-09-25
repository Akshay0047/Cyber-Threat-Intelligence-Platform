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
      { name: "motivation", label: "Motivation", type: "select", options: ["financial", "espionage", "disruption", "hacktivism"] },
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
      { name: "sector", label: "Sector", type: "select", options: ["finance", "healthcare", "energy", "government", "telecommunications", "manufacturing", "education"] },
      { name: "country", label: "Country" },
    ],
  },
  {
    key: "relationships",
    label: "Relationships",
    path: "/api/graph/relationships/",
    idField: "element_id",
    immutable: true,
    fields: [
      { name: "type", label: "Type", type: "select", options: ["USES", "COMMUNICATES_WITH", "EXPLOITS", "PART_OF", "TARGETS", "ATTRIBUTED_TO"] },
      { name: "from_id", label: "From" },
      { name: "to_id", label: "To" },
    ],
  },
];

function businessId(node) {
  const props = node?.properties || {};
  return props.actor_id || props.malware_id || props.indicator_id || props.cve_id || props.campaign_id || props.org_id || "";
}

function emptyForm(collection) {
  return Object.fromEntries(collection.fields.map((field) => [field.name, ""]));
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
    if (field.type === "csv") payload[field.name] = raw.split(",").map((part) => part.trim()).filter(Boolean);
    else if (field.type === "number") payload[field.name] = Number(raw);
    else if (field.type === "datetime-local") payload[field.name] = new Date(raw).toISOString();
    else payload[field.name] = raw;
  });
  return payload;
}

function cell(value) {
  if (Array.isArray(value)) return value.join(", ");
  if (value == null) return "";
  const text = String(value);
  return text.length > 72 ? `${text.slice(0, 72)}...` : text;
}

const controlClass =
  "mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 shadow-inset outline-none focus:border-cyan-400";

export default function EntityList() {
  const [key, setKey] = useState(COLLECTIONS[0].key);
  const collection = useMemo(() => COLLECTIONS.find((item) => item.key === key), [key]);
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState(() => emptyForm(COLLECTIONS[0]));
  const [editing, setEditing] = useState(false);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load(next = collection) {
    const data = await api(next.path);
    if (next.key === "relationships") {
      setRows(
        data.map((rel) => ({
          element_id: rel.element_id,
          type: rel.type,
          from_id: businessId(rel.from_node),
          to_id: businessId(rel.to_node),
        }))
      );
      return;
    }
    setRows(data);
  }

  useEffect(() => {
    setForm(emptyForm(collection));
    setEditing(false);
    setOpen(false);
    setError("");
    load(collection).catch((err) => setError(errorMessage(err)));
  }, [collection]);

  function editRow(row) {
    if (collection.immutable) return;
    const next = {};
    collection.fields.forEach((field) => {
      next[field.name] = toInput(field, row[field.name]);
    });
    setForm(next);
    setEditing(true);
    setOpen(true);
  }

  function startCreate() {
    setForm(emptyForm(collection));
    setEditing(false);
    setOpen(true);
  }

  async function onSubmit(event) {
    event.preventDefault();
    if (collection.immutable && editing) return;
    setBusy(true);
    setError("");
    try {
      const payload = toPayload(collection, form);
      if (editing && !collection.immutable) {
        await api(`${collection.path}${encodeURIComponent(payload[collection.idField])}/`, { method: "PUT", body: payload });
      } else {
        await api(collection.path, { method: "POST", body: payload });
      }
      setOpen(false);
      setEditing(false);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function remove(row) {
    const id = row[collection.idField];
    if (!window.confirm(`Delete ${id}?`)) return;
    setError("");
    try {
      const target = collection.key === "relationships"
        ? `${collection.path}?id=${encodeURIComponent(id)}`
        : `${collection.path}${encodeURIComponent(id)}/`;
      await api(target, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl text-slate-50">Entities</h1>
          <p className="mt-1 text-sm text-slate-400">Create, review, and delete records. Relationships cannot be updated.</p>
        </div>
        <div className="flex gap-2">
          <select value={key} onChange={(event) => setKey(event.target.value)} className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100">
            {COLLECTIONS.map((item) => (
              <option key={item.key} value={item.key}>{item.label}</option>
            ))}
          </select>
          <button type="button" onClick={startCreate} className="rounded-md bg-cyan-400 px-4 py-2 font-semibold text-slate-950 hover:bg-cyan-300">
            Create
          </button>
        </div>
      </div>
      {error && <p className="mt-3 rounded-md border border-red-500/40 bg-red-950/70 px-3 py-2 text-sm text-red-200">{error}</p>}
      <div className="mt-4 overflow-auto rounded-xl border border-slate-800">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-950 text-xs uppercase tracking-wider text-slate-500">
            <tr>
              {collection.fields.map((field) => (
                <th key={field.name} className="whitespace-nowrap px-3 py-3 font-medium">{field.label}</th>
              ))}
              <th className="px-3 py-3" />
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row[collection.idField]} className="border-t border-slate-800 transition hover:bg-slate-800/80">
                {collection.fields.map((field) => (
                  <td key={field.name} className="max-w-[220px] px-3 py-2.5 text-slate-200" title={String(row[field.name] ?? "")}>
                    {cell(row[field.name])}
                  </td>
                ))}
                <td className="whitespace-nowrap px-3 py-2.5 text-right">
                  {!collection.immutable && (
                    <button type="button" onClick={() => editRow(row)} className="mr-2 rounded border border-slate-600 px-2 py-1 text-xs text-slate-200 hover:border-cyan-400">
                      Edit
                    </button>
                  )}
                  <button type="button" onClick={() => remove(row)} className="rounded border border-red-500/40 px-2 py-1 text-xs text-red-300 hover:bg-red-950">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="px-3 py-6 text-sm text-slate-500">No records.</p>}
      </div>

      {open && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/70 p-4 backdrop-blur-sm" onClick={() => setOpen(false)}>
          <form className="max-h-[90vh] w-full max-w-lg space-y-3 overflow-auto rounded-2xl border border-cyan-400/30 bg-slate-900 p-5 shadow-glow" onClick={(event) => event.stopPropagation()} onSubmit={onSubmit}>
            <h2 className="font-display text-lg text-slate-50">{editing && !collection.immutable ? "Edit record" : "Create record"}</h2>
            {collection.fields.map((field) => (
              <label key={field.name} className="block text-sm text-slate-300">
                {field.label}
                {field.type === "textarea" ? (
                  <textarea className={controlClass} value={form[field.name] || ""} onChange={(event) => setForm({ ...form, [field.name]: event.target.value })} required={field.name !== "notes"} />
                ) : field.type === "select" ? (
                  <select className={controlClass} value={form[field.name] || ""} onChange={(event) => setForm({ ...form, [field.name]: event.target.value })} required>
                    <option value="">Select</option>
                    {field.options.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    className={controlClass}
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
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setOpen(false)} className="rounded-md border border-slate-600 px-3 py-2 text-slate-300">
                Cancel
              </button>
              {!(collection.immutable && editing) && (
                <button type="submit" disabled={busy} className="rounded-md bg-emerald-400 px-4 py-2 font-semibold text-slate-950 hover:bg-emerald-300 disabled:opacity-60">
                  {busy ? "Saving..." : editing ? null : "Create"}
                  {!busy && editing && !collection.immutable ? "Update" : ""}
                </button>
              )}
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
