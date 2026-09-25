from django.conf import settings
from neo4j import GraphDatabase
from neo4j.graph import Node, Path, Relationship

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_timeout=3,
        )
    return _driver


def _json_safe(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return isoformat()
    return str(value)


def _display(props, labels):
    for key in (
        "name",
        "value",
        "actor_id",
        "malware_id",
        "indicator_id",
        "cve_id",
        "campaign_id",
        "org_id",
    ):
        if props.get(key):
            return str(props[key])
    return labels[0] if labels else "node"


def node_to_dict(node):
    labels = list(node.labels)
    props = {key: _json_safe(value) for key, value in dict(node).items()}
    label = labels[0] if labels else "Node"
    title = _display(props, labels)
    return {
        "element_id": node.element_id,
        "labels": labels,
        "properties": props,
        "vis": {
            "id": node.element_id,
            "label": f"{label}: {title}",
            "group": label,
            "title": "\n".join(f"{key}: {value}" for key, value in props.items()),
        },
    }


def rel_to_dict(rel):
    start = getattr(rel, "start_node", None)
    end = getattr(rel, "end_node", None)
    payload = {
        "element_id": rel.element_id,
        "type": rel.type,
        "properties": {key: _json_safe(value) for key, value in dict(rel).items()},
    }
    if start is not None:
        payload["start"] = start.element_id
    if end is not None:
        payload["end"] = end.element_id
    if payload.get("start") and payload.get("end"):
        payload["vis"] = {
            "id": rel.element_id,
            "from": payload["start"],
            "to": payload["end"],
            "label": rel.type,
        }
    return payload


def path_to_dict(path):
    return {
        "nodes": [node_to_dict(node) for node in path.nodes],
        "relationships": [rel_to_dict(rel) for rel in path.relationships],
        "length": len(path.relationships),
    }


def _convert(value):
    if isinstance(value, Node):
        return node_to_dict(value)
    if isinstance(value, Relationship):
        return rel_to_dict(value)
    if isinstance(value, Path):
        return path_to_dict(value)
    if isinstance(value, list):
        return [_convert(item) for item in value]
    return _json_safe(value)


def read_query(cypher, parameters=None):
    parameters = parameters or {}
    with get_driver().session() as session:
        result = session.run(cypher, **parameters)
        return [{key: _convert(record[key]) for key in record.keys()} for record in result]


def write_transaction(work):
    """Run work(tx) inside a single Neo4j write transaction."""
    with get_driver().session() as session:
        return session.execute_write(work)
