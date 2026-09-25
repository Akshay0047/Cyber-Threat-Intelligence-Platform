from cti_api.db.mongo import incidents
from cti_api.serializers import IncidentSerializer
from cti_api.views.mongo_crud import make_mongo_views

IncidentListView, IncidentDetailView = make_mongo_views(
    incidents,
    IncidentSerializer,
    "incident_id",
    list_sort=[("severity", 1), ("timestamp", -1)],
)
