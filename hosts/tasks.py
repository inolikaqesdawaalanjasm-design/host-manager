from celery import shared_task

from .services import generate_daily_statistics, ping_all_hosts_and_log


@shared_task
def generate_daily_host_statistics():
    result = generate_daily_statistics()
    return f"主机每日统计任务执行完成，日期：{result['statistic_date']}，记录数：{result['total_rows']}"


@shared_task
def check_all_hosts_connectivity():
    result = ping_all_hosts_and_log(check_type="scheduled")
    return f"主机连通性定时探测完成，总数：{result['total']}，可达：{result['reachable']}，不可达：{result['unreachable']}"
