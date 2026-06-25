from django.contrib import admin
from django.urls import include, path

from hosts.page_views import HostManagerPageView

urlpatterns = [
    path("", HostManagerPageView.as_view(), name="host-manager"),
    path("admin/", admin.site.urls),
    path("api/", include("hosts.urls")),
]
