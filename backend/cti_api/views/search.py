import re

from rest_framework.response import Response
from rest_framework.views import APIView

from cti_api.db.mongo import incidents, to_jsonable
from cti_api.db.neo4j import read_query


class SearchView(APIView):
    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        if not query:
            return Response({"detail": "Query parameter q is required"}, status=400)
        if len(query) > 200:
            return Response({"detail": "Query is too long"}, status=400)

        pattern = re.escape(query)
        incident_docs = incidents().find(
            {"related_indicators": {"$regex": pattern, "$options": "i"}}
        )
        infrastructure = read_query(
            """
            MATCH (i:Infrastructure)
            WHERE toLower(i.value) CONTAINS toLower($q) OR i.indicator_id = $q
            RETURN i
            ORDER BY i.indicator_id
            """,
            {"q": query},
        )
        return Response(
            {
                "query": query,
                "incidents": [to_jsonable(doc) for doc in incident_docs],
                "infrastructure": [row["i"] for row in infrastructure],
            }
        )
