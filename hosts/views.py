from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import City, ComputerRoom, Employee, Host, HostConnectivityLog, HostDailyStatistic, Organization
from .serializers import (
    CitySerializer,
    ComputerRoomSerializer,
    EmployeeSerializer,
    HostConnectivityLogSerializer,
    HostDailyStatisticSerializer,
    HostSerializer,
    OrganizationSerializer,
)
from .services import create_seed_test_data, generate_daily_statistics, has_seed_test_data, ping_all_hosts_and_log, ping_host_and_log


class BaseModelViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return self.queryset.filter(is_deleted=False)

    def get_current_user(self):
        user = self.request.user
        if user and user.is_authenticated:
            return user
        return None

    def perform_create(self, serializer):
        user = self.get_current_user()
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.get_current_user())

    def check_can_delete(self, obj):
        return None

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        error_message = self.check_can_delete(obj)
        if error_message:
            return Response({"message": error_message}, status=status.HTTP_400_BAD_REQUEST)

        obj.is_deleted = True
        obj.updated_by = self.get_current_user()
        obj.save(update_fields=["is_deleted", "updated_by", "updated_at"])
        return Response({"message": "删除成功"}, status=status.HTTP_200_OK)


class CityViewSet(BaseModelViewSet):
    queryset = City.objects.all().order_by("-id")
    serializer_class = CitySerializer

    def check_can_delete(self, obj):
        if obj.computer_rooms.filter(is_deleted=False).exists():
            return "该城市下存在机房，不能删除"
        return None


class OrganizationViewSet(BaseModelViewSet):
    queryset = Organization.objects.all().order_by("-id")
    serializer_class = OrganizationSerializer

    def check_can_delete(self, obj):
        if obj.children.filter(is_deleted=False).exists():
            return "该组织下存在子组织，不能删除"
        if obj.employees.filter(is_deleted=False).exists():
            return "该组织下存在员工，不能删除"
        if obj.hosts.filter(is_deleted=False).exists():
            return "该组织下存在主机，不能删除"
        return None


class EmployeeViewSet(BaseModelViewSet):
    queryset = Employee.objects.select_related("organization").all().order_by("-id")
    serializer_class = EmployeeSerializer

    def check_can_delete(self, obj):
        if obj.managed_rooms.filter(is_deleted=False).exists():
            return "该员工正在作为机房负责人，不能删除"
        if obj.owned_hosts.filter(is_deleted=False).exists():
            return "该员工正在作为主机负责人，不能删除"
        return None


class ComputerRoomViewSet(BaseModelViewSet):
    queryset = ComputerRoom.objects.select_related("city", "manager").all().order_by("-id")
    serializer_class = ComputerRoomSerializer

    def check_can_delete(self, obj):
        if obj.hosts.filter(is_deleted=False).exists():
            return "该机房下存在主机，不能删除"
        return None


class HostViewSet(BaseModelViewSet):
    queryset = Host.objects.select_related(
        "computer_room",
        "computer_room__city",
        "organization",
        "owner",
    ).all().order_by("-id")
    serializer_class = HostSerializer

    @action(methods=["post"], detail=True, url_path="ping")
    def ping_host(self, request, pk=None):
        host = self.get_object()
        result = ping_host_and_log(host, check_type="manual")
        return Response(result)

    @action(methods=["post"], detail=False, url_path="ping-all")
    def ping_all_hosts(self, request):
        result = ping_all_hosts_and_log(check_type="batch")
        return Response(result)


class HostConnectivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HostConnectivityLogSerializer

    def get_queryset(self):
        queryset = HostConnectivityLog.objects.select_related(
            "host",
            "host__computer_room",
            "host__computer_room__city",
        ).filter(is_deleted=False)
        host_id = self.request.query_params.get("host")
        reachable = self.request.query_params.get("reachable")

        if host_id:
            queryset = queryset.filter(host_id=host_id)
        if reachable in ("true", "false"):
            queryset = queryset.filter(reachable=reachable == "true")
        return queryset.order_by("-check_time", "-id")

    @action(methods=["post"], detail=False, url_path="run-scheduled-check")
    def run_scheduled_check(self, request):
        result = ping_all_hosts_and_log(check_type="scheduled")
        return Response(result)


class HostDailyStatisticViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HostDailyStatisticSerializer

    def get_queryset(self):
        queryset = HostDailyStatistic.objects.select_related("city", "computer_room").filter(is_deleted=False)
        statistic_date = self.request.query_params.get("statistic_date")
        city_id = self.request.query_params.get("city")
        computer_room_id = self.request.query_params.get("computer_room")

        if statistic_date:
            queryset = queryset.filter(statistic_date=statistic_date)
        if city_id:
            queryset = queryset.filter(city_id=city_id)
        if computer_room_id:
            queryset = queryset.filter(computer_room_id=computer_room_id)
        return queryset.order_by("-statistic_date", "city_id", "computer_room_id")

    @action(methods=["post"], detail=False, url_path="generate")
    def generate(self, request):
        result = generate_daily_statistics()
        return Response(result)


@api_view(["GET", "POST"])
def seed_test_data(request):
    if request.method == "GET":
        return Response({"seeded": has_seed_test_data()})
    return Response(create_seed_test_data())
