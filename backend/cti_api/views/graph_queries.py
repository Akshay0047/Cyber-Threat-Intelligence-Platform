from rest_framework.response import Response
from rest_framework.views import APIView

from cti_api.db.neo4j import read_query

ACTOR_MALWARE = """
MATCH (a:ThreatActor {actor_id:$actor_id})-[:USES]->(m:Malware)
RETURN m
"""

MALWARE_INFRA = """
MATCH (m:Malware {malware_id:$malware_id})-[:COMMUNICATES_WITH]->(i:Infrastructure)
RETURN i
"""

ACTOR_CAMPAIGNS = """
MATCH (c:Campaign)-[:ATTRIBUTED_TO]->(a:ThreatActor {actor_id:$actor_id}),
      (c)-[:TARGETS]->(o:Organization)
RETURN c, o
"""

SHARED_INFRA = """
MATCH (i:Infrastructure)<-[:COMMUNICATES_WITH]-(m:Malware)
WITH i, count(DISTINCT m) AS malwareCount
WHERE malwareCount > 1
RETURN i, malwareCount
ORDER BY malwareCount DESC
"""

SHORTEST_PATH = """
MATCH p = shortestPath(
  (a:ThreatActor {actor_id:$actor_id})-[*..6]-(o:Organization {org_id:$org_id})
)
RETURN p
"""


def _graph_from_nodes(nodes):
    seen = {}
    for node in nodes:
        if node and node.get("element_id"):
            seen[node["element_id"]] = node["vis"]
    return {"nodes": list(seen.values()), "edges": []}


class ActorMalwareQuery(APIView):
    def get(self, request):
        actor_id = request.query_params.get("actor_id", "")
        if not actor_id:
            return Response({"detail": "actor_id is required"}, status=400)
        rows = read_query(ACTOR_MALWARE, {"actor_id": actor_id})
        nodes = [row["m"] for row in rows]
        return Response({"records": nodes, "graph": _graph_from_nodes(nodes)})


class MalwareInfraQuery(APIView):
    def get(self, request):
        malware_id = request.query_params.get("malware_id", "")
        if not malware_id:
            return Response({"detail": "malware_id is required"}, status=400)
        rows = read_query(MALWARE_INFRA, {"malware_id": malware_id})
        nodes = [row["i"] for row in rows]
        return Response({"records": nodes, "graph": _graph_from_nodes(nodes)})


class ActorCampaignsQuery(APIView):
    def get(self, request):
        actor_id = request.query_params.get("actor_id", "")
        if not actor_id:
            return Response({"detail": "actor_id is required"}, status=400)
        rows = read_query(ACTOR_CAMPAIGNS, {"actor_id": actor_id})
        nodes = []
        records = []
        for row in rows:
            records.append({"campaign": row["c"], "organization": row["o"]})
            nodes.extend([row["c"], row["o"]])
        return Response({"records": records, "graph": _graph_from_nodes(nodes)})


class SharedInfraQuery(APIView):
    def get(self, request):
        rows = read_query(SHARED_INFRA)
        records = []
        vis_nodes = []
        for row in rows:
            node = row["i"]
            count = row["malwareCount"]
            vis = dict(node["vis"])
            vis["label"] = f"{vis['label']}\nshared by {count}"
            records.append({"infrastructure": node, "malwareCount": count})
            vis_nodes.append(vis)
        return Response({"records": records, "graph": {"nodes": vis_nodes, "edges": []}})


class ShortestPathQuery(APIView):
    def get(self, request):
        actor_id = request.query_params.get("actor_id", "")
        org_id = request.query_params.get("org_id", "")
        if not actor_id or not org_id:
            return Response({"detail": "actor_id and org_id are required"}, status=400)
        rows = read_query(SHORTEST_PATH, {"actor_id": actor_id, "org_id": org_id})
        if not rows:
            return Response({"records": [], "path": None, "graph": {"nodes": [], "edges": []}})
        path = rows[0]["p"]
        edges = []
        for rel in path["relationships"]:
            if rel.get("vis"):
                edges.append(rel["vis"])
            elif rel.get("start") and rel.get("end"):
                edges.append(
                    {
                        "id": rel["element_id"],
                        "from": rel["start"],
                        "to": rel["end"],
                        "label": rel["type"],
                    }
                )
        return Response(
            {
                "records": [path],
                "path": path,
                "graph": {
                    "nodes": [node["vis"] for node in path["nodes"]],
                    "edges": edges,
                },
            }
        )


class NeighborhoodQuery(APIView):
    def get(self, request):
        node_id = (request.query_params.get("id") or "").strip()
        if not node_id:
            return Response({"detail": "id is required"}, status=400)
        rows = read_query(
            """
            MATCH (n)
            WHERE n.actor_id = $id OR n.malware_id = $id OR n.indicator_id = $id
               OR n.cve_id = $id OR n.campaign_id = $id OR n.org_id = $id
               OR n.value = $id
            OPTIONAL MATCH (n)-[r]-(m)
            RETURN n, r, m,
                   CASE WHEN r IS NULL THEN NULL ELSE elementId(startNode(r)) END AS start_id,
                   CASE WHEN r IS NULL THEN NULL ELSE elementId(endNode(r)) END AS end_id
            """,
            {"id": node_id},
        )
        nodes = {}
        edges = {}
        for row in rows:
            center = row["n"]
            nodes[center["element_id"]] = center["vis"]
            neighbor = row.get("m")
            if neighbor:
                nodes[neighbor["element_id"]] = neighbor["vis"]
            rel = row.get("r")
            if rel and row.get("start_id") and row.get("end_id"):
                edges[rel["element_id"]] = {
                    "id": rel["element_id"],
                    "from": row["start_id"],
                    "to": row["end_id"],
                    "label": rel["type"],
                }
        return Response({"nodes": list(nodes.values()), "edges": list(edges.values())})
