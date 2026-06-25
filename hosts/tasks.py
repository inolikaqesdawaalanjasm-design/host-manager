from celery import shared_task
from django.db.models import Count
from django.utils import timezone

from .models import Host, HostDailyStatistic


@shared_task
def generate_daily_host_statistics():
    today = timezone.localdate()
    statistics = (
        Host.objects.filter(is_deleted=False)
        .values("computer_room_id", "computer_room__city_id")
        .annotate(host_count=Count("id"))
    )

    for item in statistics:
        HostDailyStatistic.objects.update_or_create(
            statistic_date=today,
            city_id=item["computer_room__city_id"],
            computer_room_id=item["computer_room_id"],
            defaults={"host_count": item["host_count"]},
        )

    return "主机每日统计任务执行完成"
