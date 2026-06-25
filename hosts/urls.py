from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CityViewSet, ComputerRoomViewSet, EmployeeViewSet, HostViewSet, OrganizationViewSet

router = DefaultRouter()
router.register(r"cities", CityViewSet, basename="city")
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"employees", EmployeeViewSet, basename="employee")
router.register(r"computer-rooms", ComputerRoomViewSet, basename="computer-room")
router.register(r"hosts", HostViewSet, basename="host")

urlpatterns = [
    path("", include(router.urls)),
]
