from rest_framework import serializers

from monitoring.publishing.models import CloudSite, GridSite, GridSiteSync


class GridSiteSerializer(serializers.HyperlinkedModelSerializer):
    # Override default format with None so that Python datetime is used as
    # ouput format. Encoding will be determined by the renderer and can be
    # formatted by a template filter.
    updated = serializers.DateTimeField(format=None)

    class Meta:
        model = GridSite
        fields = ('url', 'SiteName', 'updated')


class GridSiteSyncSerializer(serializers.HyperlinkedModelSerializer):
    # Override default format with None so that Python datetime is used as
    # ouput format. Encoding will be determined by the renderer and can be
    # formatted by a template filter.

    class Meta:
        model = GridSiteSync
        fields = ('url', 'SiteName', 'YearMonth', 'RecordStart', 'RecordEnd', 'RecordCountPublished', 'RecordCountInDb', 'SyncStatus')

        # Sitename substitutes pk
        lookup_field = 'SiteName'
        extra_kwargs = {
            'url': {'lookup_field': 'SiteName'}
        }


class CloudSiteSerializer(serializers.HyperlinkedModelSerializer):
    # Override default format with None so that Python datetime is used as
    # ouput format. Encoding will be determined by the renderer and can be
    # formatted by a template filter.
    updated = serializers.DateTimeField(format=None)

    class Meta:
        model = CloudSite
        fields = ('url', 'SiteName', 'Vms', 'Script', 'updated')
