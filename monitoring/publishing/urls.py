from django.conf.urls import include, url

from rest_framework import routers

from monitoring.publishing import views
from django.urls import re_path

router = routers.SimpleRouter()
router.register(r'cloud', views.CloudSiteViewSet)
router.register(r'grid', views.GridSiteViewSet)
router.register(r'gridsync', views.GridSiteSyncViewSet)

# Necessary to retrieve one site only
urlpatterns = [
    re_path(r'^gridsync/(?P<SiteName>[a-zA-Z0-9-]+)/$', views.GridSiteSyncViewSet.as_view({'get': 'retrieve'}), name='gridsync_singlesite'),
]

urlpatterns += router.urls
