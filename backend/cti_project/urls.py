from django.urls import include, path

urlpatterns = [
    path("api/", include("cti_api.urls")),
]
