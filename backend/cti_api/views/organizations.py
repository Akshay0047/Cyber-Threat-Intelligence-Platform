from cti_api.db.mongo import organizations
from cti_api.serializers import OrganizationSerializer
from cti_api.views.mongo_crud import make_mongo_views

OrganizationListView, OrganizationDetailView = make_mongo_views(
    organizations,
    OrganizationSerializer,
    "org_id",
)
