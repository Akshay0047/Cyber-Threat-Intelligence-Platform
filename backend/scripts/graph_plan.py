"""Relationship plan for the seeded Neo4j graph.

Counts match the review minimums exactly, and every actor can reach every
organization in at most 6 undirected hops.
"""

from collections import defaultdict, deque

MINIMUMS = {
    "USES": 20,
    "COMMUNICATES_WITH": 25,
    "EXPLOITS": 20,
    "PART_OF": 30,
    "TARGETS": 15,
    "ATTRIBUTED_TO": 15,
}
SCHEMA = {
    "USES": {("ThreatActor", "Malware")},
    "COMMUNICATES_WITH": {("Malware", "Infrastructure")},
    "EXPLOITS": {("Malware", "Vulnerability")},
    "PART_OF": {("Malware", "Campaign"), ("Infrastructure", "Campaign")},
    "TARGETS": {("Campaign", "Organization")},
    "ATTRIBUTED_TO": {("Campaign", "ThreatActor")},
}
KEYS = {
    "ThreatActor": "actor_id",
    "Malware": "malware_id",
    "Infrastructure": "indicator_id",
    "Vulnerability": "cve_id",
    "Campaign": "campaign_id",
    "Organization": "org_id",
}


def split_communities(items, groups=3):
    count = len(items)
    base, extra = divmod(count, groups)
    chunks = []
    index = 0
    for group in range(groups):
        size = base + (1 if group < extra else 0)
        chunks.append(items[index : index + size])
        index += size
    return chunks


def _edge(rel_type, from_label, from_id, to_label, to_id):
    return {
        "type": rel_type,
        "from_label": from_label,
        "from_key": KEYS[from_label],
        "from_id": from_id,
        "to_label": to_label,
        "to_key": KEYS[to_label],
        "to_id": to_id,
    }


def build_relationships(actors, malware, infrastructure, vulnerabilities, campaigns, organizations):
    actor_groups = split_communities(actors)
    malware_groups = split_communities(malware)
    infra_groups = split_communities(infrastructure)
    vuln_groups = split_communities(vulnerabilities)
    camp_groups = split_communities(campaigns)
    org_groups = split_communities(organizations)
    edges = []
    bridges = []

    for group in range(3):
        group_actors = actor_groups[group]
        group_malware = malware_groups[group]
        group_infra = infra_groups[group]
        group_vulns = vuln_groups[group]
        group_camps = camp_groups[group]
        group_orgs = org_groups[group]
        hub = group_camps[0]

        for index, malware_id in enumerate(group_malware):
            edges.append(
                _edge("USES", "ThreatActor", group_actors[index % len(group_actors)], "Malware", malware_id)
            )
            edges.append(
                _edge("EXPLOITS", "Malware", malware_id, "Vulnerability", group_vulns[index % len(group_vulns)])
            )
            edges.append(_edge("PART_OF", "Malware", malware_id, "Campaign", hub))

        for index in range(len(group_malware)):
            edges.append(
                _edge(
                    "COMMUNICATES_WITH",
                    "Malware",
                    group_malware[index],
                    "Infrastructure",
                    group_infra[index],
                )
            )
        extras = group_infra[len(group_malware) :]
        for extra in extras[:-1]:
            edges.append(
                _edge("COMMUNICATES_WITH", "Malware", group_malware[0], "Infrastructure", extra)
            )
        bridges.append(extras[-1])

        for index, campaign_id in enumerate(group_camps):
            edges.append(
                _edge("ATTRIBUTED_TO", "Campaign", campaign_id, "ThreatActor", group_actors[index])
            )
        for org_id in group_orgs:
            edges.append(_edge("TARGETS", "Campaign", hub, "Organization", org_id))

    for group, infra_id in enumerate(bridges):
        target_malware = malware_groups[(group + 1) % 3][0]
        edges.append(
            _edge("COMMUNICATES_WITH", "Malware", target_malware, "Infrastructure", infra_id)
        )

    chosen = []
    seen = set()
    for group, infra_id in enumerate(bridges):
        chosen.append((infra_id, camp_groups[group][0]))
        seen.add(infra_id)
    for group in range(3):
        hub = camp_groups[group][0]
        for infra_id in infra_groups[group]:
            if len(chosen) >= 10:
                break
            if infra_id in seen:
                continue
            chosen.append((infra_id, hub))
            seen.add(infra_id)
    for infra_id, hub in chosen:
        edges.append(_edge("PART_OF", "Infrastructure", infra_id, "Campaign", hub))
    return edges


def _node_key(label, node_id):
    return (label, node_id)


def verify(edges, nodes_by_label):
    counts = defaultdict(int)
    seen_edges = set()
    for edge in edges:
        pair = (edge["from_label"], edge["to_label"])
        if pair not in SCHEMA[edge["type"]]:
            raise AssertionError(f"Bad direction for {edge}")
        signature = (edge["type"], edge["from_label"], edge["from_id"], edge["to_label"], edge["to_id"])
        if signature in seen_edges:
            raise AssertionError(f"Duplicate edge {signature}")
        seen_edges.add(signature)
        counts[edge["type"]] += 1
    for rel_type, minimum in MINIMUMS.items():
        if counts[rel_type] < minimum:
            raise AssertionError(f"{rel_type} count {counts[rel_type]} < {minimum}")

    adjacency = defaultdict(set)
    all_nodes = []
    for label, node_ids in nodes_by_label.items():
        for node_id in node_ids:
            all_nodes.append(_node_key(label, node_id))
    for node in all_nodes:
        adjacency[node]
    for edge in edges:
        left = _node_key(edge["from_label"], edge["from_id"])
        right = _node_key(edge["to_label"], edge["to_id"])
        adjacency[left].add(right)
        adjacency[right].add(left)

    orphans = [node for node, neighbors in adjacency.items() if not neighbors]
    if orphans:
        raise AssertionError(f"Orphan nodes: {orphans[:5]}")

    start = all_nodes[0]
    seen = set()
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(adjacency[current] - seen)
    if len(seen) != len(all_nodes):
        raise AssertionError(f"Graph has multiple components ({len(seen)}/{len(all_nodes)})")

    distances = []
    for actor_id in nodes_by_label["ThreatActor"]:
        origin = _node_key("ThreatActor", actor_id)
        dist = {origin: 0}
        queue = deque([origin])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in dist:
                    dist[neighbor] = dist[current] + 1
                    queue.append(neighbor)
        for org_id in nodes_by_label["Organization"]:
            hop = dist.get(_node_key("Organization", org_id))
            if hop is None or hop > 6 or hop < 1:
                raise AssertionError(f"Path {actor_id} -> {org_id} has distance {hop}")
            distances.append(hop)
    return {"counts": dict(counts), "max_actor_org_distance": max(distances), "nodes": len(all_nodes)}


def _demo_ids():
    return {
        "ThreatActor": [f"TA-{i:02d}" for i in range(1, 16)],
        "Malware": [f"MW-{i:02d}" for i in range(1, 21)],
        "Infrastructure": [f"INF-{i:02d}" for i in range(1, 26)],
        "Vulnerability": [f"CVE-2026-{1000 + i}" for i in range(1, 16)],
        "Campaign": [f"CAMP-{i:02d}" for i in range(1, 16)],
        "Organization": [f"ORG-{i:02d}" for i in range(1, 16)],
    }


if __name__ == "__main__":
    nodes = _demo_ids()
    edges = build_relationships(
        nodes["ThreatActor"],
        nodes["Malware"],
        nodes["Infrastructure"],
        nodes["Vulnerability"],
        nodes["Campaign"],
        nodes["Organization"],
    )
    stats = verify(edges, nodes)
    print(stats)
