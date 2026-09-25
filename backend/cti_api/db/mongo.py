from datetime import datetime

from django.conf import settings
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from bson import ObjectId

_client = None


def get_client():
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
    return _client


def get_database():
    client = get_client()
    try:
        return client.get_default_database()
    except ConfigurationError:
        return client["cti"]


def collection(name):
    return get_database()[name]


def incidents():
    return collection("incident_reports")


def malware_profiles():
    return collection("malware_profiles")


def threat_actor_profiles():
    return collection("threat_actor_profiles")


def source_feeds():
    return collection("source_feeds")


def organizations():
    return collection("organizations")


def users():
    return collection("users")


def to_jsonable(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
