from django.contrib import admin

from .models import City, ComputerRoom, Employee, Host, HostConnectivityLog, HostDailyStatistic, Organization


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "region", "is_deleted", "created_at")
    search_fields = ("name", "code")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "parent", "is_deleted", "created_at")
    search_fields = ("name", "code")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "job_no", "organization", "phone", "email", "is_deleted")
    search_fields = ("name", "job_no", "phone", "email")
    list_select_related = ("organization",)


@admin.register(ComputerRoom)
class ComputerRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "city", "manager", "status", "is_deleted")
    search_fields = ("name", "code")
    list_select_related = ("city", "manager")


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "hostname",
        "ip_address",
        "computer_room",
        "organization",
        "owner",
        "status",
        "last_check_result",
        "is_deleted",
    )
    search_fields = ("hostname", "ip_address", "manage_ip")
    list_select_related = ("computer_room", "organization", "owner")


@admin.register(HostDailyStatistic)
class HostDailyStatisticAdmin(admin.ModelAdmin):
    list_display = ("id", "statistic_date", "city", "computer_room", "host_count")
    list_filter = ("statistic_date", "city", "computer_room")
    list_select_related = ("city", "computer_room")


@admin.register(HostConnectivityLog)
class HostConnectivityLogAdmin(admin.ModelAdmin):
    list_display = ("id", "host", "target_ip", "reachable", "check_type", "duration_ms", "check_time")
    list_filter = ("reachable", "check_type", "check_time")
    search_fields = ("host__hostname", "target_ip", "command", "output")
    list_select_related = ("host",)
