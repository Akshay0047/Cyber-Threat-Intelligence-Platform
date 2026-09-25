from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    from neo4j.exceptions import AuthError, ServiceUnavailable
    from pymongo.errors import PyMongoError

    if isinstance(exc, (ServiceUnavailable, AuthError)):
        return Response(
            {"detail": "Neo4j is unavailable. Check NEO4J_URI and credentials."},
            status=503,
        )
    if isinstance(exc, PyMongoError):
        return Response(
            {"detail": "MongoDB is unavailable. Check MONGO_URI."},
            status=503,
        )
    return exception_handler(exc, context)
