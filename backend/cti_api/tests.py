import json
from datetime import datetime, timezone

from django.test import Client, TestCase


class ApiTests(TestCase):
    def setUp(self):
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "admin", "password": "cti-lab-2026"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)

    def test_login_rejects_bad_password(self):
        client = Client()
        response = client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "admin", "password": "wrong-password"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_me_requires_cookie(self):
        response = Client().get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_me_returns_role(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["user_id"], "USER-01")
        self.assertEqual(body["role"], "admin")

    def test_mongo_collections_are_seeded(self):
        expected = {
            "/api/incidents/": 30,
            "/api/malware/": 20,
            "/api/actor-profiles/": 15,
            "/api/feeds/": 10,
            "/api/organizations/": 15,
        }
        for path, count in expected.items():
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertGreaterEqual(len(response.json()), count, path)

    def test_incident_crud_round_trip(self):
        payload = {
            "incident_id": "INC-TEST-1",
            "source": "Harbor Watch",
            "severity": "high",
            "timestamp": datetime(2026, 9, 1, tzinfo=timezone.utc).isoformat(),
            "description": "Temporary test incident",
            "related_indicators": ["203.0.113.10"],
            "reliability": 0.5,
        }
        created = self.client.post(
            "/api/incidents/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201, created.content)
        payload["severity"] = "critical"
        updated = self.client.put(
            "/api/incidents/INC-TEST-1/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(updated.status_code, 200, updated.content)
        self.assertEqual(updated.json()["severity"], "critical")
        deleted = self.client.delete("/api/incidents/INC-TEST-1/")
        self.assertEqual(deleted.status_code, 204)
        missing = self.client.get("/api/incidents/INC-TEST-1/")
        self.assertEqual(missing.status_code, 404)

    def test_analytics_endpoints(self):
        checks = {
            "/api/analytics/severity-breakdown/": "severity",
            "/api/analytics/top-indicators/": "indicator",
            "/api/analytics/source-reliability/": "name",
            "/api/analytics/monthly-trend/": "month",
            "/api/analytics/malware-families/": "family",
        }
        for path, field in checks.items():
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            rows = response.json()
            self.assertGreater(len(rows), 0, path)
            self.assertIn(field, rows[0])

    def test_graph_nodes_and_queries(self):
        actors = self.client.get("/api/graph/actors/")
        self.assertEqual(actors.status_code, 200)
        self.assertGreaterEqual(len(actors.json()), 15)
        malware = self.client.get("/api/graph/queries/actor-malware/?actor_id=TA-01")
        self.assertEqual(malware.status_code, 200)
        self.assertGreater(len(malware.json()["records"]), 0)
        infra = self.client.get("/api/graph/queries/malware-infra/?malware_id=MW-01")
        self.assertEqual(infra.status_code, 200)
        campaigns = self.client.get("/api/graph/queries/actor-campaigns/?actor_id=TA-01")
        self.assertEqual(campaigns.status_code, 200)
        shared = self.client.get("/api/graph/queries/shared-infra/")
        self.assertEqual(shared.status_code, 200)
        path = self.client.get("/api/graph/queries/shortest-path/?actor_id=TA-01&org_id=ORG-15")
        self.assertEqual(path.status_code, 200)
        self.assertIsNotNone(path.json()["path"])
        self.assertGreaterEqual(path.json()["path"]["length"], 1)
        self.assertLessEqual(path.json()["path"]["length"], 6)

    def test_search_and_neighborhood(self):
        response = self.client.get("/api/search/?q=INF-01")
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertGreater(len(body["infrastructure"]), 0)
        indicator = body["infrastructure"][0]["properties"]["value"]
        self.assertNotIn("indicator_id", body["infrastructure"][0]["vis"]["label"])
        neighborhood = self.client.get(f"/api/graph/neighborhood/?id={indicator}")
        self.assertEqual(neighborhood.status_code, 200)
        self.assertGreater(len(neighborhood.json()["nodes"]), 0)

    def test_graph_actor_crud_and_relationship(self):
        payload = {"actor_id": "TA-TEST", "name": "Test Cell", "origin": "Nowhere"}
        created = self.client.post(
            "/api/graph/actors/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201, created.content)
        edge = self.client.post(
            "/api/graph/relationships/",
            data=json.dumps({"type": "USES", "from_id": "TA-TEST", "to_id": "MW-01"}),
            content_type="application/json",
        )
        self.assertEqual(edge.status_code, 201, edge.content)
        rel_id = edge.json()["element_id"]
        listed = self.client.get("/api/graph/relationships/?from=TA-TEST")
        self.assertEqual(listed.status_code, 200)
        self.assertTrue(any(item["element_id"] == rel_id for item in listed.json()))
        removed_edge = self.client.delete(f"/api/graph/relationships/?id={rel_id}")
        self.assertEqual(removed_edge.status_code, 204)
        removed_actor = self.client.delete("/api/graph/actors/TA-TEST/")
        self.assertEqual(removed_actor.status_code, 204)
