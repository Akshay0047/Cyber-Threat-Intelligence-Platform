import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.bootstrap import setup_django

setup_django()

from cti_api.db.mongo import incidents
from cti_api.db.neo4j import get_driver


MONGO_INDEXES = [
    ("incident_id", {"unique": True, "name": "incident_id_unique"}),
    ("related_indicators", {"name": "related_indicators_multikey"}),
]

NEO4J_STATEMENTS = [
    "CREATE CONSTRAINT threat_actor_actor_id IF NOT EXISTS FOR (n:ThreatActor) REQUIRE n.actor_id IS UNIQUE",
    "CREATE CONSTRAINT malware_malware_id IF NOT EXISTS FOR (n:Malware) REQUIRE n.malware_id IS UNIQUE",
    "CREATE CONSTRAINT infrastructure_indicator_id IF NOT EXISTS FOR (n:Infrastructure) REQUIRE n.indicator_id IS UNIQUE",
    "CREATE CONSTRAINT vulnerability_cve_id IF NOT EXISTS FOR (n:Vulnerability) REQUIRE n.cve_id IS UNIQUE",
    "CREATE CONSTRAINT campaign_campaign_id IF NOT EXISTS FOR (n:Campaign) REQUIRE n.campaign_id IS UNIQUE",
    "CREATE CONSTRAINT organization_org_id IF NOT EXISTS FOR (n:Organization) REQUIRE n.org_id IS UNIQUE",
    "CREATE INDEX infrastructure_value IF NOT EXISTS FOR (n:Infrastructure) ON (n.value)",
]


def create_mongo_indexes():
    collection = incidents()
    collection.create_index("incident_id", unique=True, name="incident_id_unique")
    collection.create_index("related_indicators", name="related_indicators_multikey")
    collection.create_index(
        [("severity", 1), ("timestamp", -1)],
        name="severity_timestamp",
    )
    print("MongoDB indexes:", sorted(collection.index_information()))


def create_neo4j_constraints():
    with get_driver().session() as session:
        for statement in NEO4J_STATEMENTS:
            session.run(statement).consume()
            print("Neo4j:", statement.split(" FOR ")[0])


if __name__ == "__main__":
    create_mongo_indexes()
    create_neo4j_constraints()
    print("Indexes and constraints are ready.")
