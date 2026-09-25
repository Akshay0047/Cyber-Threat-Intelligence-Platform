from django.urls import path

from cti_api.views.actor_profiles import ActorProfileDetailView, ActorProfileListView
from cti_api.views.analytics import (
    MalwareFamiliesView,
    MonthlyTrendView,
    SeverityBreakdownView,
    SourceReliabilityView,
    TopIndicatorsView,
)
from cti_api.views.auth_views import LoginView, LogoutView, MeView
from cti_api.views.feeds import FeedDetailView, FeedListView
from cti_api.views.graph_actors import (
    ActorDetailView,
    ActorListView,
    GraphMalwareDetailView,
    GraphMalwareListView,
    InfraDetailView,
    InfraListView,
)
from cti_api.views.graph_queries import (
    ActorCampaignsQuery,
    ActorMalwareQuery,
    MalwareInfraQuery,
    NeighborhoodQuery,
    SharedInfraQuery,
    ShortestPathQuery,
)
from cti_api.views.graph_relationships import RelationshipDetailView, RelationshipListView
from cti_api.views.incidents import IncidentDetailView, IncidentListView
from cti_api.views.malware import MalwareDetailView, MalwareListView
from cti_api.views.organizations import OrganizationDetailView, OrganizationListView
from cti_api.views.search import SearchView

urlpatterns = [
    path("auth/login/", LoginView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("search/", SearchView.as_view()),
    path("incidents/", IncidentListView.as_view()),
    path("incidents/<str:doc_id>/", IncidentDetailView.as_view()),
    path("malware/", MalwareListView.as_view()),
    path("malware/<str:doc_id>/", MalwareDetailView.as_view()),
    path("actor-profiles/", ActorProfileListView.as_view()),
    path("actor-profiles/<str:doc_id>/", ActorProfileDetailView.as_view()),
    path("feeds/", FeedListView.as_view()),
    path("feeds/<str:doc_id>/", FeedDetailView.as_view()),
    path("organizations/", OrganizationListView.as_view()),
    path("organizations/<str:doc_id>/", OrganizationDetailView.as_view()),
    path("analytics/severity-breakdown/", SeverityBreakdownView.as_view()),
    path("analytics/top-indicators/", TopIndicatorsView.as_view()),
    path("analytics/source-reliability/", SourceReliabilityView.as_view()),
    path("analytics/monthly-trend/", MonthlyTrendView.as_view()),
    path("analytics/malware-families/", MalwareFamiliesView.as_view()),
    path("graph/actors/", ActorListView.as_view()),
    path("graph/actors/<str:doc_id>/", ActorDetailView.as_view()),
    path("graph/malware/", GraphMalwareListView.as_view()),
    path("graph/malware/<str:doc_id>/", GraphMalwareDetailView.as_view()),
    path("graph/infra/", InfraListView.as_view()),
    path("graph/infra/<str:doc_id>/", InfraDetailView.as_view()),
    path("graph/relationships/", RelationshipListView.as_view()),
    path("graph/relationships/<str:rel_id>/", RelationshipDetailView.as_view()),
    path("graph/queries/actor-malware/", ActorMalwareQuery.as_view()),
    path("graph/queries/malware-infra/", MalwareInfraQuery.as_view()),
    path("graph/queries/actor-campaigns/", ActorCampaignsQuery.as_view()),
    path("graph/queries/shared-infra/", SharedInfraQuery.as_view()),
    path("graph/queries/shortest-path/", ShortestPathQuery.as_view()),
    path("graph/neighborhood/", NeighborhoodQuery.as_view()),
]
