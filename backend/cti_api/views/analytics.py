from rest_framework.response import Response
from rest_framework.views import APIView

from cti_api.db.mongo import incidents, malware_profiles, source_feeds


class SeverityBreakdownView(APIView):
    def get(self, request):
        pipeline = [
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
            {"$project": {"_id": 0, "severity": "$_id", "count": 1}},
            {"$sort": {"count": -1}},
        ]
        return Response(list(incidents().aggregate(pipeline)))


class TopIndicatorsView(APIView):
    def get(self, request):
        pipeline = [
            {"$unwind": "$related_indicators"},
            {"$group": {"_id": "$related_indicators", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
            {"$project": {"_id": 0, "indicator": "$_id", "count": 1}},
        ]
        return Response(list(incidents().aggregate(pipeline)))


class SourceReliabilityView(APIView):
    def get(self, request):
        pipeline = [
            {
                "$project": {
                    "_id": 0,
                    "feed_id": 1,
                    "name": 1,
                    "type": 1,
                    "reliability_score": 1,
                }
            },
            {"$sort": {"reliability_score": -1}},
        ]
        return Response(list(source_feeds().aggregate(pipeline)))


class MonthlyTrendView(APIView):
    def get(self, request):
        pipeline = [
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m", "date": "$timestamp"}},
                    "count": {"$sum": 1},
                }
            },
            {"$project": {"_id": 0, "month": "$_id", "count": 1}},
            {"$sort": {"month": 1}},
        ]
        return Response(list(incidents().aggregate(pipeline)))


class MalwareFamiliesView(APIView):
    def get(self, request):
        pipeline = [
            {"$group": {"_id": "$family", "count": {"$sum": 1}}},
            {"$project": {"_id": 0, "family": "$_id", "count": 1}},
            {"$sort": {"count": -1}},
        ]
        return Response(list(malware_profiles().aggregate(pipeline)))
