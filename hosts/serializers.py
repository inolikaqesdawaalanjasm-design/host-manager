from rest_framework import serializers

from .models import City, ComputerRoom, Employee, Host, HostConnectivityLog, HostDailyStatistic, Organization


class BaseSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_deleted",
        )


class CitySerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = City


class OrganizationSerializer(BaseSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)

    class Meta(BaseSerializer.Meta):
        model = Organization


class EmployeeSerializer(BaseSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta(BaseSerializer.Meta):
        model = Employee


class ComputerRoomSerializer(BaseSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    manager_name = serializers.CharField(source="manager.name", read_only=True)

    class Meta(BaseSerializer.Meta):
        model = ComputerRoom


class HostSerializer(BaseSerializer):
    computer_room_name = serializers.CharField(source="computer_room.name", read_only=True)
    city_name = serializers.CharField(source="computer_room.city.name", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    owner_name = serializers.CharField(source="owner.name", read_only=True)

    class Meta(BaseSerializer.Meta):
        model = Host


class HostConnectivityLogSerializer(serializers.ModelSerializer):
    hostname = serializers.CharField(source="host.hostname", read_only=True)
    ip_address = serializers.CharField(source="host.ip_address", read_only=True)
    computer_room_name = serializers.CharField(source="host.computer_room.name", read_only=True)
    city_name = serializers.CharField(source="host.computer_room.city.name", read_only=True)

    class Meta:
        model = HostConnectivityLog
        fields = "__all__"


class HostDailyStatisticSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    computer_room_name = serializers.CharField(source="computer_room.name", read_only=True)

    class Meta:
        model = HostDailyStatistic
        fields = "__all__"
