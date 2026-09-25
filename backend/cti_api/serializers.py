from rest_framework import serializers

SEVERITIES = ["low", "medium", "high", "critical"]
MOTIVATIONS = ["financial", "espionage", "disruption", "hacktivism"]
FEED_TYPES = ["osint", "commercial", "government", "internal"]
SECTORS = [
    "finance",
    "healthcare",
    "energy",
    "government",
    "telecommunications",
    "manufacturing",
    "education",
]
MALWARE_TYPES = ["loader", "ransomware", "backdoor", "stealer", "rat", "trojan"]
INDICATOR_TYPES = ["ip", "domain", "hash"]
RELATIONSHIP_TYPES = [
    "USES",
    "COMMUNICATES_WITH",
    "EXPLOITS",
    "PART_OF",
    "TARGETS",
    "ATTRIBUTED_TO",
]


class IncidentSerializer(serializers.Serializer):
    incident_id = serializers.CharField(max_length=64)
    source = serializers.CharField(max_length=200)
    severity = serializers.ChoiceField(choices=SEVERITIES)
    timestamp = serializers.DateTimeField()
    description = serializers.CharField()
    related_indicators = serializers.ListField(child=serializers.CharField(max_length=512))
    reliability = serializers.FloatField(min_value=0, max_value=1)


class MalwareProfileSerializer(serializers.Serializer):
    malware_id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=200)
    family = serializers.CharField(max_length=120)
    hash = serializers.CharField(max_length=128)
    behavior_summary = serializers.CharField()
    first_seen = serializers.DateTimeField()


class ThreatActorProfileSerializer(serializers.Serializer):
    actor_id = serializers.CharField(max_length=64)
    aliases = serializers.ListField(child=serializers.CharField(max_length=200))
    motivation = serializers.ChoiceField(choices=MOTIVATIONS)
    notes = serializers.CharField(allow_blank=True)
    sources = serializers.ListField(child=serializers.CharField(max_length=200))


class SourceFeedSerializer(serializers.Serializer):
    feed_id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=200)
    type = serializers.ChoiceField(choices=FEED_TYPES)
    reliability_score = serializers.FloatField(min_value=0, max_value=1)


class OrganizationSerializer(serializers.Serializer):
    org_id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=200)
    sector = serializers.ChoiceField(choices=SECTORS)
    country = serializers.CharField(max_length=120)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=80)
    password = serializers.CharField(max_length=200)


class GraphActorSerializer(serializers.Serializer):
    actor_id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=200)
    origin = serializers.CharField(max_length=120)


class GraphMalwareSerializer(serializers.Serializer):
    malware_id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=200)
    type = serializers.ChoiceField(choices=MALWARE_TYPES)


class GraphInfraSerializer(serializers.Serializer):
    indicator_id = serializers.CharField(max_length=64)
    value = serializers.CharField(max_length=512)
    indicator_type = serializers.ChoiceField(choices=INDICATOR_TYPES)


class RelationshipSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=RELATIONSHIP_TYPES)
    from_id = serializers.CharField(max_length=128)
    to_id = serializers.CharField(max_length=128)
