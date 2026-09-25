# Cyber Threat Intelligence Platform

Lab project for BCSE302P. MongoDB stores documents, Neo4j stores the relationship graph, and Django REST Framework exposes both through a manual data layer (PyMongo and the Neo4j Bolt driver, not an ORM). The React UI signs in with an httpOnly JWT cookie.

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB listening on port 27017
- Neo4j 5 listening on Bolt port 7687

Optional containers:

```powershell
docker run -d --name cti-mongo -p 27017:27017 mongo:7
docker run -d --name cti-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/cti-password neo4j:5
```

## Setup

From `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and set `MONGO_URI`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, and `JWT_SECRET`. Include the database name in the Mongo URI (`mongodb://localhost:27017/cti`). If you used the Docker command above, set `NEO4J_PASSWORD=cti-password`.

```powershell
python scripts\create_indexes.py
python scripts\seed_mongo.py
python scripts\seed_neo4j.py
python manage.py runserver
```

From `frontend`:

```powershell
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to Django so the auth cookie stays on one origin.

## Demo login

All 10 seeded users share the password `cti-lab-2026`.

| Username | Role |
| --- | --- |
| admin, admin2 | admin |
| analyst1 … analyst8 | analyst |

There is no registration page. Re-running the seed scripts wipes and reloads synthetic data.

## What to click

- **Search** — paste an indicator value printed by `seed_mongo.py`. Incident documents come from MongoDB; the neighborhood graph comes from Neo4j.
- **Collections** — list, create, update, and delete the five MongoDB collections.
- **Graph** — run the five Cypher queries. `TA-01` to `ORG-15` is a cross-community shortest path.
- **Analytics** — severity, top indicators, feed reliability, monthly incident trend, and malware families.

## Schema

MongoDB collections: `incident_reports`, `malware_profiles`, `threat_actor_profiles`, `source_feeds`, `organizations`, `users`.

Neo4j labels: `ThreatActor`, `Malware`, `Infrastructure`, `Vulnerability`, `Campaign`, `Organization`.

Relationships: `USES`, `COMMUNICATES_WITH`, `EXPLOITS`, `PART_OF`, `TARGETS`, `ATTRIBUTED_TO`.

The seed builds one connected graph: 15 actors, 20 malware, 25 infrastructure, 15 vulnerabilities, 15 campaigns, 15 organizations, and at least 20 / 25 / 20 / 30 / 15 / 15 of those relationship types. Every actor can reach every organization in at most six hops.
