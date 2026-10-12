from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    from neo4j.exceptions import AuthError, ServiceUnavailable
    from pymongo.errors import PyMongoError

    if isinstance(exc, (ServiceUnavailable, AuthError)):
        return Response(
            {"detail": "The relationship graph is unavailable. Start it and try again."},
            status=503,
        )
    if isinstance(exc, PyMongoError):
        return Response(
            {"detail": "Stored records are unavailable. Start the document store and try again."},
            status=503,
        )
    return exception_handler(exc, context)
