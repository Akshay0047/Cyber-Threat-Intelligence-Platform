"""Deterministic synthetic catalog shared by the Mongo and Neo4j seed scripts."""

import random
from datetime import datetime, timezone

from faker import Faker

ACTOR_NAMES = [
    "Salted Spider",
    "Blue Nile",
    "Crimson Harbor",
    "Night Kettle",
    "Paper Lantern",
    "Velvet Orbit",
    "Glass Falcon",
    "Red Marlin",
    "Copper Finch",
    "Silent Orchard",
    "Amber Docket",
    "Northwind Cell",
    "Marble Static",
    "Yellow Cairn",
    "Iron Plover",
]
FAMILIES = [
    ("Emotet", "loader", 5),
    ("Qakbot", "loader", 4),
    ("Cobalt Strike", "backdoor", 4),
    ("LockBit", "ransomware", 3),
    ("Agent Tesla", "stealer", 2),
    ("AsyncRAT", "rat", 2),
]
MOTIVATIONS = ["financial", "espionage", "disruption", "hacktivism"]
SECTORS = [
    "finance",
    "healthcare",
    "energy",
    "government",
    "telecommunications",
    "manufacturing",
    "education",
]
FEED_SPECS = [
    ("Harbor Watch", "osint", 0.41),
    ("Northbeam Intel", "commercial", 0.48),
    ("Lantern OSINT", "osint", 0.55),
    ("Copperline Commercial", "commercial", 0.62),
    ("Marble Government Feed", "government", 0.67),
    ("Orchard Internal", "internal", 0.73),
    ("Cairn Sensor Net", "osint", 0.78),
    ("Plover Telecom Feed", "government", 0.84),
    ("Docket Financial ISAC", "commercial", 0.90),
    ("Static Grid Watch", "internal", 0.95),
]
DEMO_PASSWORD = "cti-lab-2026"


def build_catalog():
    fake = Faker()
    Faker.seed(42)
    fake.seed_instance(42)
    rng = random.Random(42)

    feeds = [
        {
            "feed_id": f"FEED-{index:02d}",
            "name": name,
            "type": feed_type,
            "reliability_score": score,
        }
        for index, (name, feed_type, score) in enumerate(FEED_SPECS, start=1)
    ]
    feed_names = [feed["name"] for feed in feeds]

    organizations = []
    used_names = set()
    for index in range(1, 16):
        name = fake.company()
        while name in used_names:
            name = f"{fake.company()} {index}"
        used_names.add(name)
        organizations.append(
            {
                "org_id": f"ORG-{index:02d}",
                "name": name,
                "sector": SECTORS[(index - 1) % len(SECTORS)],
                "country": fake.country(),
            }
        )

    actors = []
    for index, name in enumerate(ACTOR_NAMES, start=1):
        alias = f"{fake.last_name()} {fake.color_name()}"
        actors.append(
            {
                "actor_id": f"TA-{index:02d}",
                "name": name,
                "origin": fake.country(),
                "aliases": [name, alias],
                "motivation": MOTIVATIONS[(index - 1) % len(MOTIVATIONS)],
                "notes": fake.paragraph(nb_sentences=2),
                "sources": rng.sample(feed_names, 2),
            }
        )

    malware = []
    counter = 1
    for family, malware_type, count in FAMILIES:
        for variant in range(1, count + 1):
            malware.append(
                {
                    "malware_id": f"MW-{counter:02d}",
                    "name": f"{family}.{variant}",
                    "family": family,
                    "type": malware_type,
                    "hash": fake.sha256(),
                    "behavior_summary": fake.paragraph(nb_sentences=2),
                    "first_seen": datetime(2025, ((counter - 1) % 12) + 1, min(28, variant * 3), tzinfo=timezone.utc),
                }
            )
            counter += 1

    infrastructure = []
    seen_values = set()
    for index in range(1, 26):
        if index <= 10:
            indicator_type = "ip"
            value = fake.ipv4_public()
        elif index <= 20:
            indicator_type = "domain"
            value = fake.domain_name()
        else:
            indicator_type = "hash"
            value = fake.sha256()
        while value in seen_values:
            value = fake.sha256() if indicator_type == "hash" else fake.domain_name()
        seen_values.add(value)
        infrastructure.append(
            {
                "indicator_id": f"INF-{index:02d}",
                "value": value,
                "indicator_type": indicator_type,
            }
        )

    vulnerabilities = [
        {
            "cve_id": f"CVE-2026-{1000 + index}",
            "severity_score": round(rng.uniform(4.0, 9.8), 1),
        }
        for index in range(1, 16)
    ]
    campaigns = [
        {
            "campaign_id": f"CAMP-{index:02d}",
            "name": f"Operation {fake.word().title()} {fake.word().title()}",
            "start_date": f"2026-{((index - 1) % 9) + 1:02d}-15",
        }
        for index in range(1, 16)
    ]

    users = [
        {"user_id": "USER-01", "username": "admin", "password": DEMO_PASSWORD, "role": "admin"},
        {"user_id": "USER-02", "username": "admin2", "password": DEMO_PASSWORD, "role": "admin"},
    ]
    for index in range(1, 9):
        users.append(
            {
                "user_id": f"USER-{index + 2:02d}",
                "username": f"analyst{index}",
                "password": DEMO_PASSWORD,
                "role": "analyst",
            }
        )

    return {
        "feeds": feeds,
        "organizations": organizations,
        "actors": actors,
        "malware": malware,
        "infrastructure": infrastructure,
        "vulnerabilities": vulnerabilities,
        "campaigns": campaigns,
        "users": users,
    }
