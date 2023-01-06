from django.conf.urls import url

import sys
sys.path.append('/usr/share/DJANGO_MONITORING_APP')
from monitoring.availability import views

urlpatterns = [
    url(r'^$', views.status),
]
