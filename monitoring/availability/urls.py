from django.conf.urls import url
import sys
from monitoring.availability import views

sys.path.append('/usr/share/DJANGO_MONITORING_APP')

urlpatterns = [
    url(r'^$', views.status),
]
