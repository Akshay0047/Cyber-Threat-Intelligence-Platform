# Presentation guide

Use this while preparing and while presenting. Setup commands live in `README.md`. The website itself does not show the course code or the database product names. Say those names out loud. They are part of the design.

Repository: https://github.com/Akshay0047/Cyber-Threat-Intelligence-Platform

## One-minute pitch

This is a cyber threat intelligence platform. Analysts sign in, search indicators, browse records, explore how actors, malware, infrastructure, and victims connect, and read summary charts.

Two stores are used on purpose:

- **MongoDB** holds documents that do not share one rigid shape: incident reports, malware profiles, threat-actor profiles, source feeds, organizations, and users.
- **Neo4j** holds the relationship graph. The interesting questions are paths and shared neighbors, which a document store answers poorly.
- **Django REST Framework** is only the API. Views call **PyMongo** and the official **Neo4j Bolt driver** directly. There is no ORM, no Djongo, no mongoengine, and no py2neo.
- **React** (Vite, Tailwind) is the analyst UI. It never talks to the databases. Every call goes through `/api`.

## What to have running before you walk in

1. MongoDB is already installed locally and must be listening on port **27017**.
2. Start Docker Desktop, then start the graph database:

   ```powershell
   docker start cti-neo4j
   ```

   That container is Neo4j 5. Browser UI is http://localhost:7474. Bolt is `bolt://localhost:7687`. User `neo4j`, password `cti-password`.
3. From `backend`, with the virtual environment active:

   ```powershell
   .\.venv\Scripts\python.exe manage.py runserver
   ```

4. From `frontend`:

   ```powershell
   npm run dev
   ```

5. Open http://localhost:5173.

If the graph container is stopped, document pages still load and the graph pages show “The relationship graph is unavailable.” If MongoDB is stopped, record pages show “Stored records are unavailable.”

`backend/.env` is local only and is not in git. It sets `MONGO_URI`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, and `JWT_SECRET`.

## Demo login

Password for every seeded user: `cti-lab-2026`

| Username | Role | Id |
| --- | --- | --- |
| admin | admin | USER-01 |
| admin2 | admin | USER-02 |
| analyst1 … analyst8 | analyst | USER-03 … USER-10 |

There is no registration page. That is a requirement, not a missing feature. Logout clears the cookie.

## Suggested demo, about six minutes

Sign in as **admin** / **cti-lab-2026**. The sidebar then shows `USER-01 / admin`.

1. **Search.** Type `INF-01` and search. Point at the incident cards (those documents live in MongoDB) and the neighborhood drawing (that walk lives in Neo4j). Infrastructure is labeled with its indicator value, such as an IP, domain, or shortened hash, not the internal id.
2. **Entities.** Open Incidents and show `INC-01`. Mention that each collection can be created, edited, and deleted. Open Graph actors and show `TA-01`. Open Relationships and point out that a relationship can be deleted but not edited. Changing a link means delete and create.
3. **Graph.** The form is already filled with `TA-01`, `MW-01`, and `ORG-15`. Run **Shortest path**. Say that `TA-01` (Salted Spider) reaches `ORG-15` in at most six hops, and that this pair crosses communities. Then run **Actor malware** to show what Salted Spider uses.
4. **Analytics.** Severity bars are Low, Medium, High, and Critical. With the seed data that is 8, 8, 7, and 7. Malware families are Emotet 5, Qakbot 4, Cobalt Strike 4, LockBit 3, Agent Tesla 2, AsyncRAT 2. The other charts are the ten most common indicators, feeds ranked by reliability, and incident counts from January through September 2026.

If a reviewer wants a write, create a throwaway incident such as `INC-99` and delete it before you finish. Re-running the seed scripts wipes everything and reloads the same synthetic set.

## Architecture to draw on the board

```text
Browser (React, port 5173)
        |  credentials: include
        |  Vite proxies /api to Django
        v
Django REST (port 8000)
        |                         |
        | PyMongo                 | neo4j Bolt driver
        v                         v
MongoDB :27017                Neo4j Bolt :7687
database cti                  user neo4j
```

The Vite proxy matters. The JWT cookie is set by Django and must be first-party. The browser calls `http://localhost:5173/api/...`, and Vite forwards that to `http://127.0.0.1:8000`. Django’s unused default database is SQLite and stores nothing for this app.

## Authentication, said simply

- Login is `POST /api/auth/login/`. The password is checked with **bcrypt** against `password_hash` in the `users` collection.
- A **PyJWT** token is written into an **httpOnly** cookie named `cti_jwt`. Lifetime is 12 hours. `SameSite=Lax`. JavaScript cannot read the cookie, so a page script cannot steal it.
- Custom middleware checks that cookie on every other `/api/` route. Login and logout are the exceptions. Django session auth is not used. DRF authentication classes are empty.
- A missing or bad cookie returns 401. The UI then sends the analyst back to the login page and shows a toast.
- `GET /api/auth/me/` returns `user_id` and `role`.

## MongoDB

Database name: `cti`, from `mongodb://localhost:27017/cti`.

| Collection | Count | Business id | Fields |
| --- | --- | --- | --- |
| incident_reports | 30 | incident_id | source, severity, timestamp, description, related_indicators, reliability (0–1) |
| malware_profiles | 20 | malware_id | name, family, hash, behavior_summary, first_seen |
| threat_actor_profiles | 15 | actor_id | aliases, motivation, notes, sources |
| source_feeds | 10 | feed_id | name, type, reliability_score (0.41–0.95) |
| organizations | 15 | org_id | name, sector, country |
| users | 10 | user_id | username, password_hash, role (`analyst` or `admin`) |

Severities: `low`, `medium`, `high`, `critical`. Motivations: `financial`, `espionage`, `disruption`, `hacktivism`. Feed types: `osint`, `commercial`, `government`, `internal`. Sectors: finance, healthcare, energy, government, telecommunications, manufacturing, education.

Incidents are dated January–September 2026. Monthly counts are 2, 3, 4, 2, 5, 3, 4, 3, 4.

Indexes, all on `incident_reports`:

- unique index on `incident_id`
- multikey index on `related_indicators` so one incident can be found by any of its indicators
- compound index `{severity: 1, timestamp: -1}` for “this severity, newest first”

Analytics are MongoDB aggregation pipelines, not rows counted in Python:

- severity breakdown groups by `severity`
- top indicators unwinds `related_indicators`, counts them, and keeps 10
- source reliability sorts feeds by `reliability_score`
- monthly trend groups timestamps as `YYYY-MM`
- malware families groups profiles by `family`

## Neo4j

105 nodes. Ids are shared with the documents where both stores describe the same thing (`TA-01` is the same actor in both).

| Label | Count | Id property | Other properties |
| --- | --- | --- | --- |
| ThreatActor | 15 | actor_id | name, origin |
| Malware | 20 | malware_id | name, type |
| Infrastructure | 25 | indicator_id | value, indicator_type (`ip`, `domain`, or `hash`) |
| Vulnerability | 15 | cve_id | severity_score |
| Campaign | 15 | campaign_id | name, start_date |
| Organization | 15 | org_id | name, sector |

`INF-01` through `INF-10` are public IPs, `INF-11` through `INF-20` are domains, and `INF-21` through `INF-25` are SHA-256 hashes. Vulnerabilities are `CVE-2026-1001` through `CVE-2026-1015`.

Constraints make each id unique. There is also an index on `Infrastructure.value` because search looks up indicator text.

Relationship direction is part of the meaning. An arrow the other way would be a different fact.

| Relationship | Direction | Count |
| --- | --- | --- |
| USES | ThreatActor → Malware | 20 |
| COMMUNICATES_WITH | Malware → Infrastructure | 25 |
| EXPLOITS | Malware → Vulnerability | 20 |
| PART_OF | Malware → Campaign, and Infrastructure → Campaign | 30 |
| TARGETS | Campaign → Organization | 15 |
| ATTRIBUTED_TO | Campaign → ThreatActor | 15 |

How the seed keeps the graph usable:

- Nodes are split into three communities.
- Each community has one hub campaign. Every malware sample in that community is `PART_OF` the hub. The hub `TARGETS` every organization in the community.
- Each campaign is `ATTRIBUTED_TO` exactly one actor.
- Three infrastructure nodes are bridges: malware in the next community also `COMMUNICATES_WITH` them, and each bridge is still `PART_OF` its home hub.
- The result is one connected component, no orphan nodes, and every actor can reach every organization in **at most 6 undirected hops**. `shortestPath` is queried with `[*..6]`.

`TA-01` is Salted Spider. `MW-01` is Emotet.1. `TA-01` to `ORG-15` is the cross-community path to show.

Graph writes that touch more than one statement, including a batch of relationships, run inside one write transaction. Relationship type is not a Cypher parameter. The API allowlists the six types and then interpolates the chosen type. `PART_OF` may start from either a malware id or an infrastructure id.

## API map

All paths are under `/api/`. List and create use the collection URL. Read, update, and delete use the business id.

| Area | Method and path |
| --- | --- |
| Login | POST `/api/auth/login/` |
| Logout | POST `/api/auth/logout/` |
| Current user | GET `/api/auth/me/` |
| Incidents, malware profiles, actor profiles, feeds, organizations | GET/POST `/api/incidents/`, `/api/malware/`, `/api/actor-profiles/`, `/api/feeds/`, `/api/organizations/` and the same path plus `/{id}/` for GET, PUT, DELETE |
| Graph nodes | `/api/graph/actors/`, `/api/graph/malware/`, `/api/graph/infra/` with the same CRUD pattern |
| Relationships | POST `/api/graph/relationships/` with one edge or a batch. GET `?from=&to=`. DELETE by element id. No update. |
| Actor’s malware | GET `/api/graph/queries/actor-malware/?actor_id=TA-01` |
| Malware’s infrastructure | GET `/api/graph/queries/malware-infra/?malware_id=MW-01` |
| Actor’s campaigns and targets | GET `/api/graph/queries/actor-campaigns/?actor_id=TA-01` |
| Infrastructure used by more than one malware | GET `/api/graph/queries/shared-infra/` |
| Shortest path | GET `/api/graph/queries/shortest-path/?actor_id=TA-01&org_id=ORG-15` |
| Neighbors of any id or indicator value | GET `/api/graph/neighborhood/?id=` |
| Search | GET `/api/search/?q=` |
| Analytics | GET `/api/analytics/severity-breakdown/`, `top-indicators/`, `source-reliability/`, `monthly-trend/`, `malware-families/` |

Search matches incident `related_indicators` with a regular expression and matches infrastructure by `value` or `indicator_id`.

## Frontend pages

| Page | Route | What it shows |
| --- | --- | --- |
| Login | `/login` | Username and password. Demo password is printed on the card. |
| Search | `/search` | Indicator search, incident cards, neighborhood graph. |
| Entities | `/entities` | Five document collections, three graph-node collections, and relationships. |
| Graph | `/graph` | The five Cypher queries, drawn with vis-network. |
| Analytics | `/analytics` | Five bar charts. Severity labels are capitalized in the UI. |

Node colors: threat actor red, malware orange, infrastructure blue, vulnerability purple, campaign teal, organization green. Organization green means the victim, not “this node is safe.”

## Data you can quote

- Seed is synthetic. Faker and Python `random` use fixed seeds (`42` for the catalog, `7` for incidents), so a re-seed reproduces the same records.
- Actor display names are fictional: Salted Spider, Blue Nile, Crimson Harbor, Night Kettle, Paper Lantern, Velvet Orbit, Glass Falcon, Red Marlin, Copper Finch, Silent Orchard, Amber Docket, Northwind Cell, Marble Static, Yellow Cairn, Iron Plover.
- Feed reliability runs from Harbor Watch at 0.41 up to Static Grid Watch at 0.95.
- Passwords are stored only as bcrypt hashes.

## Questions they may ask

**Why not store everything in one database?**  
Incidents, profiles, and feeds are documents. “Who can reach this victim, and through what malware?” is a path query. Each store is used for the question it answers well. Shared ids (`TA-01`, `ORG-01`, `MW-01`) are how the two sides refer to the same real-world object.

**Why is there no ORM?**  
The requirement is a manual data layer. Views call PyMongo and the Bolt driver. Django’s SQLite entry exists only because Django requires a `DATABASES` setting. No application data is migrated into it.

**Why is the cookie httpOnly?**  
So page scripts cannot read the token. The Vite proxy keeps the cookie on the same origin as the UI.

**Why can a relationship be deleted but not updated?**  
A relationship is a typed directed edge. Replacing it is a new edge. The API exposes create and delete only.

**How do you know the graph is connected?**  
`scripts/graph_plan.py` checks the plan before anything is inserted: exact relationship counts, no orphans, one component, and a maximum actor-to-organization distance of 6. `scripts/seed_neo4j.py` then deletes the old graph and writes nodes and edges in one transaction.

**What are the indexes for?**  
Unique `incident_id` stops duplicate reports. The multikey index serves indicator search. The compound severity/timestamp index serves filtered, time-ordered incident lists. Neo4j uniqueness constraints stop duplicate node ids, and the value index serves indicator lookup.

**Where do the charts come from?**  
MongoDB aggregation, computed when the page asks. They are not stored as a separate collection.

**Is the data real?**  
No. It is synthetic, generated for the lab, and safe to wipe.

## What was verified

- `python manage.py test cti_api` — 9 tests: bad password, cookie required, seeded counts, incident create/update/delete, all five analytics endpoints, graph queries including a shortest path of length 1 to 6, search, and create/delete of a graph actor plus a `USES` edge.
- Playwright in `frontend/e2e/pages.spec.js` — 6 tests: login layout, no overlapping controls on Search, Entities, Graph, and Analytics, and those pages rendering real data (`INF-01`, `INC-01`, `TA-01`, a hop count, and the words Critical and Low).

Both suites need the two databases running. The Playwright suite also needs Django on port 8000 and Vite on port 5173.
