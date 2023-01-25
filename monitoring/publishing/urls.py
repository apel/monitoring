from django.conf.urls import include, url

from rest_framework import routers

from monitoring.publishing import views
from django.urls import re_path

router = routers.SimpleRouter()
router.register(r'cloud', views.CloudSiteViewSet)
router.register(r'grid', views.GridSiteViewSet)
router.register(r'gridsync', views.GridSiteSyncViewSet)
router.register(r'gridsync', views.GridSiteSyncSubmitHViewSet)

urlpatterns = [
    re_path(r'^gridsync/(?P<SiteName>[a-zA-Z0-9-]+)/$', views.GridSiteSyncViewSet.as_view({'get': 'retrieve'}), name='gridsync_singlesite'),
    re_path(r'^gridsync/(?P<SiteName>[a-zA-Z0-9-]+)/(?P<YearMonth>[0-9-]+)/$', views.GridSiteSyncSubmitHViewSet.as_view({'get': 'retrieve'}), name='gridsync_submithost'),
]

urlpatterns += router.urls
