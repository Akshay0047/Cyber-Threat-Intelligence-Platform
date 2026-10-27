/** Human-readable labels for infrastructure indicators (avoid leading with a 64-char hash). */

export function shortenHash(value) {
  const text = String(value || "").trim();
  if (text.length > 20 && /^[a-f0-9]+$/i.test(text)) {
    return `${text.slice(0, 12)}…`;
  }
  return text;
}

export function formatIndicatorValue(value, indicatorType) {
  const text = String(value || "").trim();
  if (!text) return "—";
  if (indicatorType === "hash" || (text.length > 32 && /^[a-f0-9]+$/i.test(text))) {
    return shortenHash(text);
  }
  return text;
}

/** Primary line for an infrastructure node card or table cell. */
export function infrastructureTitle(props = {}) {
  const id = props.indicator_id;
  const type = props.indicator_type;
  const value = props.value;
  if (id) {
    if (type) return `${id} (${type})`;
    return id;
  }
  return formatIndicatorValue(value, type);
}

/** Secondary line under the title. */
export function infrastructureDetail(props = {}) {
  const type = props.indicator_type;
  const value = props.value;
  if (!value) return type || "";
  if (type === "hash") return `Hash fingerprint: ${formatIndicatorValue(value, "hash")}`;
  if (type && type !== "hash") return `${type}: ${value}`;
  return String(value);
}

/** Label for relationship endpoints and graph-adjacent lists. */
export function linkNodeLabel(node) {
  const props = node?.properties || node || {};
  if (props.indicator_id) {
    const short = formatIndicatorValue(props.value, props.indicator_type);
    if (props.indicator_type === "hash") {
      return `${props.indicator_id} · ${short}`;
    }
    return `${props.indicator_id} · ${props.value || short}`;
  }
  return (
    props.name ||
    props.actor_id ||
    props.malware_id ||
    props.cve_id ||
    props.campaign_id ||
    props.org_id ||
    ""
  );
}

/** Incident badge text when related_indicators stores raw values. */
export function incidentIndicatorLabel(indicator) {
  const text = String(indicator || "").trim();
  if (text.length > 32 && /^[a-f0-9]+$/i.test(text)) {
    return `hash ${shortenHash(text)}`;
  }
  return text;
}
