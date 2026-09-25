import re

from rest_framework.response import Response
from rest_framework.views import APIView

from cti_api.db.neo4j import node_to_dict, read_query, write_transaction

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def make_graph_views(label, id_field, serializer_class, mutable_fields):
    if not _IDENT.match(label) or not _IDENT.match(id_field):
        raise ValueError("Unsafe label or id field")

    class ListView(APIView):
        def get(self, request):
            rows = read_query(
                f"MATCH (n:{label}) RETURN n ORDER BY n.{id_field}"
            )
            return Response([row["n"] for row in rows])

        def post(self, request):
            serializer = serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = dict(serializer.validated_data)

            def work(tx):
                existing = list(
                    tx.run(
                        f"MATCH (n:{label} {{{id_field}: $id}}) RETURN n",
                        id=data[id_field],
                    )
                )
                if existing:
                    return "duplicate"
                assignments = ", ".join(f"{field}: ${field}" for field in data)
                created = list(
                    tx.run(
                        f"CREATE (n:{label} {{{assignments}}}) RETURN n",
                        **data,
                    )
                )
                return node_to_dict(created[0]["n"])

            result = write_transaction(work)
            if result == "duplicate":
                return Response({id_field: ["Already exists"]}, status=409)
            return Response(result, status=201)

    class DetailView(APIView):
        def get(self, request, doc_id):
            rows = read_query(
                f"MATCH (n:{label} {{{id_field}: $id}}) RETURN n",
                {"id": doc_id},
            )
            if not rows:
                return Response({"detail": "Not found"}, status=404)
            return Response(rows[0]["n"])

        def put(self, request, doc_id):
            payload = request.data.copy()
            if id_field in payload and payload[id_field] != doc_id:
                return Response({"detail": f"{id_field} cannot be changed"}, status=400)
            payload[id_field] = doc_id
            serializer = serializer_class(data=payload)
            serializer.is_valid(raise_exception=True)
            data = dict(serializer.validated_data)
            sets = ", ".join(f"n.{field} = ${field}" for field in mutable_fields)

            def work(tx):
                rows = list(
                    tx.run(
                        f"""
                        MATCH (n:{label} {{{id_field}: $id}})
                        SET {sets}
                        RETURN n
                        """,
                        id=doc_id,
                        **{field: data[field] for field in mutable_fields},
                    )
                )
                if not rows:
                    return None
                return node_to_dict(rows[0]["n"])

            node = write_transaction(work)
            if not node:
                return Response({"detail": "Not found"}, status=404)
            return Response(node)

        def delete(self, request, doc_id):
            def work(tx):
                rows = list(
                    tx.run(
                        f"""
                        MATCH (n:{label} {{{id_field}: $id}})
                        WITH n, elementId(n) AS eid
                        DETACH DELETE n
                        RETURN eid
                        """,
                        id=doc_id,
                    )
                )
                return rows

            rows = write_transaction(work)
            if not rows:
                return Response({"detail": "Not found"}, status=404)
            return Response(status=204)

    return ListView, DetailView
