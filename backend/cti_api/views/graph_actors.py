from cti_api.serializers import (
    GraphActorSerializer,
    GraphInfraSerializer,
    GraphMalwareSerializer,
)
from cti_api.views.graph_nodes import make_graph_views

ActorListView, ActorDetailView = make_graph_views(
    "ThreatActor",
    "actor_id",
    GraphActorSerializer,
    ["name", "origin"],
)
GraphMalwareListView, GraphMalwareDetailView = make_graph_views(
    "Malware",
    "malware_id",
    GraphMalwareSerializer,
    ["name", "type"],
)
InfraListView, InfraDetailView = make_graph_views(
    "Infrastructure",
    "indicator_id",
    GraphInfraSerializer,
    ["value", "indicator_type"],
)
