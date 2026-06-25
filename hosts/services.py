import platform
import subprocess
import time

from django.utils import timezone

from django.db import transaction
from django.db.models import Count, Q

from .models import City, ComputerRoom, Employee, Host, HostConnectivityLog, HostDailyStatistic, Organization


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
        .annotate(
            host_count=Count("id"),
            reachable_count=Count("id", filter=Q(last_check_result=True)),
            unreachable_count=Count("id", filter=Q(last_check_result=False)),
        )
    )

    rows = []
    for item in statistics:
        statistic, _ = HostDailyStatistic.objects.update_or_create(
            statistic_date=today,
            city_id=item["computer_room__city_id"],
            computer_room_id=item["computer_room_id"],
            defaults={
                "host_count": item["host_count"],
                "reachable_count": item["reachable_count"],
                "unreachable_count": item["unreachable_count"],
            },
        )
        rows.append(
            {
                "id": statistic.id,
                "statistic_date": str(statistic.statistic_date),
                "city_id": statistic.city_id,
                "computer_room_id": statistic.computer_room_id,
                "host_count": statistic.host_count,
                "reachable_count": statistic.reachable_count,
                "unreachable_count": statistic.unreachable_count,
            }
        )

    return {"statistic_date": str(today), "total_rows": len(rows), "rows": rows}


DEMO_MARKER_CODE = "DEMO_SEED"


def has_seed_test_data():
    return Organization.objects.filter(code=DEMO_MARKER_CODE).exists()


def has_any_business_data():
    return any(
        [
            City.objects.filter(is_deleted=False).exists(),
            Organization.objects.filter(is_deleted=False).exists(),
            Employee.objects.filter(is_deleted=False).exists(),
            ComputerRoom.objects.filter(is_deleted=False).exists(),
            Host.objects.filter(is_deleted=False).exists(),
            HostDailyStatistic.objects.filter(is_deleted=False).exists(),
            HostConnectivityLog.objects.filter(is_deleted=False).exists(),
        ]
    )


@transaction.atomic
def create_seed_test_data():
    if has_seed_test_data():
        return {"created": False, "message": "测试数据已经创建过，不能重复创建"}
    if has_any_business_data():
        return {"created": False, "message": "当前系统已有数据，只有数据为空时才可添加测试数据"}

    beijing = City.objects.create(name="演示北京", code="BJ-DEMO", region="华北", remark="测试数据")
    shanghai = City.objects.create(name="演示上海", code="SH-DEMO", region="华东", remark="测试数据")

    marker_org = Organization.objects.create(name="测试数据标记", code=DEMO_MARKER_CODE, remark="用于防止重复创建测试数据")
    ops_org = Organization.objects.create(name="运维部", code="OPS-DEMO", parent=marker_org, remark="测试数据")
    rd_org = Organization.objects.create(name="研发部", code="RD-DEMO", parent=marker_org, remark="测试数据")

    zhangsan = Employee.objects.create(name="张三", job_no="DEMO-E001", phone="13800000001", email="zhangsan@example.com", organization=ops_org)
    lisi = Employee.objects.create(name="李四", job_no="DEMO-E002", phone="13800000002", email="lisi@example.com", organization=rd_org)

    bj_room = ComputerRoom.objects.create(
        name="演示北京一号机房",
        code="BJ-IDC-01-DEMO",
        city=beijing,
        address="北京市海淀区测试路 1 号",
        manager=zhangsan,
        status="enabled",
        remark="测试数据",
    )
    sh_room = ComputerRoom.objects.create(
        name="演示上海一号机房",
        code="SH-IDC-01-DEMO",
        city=shanghai,
        address="上海市浦东新区测试路 1 号",
        manager=lisi,
        status="enabled",
        remark="测试数据",
    )

    Host.objects.create(
        hostname="demo-web-01",
        ip_address="127.0.0.1",
        manage_ip="127.0.0.1",
        computer_room=bj_room,
        organization=ops_org,
        owner=zhangsan,
        host_type="virtual",
        environment="test",
        os_type="Linux",
        cpu_core=2,
        memory_gb=4,
        disk_gb=100,
        status="running",
        remark="测试数据：本机回环地址，通常可 ping 通",
    )
    Host.objects.create(
        hostname="demo-db-01",
        ip_address="192.0.2.10",
        manage_ip="192.0.2.11",
        computer_room=sh_room,
        organization=rd_org,
        owner=lisi,
        host_type="physical",
        environment="prod",
        os_type="Linux",
        cpu_core=8,
        memory_gb=32,
        disk_gb=500,
        status="running",
        remark="测试数据：文档保留网段，通常不可 ping 通",
    )
    Host.objects.create(
        hostname="demo-cache-01",
        ip_address="192.0.2.20",
        manage_ip="192.0.2.21",
        computer_room=bj_room,
        organization=ops_org,
        owner=zhangsan,
        host_type="cloud",
        environment="dev",
        os_type="Ubuntu",
        cpu_core=4,
        memory_gb=8,
        disk_gb=200,
        status="maintenance",
        remark="测试数据",
    )

    statistic_result = generate_daily_statistics()
    return {
        "created": True,
        "message": "测试数据创建成功",
        "counts": {
            "cities": 2,
            "organizations": 3,
            "employees": 2,
            "computer_rooms": 2,
            "hosts": 3,
            "daily_statistics": statistic_result["total_rows"],
        },
    }
