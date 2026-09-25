from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from rest_framework.response import Response
from rest_framework.views import APIView

from cti_api.db.mongo import to_jsonable


def make_mongo_views(collection_getter, serializer_class, id_field, list_sort=None):
    class ListView(APIView):
        def get(self, request):
            cursor = collection_getter().find()
            if list_sort:
                cursor = cursor.sort(list_sort)
            else:
                cursor = cursor.sort(id_field, 1)
            return Response([to_jsonable(doc) for doc in cursor])

        def post(self, request):
            serializer = serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            document = dict(serializer.validated_data)
            if collection_getter().find_one({id_field: document[id_field]}):
                return Response({id_field: ["Already exists"]}, status=409)
            try:
                collection_getter().insert_one(document)
            except DuplicateKeyError:
                return Response({id_field: ["Already exists"]}, status=409)
            return Response(to_jsonable(document), status=201)

    class DetailView(APIView):
        def get(self, request, doc_id):
            document = collection_getter().find_one({id_field: doc_id})
            if not document:
                return Response({"detail": "Not found"}, status=404)
            return Response(to_jsonable(document))

        def put(self, request, doc_id):
            if not collection_getter().find_one({id_field: doc_id}):
                return Response({"detail": "Not found"}, status=404)
            payload = request.data.copy()
            if id_field in payload and payload[id_field] != doc_id:
                return Response({"detail": f"{id_field} cannot be changed"}, status=400)
            payload[id_field] = doc_id
            serializer = serializer_class(data=payload)
            serializer.is_valid(raise_exception=True)
            updates = dict(serializer.validated_data)
            updates.pop(id_field, None)
            document = collection_getter().find_one_and_update(
                {id_field: doc_id},
                {"$set": updates},
                return_document=ReturnDocument.AFTER,
            )
            return Response(to_jsonable(document))

        def delete(self, request, doc_id):
            result = collection_getter().delete_one({id_field: doc_id})
            if result.deleted_count == 0:
                return Response({"detail": "Not found"}, status=404)
            return Response(status=204)

    return ListView, DetailView
