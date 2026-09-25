from cti_api.db.mongo import threat_actor_profiles
from cti_api.serializers import ThreatActorProfileSerializer
from cti_api.views.mongo_crud import make_mongo_views

ActorProfileListView, ActorProfileDetailView = make_mongo_views(
    threat_actor_profiles,
    ThreatActorProfileSerializer,
    "actor_id",
)
