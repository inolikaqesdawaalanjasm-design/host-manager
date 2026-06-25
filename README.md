# 主机管理系统

Django + Django REST Framework + Celery 主机管理系统。

## 功能

- 城市、组织、员工、机房、主机 CRUD 接口
- 逻辑删除，查询默认过滤 `is_deleted=False`
- 删除前占用检查
- 主机 ping 探测接口：`POST /api/hosts/{id}/ping/`
- 每天 00:00 按城市和机房统计主机数量
- 请求耗时中间件，响应头返回 `X-Request-Cost-Time`

## 运行

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Celery

默认使用本机 Redis：

```bash
celery -A host_management worker -l info
celery -A host_management beat -l info
```

定时任务配置在 `host_management/settings.py`：

```python
CELERY_BEAT_SCHEDULE = {
    "generate-daily-host-statistics": {
        "task": "hosts.tasks.generate_daily_host_statistics",
        "schedule": crontab(hour=0, minute=0),
    },
}
```

## 接口

- `GET|POST /api/cities/`
- `GET|PUT|PATCH|DELETE /api/cities/{id}/`
- `GET|POST /api/organizations/`
- `GET|PUT|PATCH|DELETE /api/organizations/{id}/`
- `GET|POST /api/employees/`
- `GET|PUT|PATCH|DELETE /api/employees/{id}/`
- `GET|POST /api/computer-rooms/`
- `GET|PUT|PATCH|DELETE /api/computer-rooms/{id}/`
- `GET|POST /api/hosts/`
- `GET|PUT|PATCH|DELETE /api/hosts/{id}/`
- `POST /api/hosts/{id}/ping/`
