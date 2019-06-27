from celery import Celery
from enhydris import set_django_settings_module

set_django_settings_module()

app = Celery("enhydris_synoptic")

app.config_from_object("django.conf:settings")
app.autodiscover_tasks()
