import platform
import subprocess

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import City, ComputerRoom, Employee, Host, Organization
from .serializers import (
    CitySerializer,
    ComputerRoomSerializer,
    EmployeeSerializer,
    HostSerializer,
    OrganizationSerializer,
)


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
        ping_count_param = "-n" if platform.system().lower() == "windows" else "-c"

        try:
            result = subprocess.run(
                ["ping", ping_count_param, "1", host.ip_address],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3,
                check=False,
            )
            reachable = result.returncode == 0
        except (subprocess.SubprocessError, OSError):
            reachable = False

        host.last_check_time = timezone.now()
        host.last_check_result = reachable
        host.save(update_fields=["last_check_time", "last_check_result", "updated_at"])

        return Response({"reachable": reachable})
