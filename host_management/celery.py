import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "host_management.settings")

app = Celery("host_management")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
