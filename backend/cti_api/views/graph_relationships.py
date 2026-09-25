from rest_framework.response import Response
from rest_framework.views import APIView

from cti_api.db.neo4j import node_to_dict, read_query, rel_to_dict, write_transaction
from cti_api.serializers import RelationshipSerializer

# Direction is fixed by relationship type. PART_OF accepts Malware or Infrastructure.
REL_ENDPOINTS = {
    "USES": ("ThreatActor", "actor_id", "Malware", "malware_id"),
    "COMMUNICATES_WITH": ("Malware", "malware_id", "Infrastructure", "indicator_id"),
    "EXPLOITS": ("Malware", "malware_id", "Vulnerability", "cve_id"),
    "TARGETS": ("Campaign", "campaign_id", "Organization", "org_id"),
    "ATTRIBUTED_TO": ("Campaign", "campaign_id", "ThreatActor", "actor_id"),
}


class MissingEndpoint(Exception):
    pass


class DuplicateRelationship(Exception):
    pass


def _create_one(tx, item):
    rel_type = item["type"]
    from_id = item["from_id"]
    to_id = item["to_id"]
    if rel_type == "PART_OF":
        existing = list(
            tx.run(
                """
                MATCH (c:Campaign {campaign_id: $to_id})
                OPTIONAL MATCH (m:Malware {malware_id: $from_id})
                OPTIONAL MATCH (i:Infrastructure {indicator_id: $from_id})
                WITH c, coalesce(m, i) AS src
                WHERE src IS NOT NULL
                MATCH (src)-[r:PART_OF]->(c)
                RETURN r
                """,
                from_id=from_id,
                to_id=to_id,
            )
        )
        if existing:
            raise DuplicateRelationship(f"PART_OF {from_id} -> {to_id} already exists")
        created = list(
            tx.run(
                """
                MATCH (c:Campaign {campaign_id: $to_id})
                OPTIONAL MATCH (m:Malware {malware_id: $from_id})
                OPTIONAL MATCH (i:Infrastructure {indicator_id: $from_id})
                WITH c, coalesce(m, i) AS src
                WHERE src IS NOT NULL
                CREATE (src)-[r:PART_OF]->(c)
                RETURN r, src AS a, c AS b
                """,
                from_id=from_id,
                to_id=to_id,
            )
        )
    else:
        from_label, from_key, to_label, to_key = REL_ENDPOINTS[rel_type]
        existing = list(
            tx.run(
                f"""
                MATCH (a:{from_label} {{{from_key}: $from_id}})
                      -[r:{rel_type}]->
                      (b:{to_label} {{{to_key}: $to_id}})
                RETURN r
                """,
                from_id=from_id,
                to_id=to_id,
            )
        )
        if existing:
            raise DuplicateRelationship(f"{rel_type} {from_id} -> {to_id} already exists")
        created = list(
            tx.run(
                f"""
                MATCH (a:{from_label} {{{from_key}: $from_id}})
                MATCH (b:{to_label} {{{to_key}: $to_id}})
                CREATE (a)-[r:{rel_type}]->(b)
                RETURN r, a, b
                """,
                from_id=from_id,
                to_id=to_id,
            )
        )
    if not created:
        raise MissingEndpoint(f"Could not link {rel_type} from {from_id} to {to_id}")
    record = created[0]
    payload = rel_to_dict(record["r"])
    payload["from_node"] = node_to_dict(record["a"])
    payload["to_node"] = node_to_dict(record["b"])
    payload["vis"] = {
        "id": record["r"].element_id,
        "from": record["a"].element_id,
        "to": record["b"].element_id,
        "label": rel_type,
    }
    return payload


class RelationshipListView(APIView):
    def get(self, request):
        rows = read_query(
            """
            MATCH (a)-[r]->(b)
            WHERE ($from = "" OR a.actor_id = $from OR a.malware_id = $from
                   OR a.indicator_id = $from OR a.cve_id = $from
                   OR a.campaign_id = $from OR a.org_id = $from)
              AND ($to = "" OR b.actor_id = $to OR b.malware_id = $to
                   OR b.indicator_id = $to OR b.cve_id = $to
                   OR b.campaign_id = $to OR b.org_id = $to)
            RETURN r, a, b
            ORDER BY type(r)
            """,
            {
                "from": request.query_params.get("from", ""),
                "to": request.query_params.get("to", ""),
            },
        )
        results = []
        for row in rows:
            payload = row["r"]
            payload["from_node"] = row["a"]
            payload["to_node"] = row["b"]
            if row["a"].get("element_id") and row["b"].get("element_id"):
                payload["vis"] = {
                    "id": payload["element_id"],
                    "from": row["a"]["element_id"],
                    "to": row["b"]["element_id"],
                    "label": payload["type"],
                }
            results.append(payload)
        return Response(results)

    def post(self, request):
        body = request.data
        if isinstance(body, dict) and "relationships" in body:
            items = body["relationships"]
        elif isinstance(body, list):
            items = body
        else:
            items = [body]
        if not items:
            return Response({"detail": "No relationships provided"}, status=400)

        serializer = RelationshipSerializer(data=items, many=True)
        serializer.is_valid(raise_exception=True)

        def work(tx):
            # One write transaction for every edge in the request, including
            # a campaign linked to both an organization and a threat actor.
            return [_create_one(tx, item) for item in serializer.validated_data]

        try:
            created = write_transaction(work)
        except DuplicateRelationship as exc:
            return Response({"detail": str(exc)}, status=409)
        except MissingEndpoint as exc:
            return Response({"detail": str(exc)}, status=404)
        status_code = 201
        if len(created) == 1 and "relationships" not in body and not isinstance(body, list):
            return Response(created[0], status=status_code)
        return Response(created, status=status_code)

    def delete(self, request):
        rel_id = request.query_params.get("id", "")
        if not rel_id:
            return Response({"detail": "Query parameter id is required"}, status=400)
        return _delete_relationship(rel_id)


class RelationshipDetailView(APIView):
    def delete(self, request, rel_id):
        return _delete_relationship(rel_id)


def _delete_relationship(rel_id):
    def work(tx):
        return list(
            tx.run(
                """
                MATCH ()-[r]->()
                WHERE elementId(r) = $rel_id
                WITH r, elementId(r) AS id, type(r) AS rel_type
                DELETE r
                RETURN id, rel_type
                """,
                rel_id=rel_id,
            )
        )

    rows = write_transaction(work)
    if not rows:
        return Response({"detail": "Not found"}, status=404)
    return Response(status=204)
