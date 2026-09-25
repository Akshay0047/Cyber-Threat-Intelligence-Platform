import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.bootstrap import setup_django

setup_django()

from cti_api.db.neo4j import get_driver, write_transaction
from scripts.catalog import build_catalog
from scripts.graph_plan import build_relationships, verify


def _ids(items, key):
    return [item[key] for item in items]


def seed():
    catalog = build_catalog()
    nodes = {
        "ThreatActor": _ids(catalog["actors"], "actor_id"),
        "Malware": _ids(catalog["malware"], "malware_id"),
        "Infrastructure": _ids(catalog["infrastructure"], "indicator_id"),
        "Vulnerability": _ids(catalog["vulnerabilities"], "cve_id"),
        "Campaign": _ids(catalog["campaigns"], "campaign_id"),
        "Organization": _ids(catalog["organizations"], "org_id"),
    }
    edges = build_relationships(
        nodes["ThreatActor"],
        nodes["Malware"],
        nodes["Infrastructure"],
        nodes["Vulnerability"],
        nodes["Campaign"],
        nodes["Organization"],
    )
    stats = verify(edges, nodes)

    def work(tx):
        tx.run("MATCH (n) DETACH DELETE n").consume()
        for actor in catalog["actors"]:
            tx.run(
                "CREATE (:ThreatActor {actor_id: $actor_id, name: $name, origin: $origin})",
                actor_id=actor["actor_id"],
                name=actor["name"],
                origin=actor["origin"],
            ).consume()
        for malware in catalog["malware"]:
            tx.run(
                "CREATE (:Malware {malware_id: $malware_id, name: $name, type: $type})",
                malware_id=malware["malware_id"],
                name=malware["name"],
                type=malware["type"],
            ).consume()
        for infra in catalog["infrastructure"]:
            tx.run(
                """
                CREATE (:Infrastructure {
                    indicator_id: $indicator_id,
                    value: $value,
                    indicator_type: $indicator_type
                })
                """,
                **infra,
            ).consume()
        for vuln in catalog["vulnerabilities"]:
            tx.run(
                "CREATE (:Vulnerability {cve_id: $cve_id, severity_score: $severity_score})",
                **vuln,
            ).consume()
        for campaign in catalog["campaigns"]:
            tx.run(
                "CREATE (:Campaign {campaign_id: $campaign_id, name: $name, start_date: $start_date})",
                **campaign,
            ).consume()
        for org in catalog["organizations"]:
            tx.run(
                "CREATE (:Organization {org_id: $org_id, name: $name, sector: $sector})",
                org_id=org["org_id"],
                name=org["name"],
                sector=org["sector"],
            ).consume()
        for edge in edges:
            created = list(
                tx.run(
                    f"""
                    MATCH (a:{edge['from_label']} {{{edge['from_key']}: $from_id}})
                    MATCH (b:{edge['to_label']} {{{edge['to_key']}: $to_id}})
                    CREATE (a)-[r:{edge['type']}]->(b)
                    RETURN type(r) AS type
                    """,
                    from_id=edge["from_id"],
                    to_id=edge["to_id"],
                )
            )
            if not created:
                raise RuntimeError(f"Failed to create {edge}")

    write_transaction(work)
    with get_driver().session() as session:
        orphan_count = session.run(
            "MATCH (n) WHERE NOT (n)--() RETURN count(n) AS orphans"
        ).single()["orphans"]
        rel_counts = {
            record["type"]: record["count"]
            for record in session.run("MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count")
        }
    if orphan_count:
        raise SystemExit(f"Seed left {orphan_count} orphan nodes")
    print("Planned", stats)
    print("Stored relationships", rel_counts)
    print("Shortest-path sample: actor_id=TA-01 org_id=ORG-15")
    print("Shared-infra sample should be non-empty (bridge malware touches two indicators).")
    print("Relationship total", sum(rel_counts.values()), "expected", sum(Counter(e["type"] for e in edges).values()))


if __name__ == "__main__":
    seed()
