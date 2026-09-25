import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.bootstrap import setup_django

setup_django()

from cti_api.auth import hash_password
from cti_api.db.mongo import (
    incidents,
    malware_profiles,
    organizations,
    source_feeds,
    threat_actor_profiles,
    users,
)
from scripts.catalog import build_catalog


def build_incidents(catalog):
    rng = random.Random(7)
    indicators = [item["value"] for item in catalog["infrastructure"]]
    hot = indicators[:8]
    month_plan = []
    for month, count in zip(range(1, 10), [2, 3, 4, 2, 5, 3, 4, 3, 4]):
        month_plan.extend([month] * count)
    severities = (["low", "medium", "high", "critical"] * 8)[:30]
    rng.shuffle(severities)
    feed_names = [feed["name"] for feed in catalog["feeds"]]
    documents = []
    for index, (month, severity) in enumerate(zip(month_plan, severities), start=1):
        picks = [rng.choice(hot)]
        for _ in range(rng.randint(0, 2)):
            picks.append(rng.choice(indicators))
        related = list(dict.fromkeys(picks))
        documents.append(
            {
                "incident_id": f"INC-{index:02d}",
                "source": rng.choice(feed_names),
                "severity": severity,
                "timestamp": datetime(
                    2026,
                    month,
                    rng.randint(1, 27),
                    rng.randint(0, 23),
                    rng.randint(0, 59),
                    tzinfo=timezone.utc,
                ),
                "description": (
                    f"Synthetic report of {severity} activity involving {related[0]} "
                    f"observed by {feed_names[index % len(feed_names)]}."
                ),
                "related_indicators": related,
                "reliability": round(rng.uniform(0.35, 0.98), 2),
            }
        )
    return documents


def seed():
    catalog = build_catalog()
    users_col = users()
    collections = [
        incidents(),
        malware_profiles(),
        threat_actor_profiles(),
        source_feeds(),
        organizations(),
        users_col,
    ]
    for collection in collections:
        collection.delete_many({})

    incident_docs = build_incidents(catalog)
    incidents().insert_many(incident_docs)
    malware_profiles().insert_many(
        [
            {
                "malware_id": item["malware_id"],
                "name": item["name"],
                "family": item["family"],
                "hash": item["hash"],
                "behavior_summary": item["behavior_summary"],
                "first_seen": item["first_seen"],
            }
            for item in catalog["malware"]
        ]
    )
    threat_actor_profiles().insert_many(
        [
            {
                "actor_id": item["actor_id"],
                "aliases": item["aliases"],
                "motivation": item["motivation"],
                "notes": item["notes"],
                "sources": item["sources"],
            }
            for item in catalog["actors"]
        ]
    )
    source_feeds().insert_many(catalog["feeds"])
    organizations().insert_many(catalog["organizations"])
    users_col.insert_many(
        [
            {
                "user_id": item["user_id"],
                "username": item["username"],
                "password_hash": hash_password(item["password"]),
                "role": item["role"],
            }
            for item in catalog["users"]
        ]
    )

    counts = {
        "incident_reports": incidents().count_documents({}),
        "malware_profiles": malware_profiles().count_documents({}),
        "threat_actor_profiles": threat_actor_profiles().count_documents({}),
        "source_feeds": source_feeds().count_documents({}),
        "organizations": organizations().count_documents({}),
        "users": users_col.count_documents({}),
        "admins": users_col.count_documents({"role": "admin"}),
    }
    print(counts)
    counter = Counter(
        indicator for doc in incident_docs for indicator in doc["related_indicators"]
    )
    sample, frequency = counter.most_common(1)[0]
    print(f"Sample indicator to search: {sample} ({frequency} incidents)")
    print("Login: admin / cti-lab-2026")


if __name__ == "__main__":
    seed()
