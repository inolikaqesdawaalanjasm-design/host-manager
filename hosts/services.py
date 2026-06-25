import platform
import subprocess
import time

from django.utils import timezone

from django.db.models import Count

from .models import Host, HostConnectivityLog, HostDailyStatistic


def ping_host_and_log(host, check_type="manual"):
    ping_count_param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", ping_count_param, "1", host.ip_address]
    start_time = time.perf_counter()
    output = ""
    return_code = None

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            check=False,
            text=True,
        )
        return_code = result.returncode
        output = (result.stdout or result.stderr or "")[:2000]
        reachable = result.returncode == 0
    except (subprocess.SubprocessError, OSError) as exc:
        output = str(exc)
        reachable = False

    checked_at = timezone.now()
    duration_ms = int((time.perf_counter() - start_time) * 1000)

    host.last_check_time = checked_at
    host.last_check_result = reachable
    host.save(update_fields=["last_check_time", "last_check_result", "updated_at"])

    log = HostConnectivityLog.objects.create(
        host=host,
        check_time=checked_at,
        reachable=reachable,
        check_type=check_type,
        target_ip=host.ip_address,
        command=" ".join(command),
        duration_ms=duration_ms,
        return_code=return_code,
        output=output,
    )

    return {
        "host_id": host.id,
        "hostname": host.hostname,
        "ip_address": host.ip_address,
        "reachable": reachable,
        "duration_ms": duration_ms,
        "log_id": log.id,
    }


def ping_all_hosts_and_log(check_type="batch"):
    hosts = Host.objects.filter(is_deleted=False).order_by("id")
    results = [ping_host_and_log(host, check_type=check_type) for host in hosts]
    return {
        "total": len(results),
        "reachable": sum(1 for item in results if item["reachable"]),
        "unreachable": sum(1 for item in results if not item["reachable"]),
        "results": results,
    }


def generate_daily_statistics():
    today = timezone.localdate()
    statistics = (
        Host.objects.filter(is_deleted=False)
        .values("computer_room_id", "computer_room__city_id")
        .annotate(host_count=Count("id"))
    )

    rows = []
    for item in statistics:
        statistic, _ = HostDailyStatistic.objects.update_or_create(
            statistic_date=today,
            city_id=item["computer_room__city_id"],
            computer_room_id=item["computer_room_id"],
            defaults={"host_count": item["host_count"]},
        )
        rows.append(
            {
                "id": statistic.id,
                "statistic_date": str(statistic.statistic_date),
                "city_id": statistic.city_id,
                "computer_room_id": statistic.computer_room_id,
                "host_count": statistic.host_count,
            }
        )

    return {"statistic_date": str(today), "total_rows": len(rows), "rows": rows}
