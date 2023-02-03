# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.db.models import Max
import pandas as pd

from rest_framework import viewsets, generics
from rest_framework.renderers import TemplateHTMLRenderer

from monitoring.publishing.models import GridSite, VSuperSummaries, CloudSite, VAnonCloudRecord, GridSiteSync, VSyncRecords, GridSiteSyncSubmitH
from monitoring.publishing.serializers import GridSiteSerializer, CloudSiteSerializer, GridSiteSyncSerializer, GridSiteSyncSubmitHSerializer


class GridSiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GridSite.objects.all()
    serializer_class = GridSiteSerializer
    template_name = 'gridsites.html'

    def list(self, request):
        last_fetched = GridSite.objects.aggregate(Max('fetched'))['fetched__max']
        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))
        if last_fetched is None or (last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20))):
            fetchset = VSuperSummaries.objects.using('grid').raw("SELECT Site, max(LatestEndTime) AS LatestPublish FROM VSuperSummaries WHERE Year=2019 GROUP BY 1;")
            for f in fetchset:
                GridSite.objects.update_or_create(defaults={'updated': f.LatestPublish}, SiteName=f.Site)
        else:
            print('No need to update')

        final_response = []
        response = super(GridSiteViewSet, self).list(request)

        for single_dict in response.data:
            date = single_dict.get('updated').replace(tzinfo=None)

            diff = datetime.today() - date
            if diff <= timedelta(days=7):
                single_dict['returncode'] = 0
                single_dict['stdout'] = "OK [ last published %s days ago: %s ]" % (diff.days, date.strftime("%Y-%m-%d"))
            elif diff > timedelta(days=7):
                single_dict['returncode'] = 1
                single_dict['stdout'] = "WARNING [ last published %s days ago: %s ]" % (diff.days, date.strftime("%Y-%m-%d"))
            else:
                single_dict['returncode'] = 3
                single_dict['stdout'] = "UNKNOWN"
            final_response.append(single_dict)

        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            response.data = {'sites': final_response, 'last_fetched': last_fetched}

        return response

    def retrieve(self, request, pk=None):
        last_fetched = GridSite.objects.aggregate(Max('fetched'))['fetched__max']
        # If there's no data then last_fetched is None.
        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))
        if last_fetched is None or last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20)):
            print('Out of date')
            fetchset = VSuperSummaries.objects.using('grid').raw("SELECT Site, max(LatestEndTime) AS LatestPublish FROM VSuperSummaries WHERE Year=2019 GROUP BY 1;")
            for f in fetchset:
                GridSite.objects.update_or_create(defaults={'updated': f.LatestPublish}, SiteName=f.Site)
        else:
            print('No need to update')

        response = super(GridSiteViewSet, self).retrieve(request)
        date = response.data['updated'].replace(tzinfo=None)

        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            # Single result put in list to work with same HTML template.
            response.data = {'sites': [response.data], 'last_fetched': last_fetched}

        diff = datetime.today() - date
        if diff <= timedelta(days=7):
            response.data['returncode'] = 0
            response.data['stdout'] = "OK [ last published %s days ago: %s ]" % (diff.days, date.strftime("%Y-%m-%d"))
        elif diff > timedelta(days=7):
            response.data['returncode'] = 1
            response.data['stdout'] = "WARNING [ last published %s days ago: %s ]" % (diff.days, date.strftime("%Y-%m-%d"))
        else:
            response.data['returncode'] = 3
            response.data['stdout'] = "UNKNOWN"

        return response


class GridSiteSyncViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GridSiteSync.objects.all()
    serializer_class = GridSiteSyncSerializer
    lookup_field = 'SiteName'

    # When a single site is showed (retrieve function used), the template
    # is different than the one used when showing a list of sites
    def get_template_names(self):
        if self.action == 'list':
            return ['gridsync.html']
        elif self.action == 'retrieve':
            return ['gridsync_singlesite.html']

    # Combine Year and Month into one string (display purposes)
    def get_year_month_string(self, year, month):
        year_string = str(year)
        month_string = str(month)
        if len(month_string) == 1:
            month_string = '0' + month_string
        return year_string + '-' + month_string

    def list(self, request):
        last_fetched = GridSiteSync.objects.aggregate(Max('fetched'))['fetched__max']
        n_sites = GridSiteSync.objects.values('SiteName').distinct().count()

        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))
        if last_fetched is None or last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20)) or n_sites == 1:
            print('Out of date')

            # The condition on EarliestEndTime and LatestEndTime is necessary to avoid error by pytz because of dates like '00-00-00'
            fetchset_Summaries = VSuperSummaries.objects.using('apel').raw("SELECT Site, Month, Year, SUM(NumberOfJobs) AS RecordCountPublished, MIN(EarliestEndTime) AS RecordStart, MAX(LatestEndTime) AS RecordEnd FROM VSuperSummaries WHERE EarliestEndTime>'1900-01-01' AND LatestEndTime>'1900-01-01' GROUP BY Site, Year, Month;")
            fetchset_SyncRecords = VSyncRecords.objects.using('apel').raw("SELECT Site, Month, Year, SUM(NumberOfJobs) AS RecordCountInDb FROM VSyncRecords GROUP BY Site, Year, Month")

            # Create empty dicts that will become dfs to be combined
            Summaries_dict = {"Site": [], "Month": [], "Year": [], "RecordCountPublished": [], "RecordStart": [], "RecordEnd": []}
            SyncRecords_dict = {"Site": [], "Month": [], "Year": [], "RecordCountInDb": []}

            # Fill the dicts with the fetched data
            for row in fetchset_Summaries:
                Summaries_dict["Site"] = Summaries_dict.get("Site") + [row.Site]
                Summaries_dict["Month"] = Summaries_dict.get("Month") + [row.Month]
                Summaries_dict["Year"] = Summaries_dict.get("Year") + [row.Year]
                Summaries_dict["RecordCountPublished"] = Summaries_dict.get("RecordCountPublished") + [row.RecordCountPublished]
                Summaries_dict["RecordStart"] = Summaries_dict.get("RecordStart") + [row.RecordStart]
                Summaries_dict["RecordEnd"] = Summaries_dict.get("RecordEnd") + [row.RecordEnd]

            for row in fetchset_SyncRecords:
                SyncRecords_dict["Site"] = SyncRecords_dict.get("Site") + [row.Site]
                SyncRecords_dict["Month"] = SyncRecords_dict.get("Month") + [row.Month]
                SyncRecords_dict["Year"] = SyncRecords_dict.get("Year") + [row.Year]
                SyncRecords_dict["RecordCountInDb"] = SyncRecords_dict.get("RecordCountInDb") + [row.RecordCountInDb]

            # Merge data from VSuperSummaries and VSyncRecords into one df
            df_Summaries = pd.DataFrame.from_dict(Summaries_dict)
            df_SyncRecords = pd.DataFrame.from_dict(SyncRecords_dict)
            df_all = df_Summaries.merge(df_SyncRecords, left_on=['Site', 'Month', 'Year'], right_on=['Site', 'Month', 'Year'], how='inner')
            fetchset = df_all.to_dict('index')

            # Delete all data if table not empty (as this function lists all sites)
            GridSiteSync.objects.all().delete()

            # Determine SyncStatus based on the difference between records published and in db
            for f in fetchset.values():
                rel_diff1 = abs(f.get("RecordCountPublished") - f.get("RecordCountInDb"))/(f.get("RecordCountInDb"))
                rel_diff2 = abs(f.get("RecordCountPublished") - f.get("RecordCountInDb"))/(f.get("RecordCountPublished"))
                if rel_diff1 < 0.01 or rel_diff2 < 0.01:
                    f['SyncStatus'] = 'OK'
                else:
                    f['SyncStatus'] = 'Error'

                # Combined primary keys outside the default dict
                GridSiteSync.objects.update_or_create(
                    defaults={
                            'RecordStart': f.get("RecordStart"),
                            'RecordEnd': f.get("RecordEnd"),
                            'RecordCountPublished': f.get("RecordCountPublished"),
                            'RecordCountInDb': f.get("RecordCountInDb"),
                            'SyncStatus': f.get("SyncStatus"),
                            },
                    YearMonth=self.get_year_month_string(f.get("Year"), f.get("Month")),
                    SiteName=f.get("Site"),
                    Month=f.get("Month"),
                    Year=f.get("Year"),
                )

        else:
            print('No need to update')

        response = super(GridSiteSyncViewSet, self).list(request)
        response.data = {'records': response.data, 'last_fetched': last_fetched}
        return response

    def retrieve(self, request, SiteName=None):
        lookup_field = 'SiteName'
        last_fetched = GridSiteSync.objects.aggregate(Max('fetched'))['fetched__max']
        row_1 = GridSiteSync.objects.filter()[:1].get()
        n_sites = GridSiteSync.objects.values('SiteName').distinct().count()

        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))
        if last_fetched is None or last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20)) or n_sites > 1 or SiteName != row_1.SiteName:
            print('Out of date')

            # The condition on EarliestEndTime and LatestEndTime is necessary to avoid error by pytz because of dates like '00-00-00'
            fetchset_Summaries = VSuperSummaries.objects.using('apel').raw("SELECT Site, Month, Year, SUM(NumberOfJobs) AS RecordCountPublished, MIN(EarliestEndTime) AS RecordStart, MAX(LatestEndTime) AS RecordEnd FROM VSuperSummaries WHERE Site='{}' AND EarliestEndTime>'1900-01-01' AND LatestEndTime>'1900-01-01'GROUP BY Site, Month, Year;".format(SiteName))
            fetchset_SyncRecords = VSyncRecords.objects.using('apel').raw("SELECT Site, Month, Year, SUM(NumberOfJobs) AS RecordCountInDb FROM VSyncRecords WHERE Site='{}' GROUP BY Site, Month, Year;".format(SiteName))

            Summaries_dict = {"Site": [], "Month": [], "Year": [], "RecordCountPublished": [], "RecordStart": [], "RecordEnd": []}
            SyncRecords_dict = {"Site": [], "Month": [], "Year": [], "RecordCountInDb": []}

            for row in fetchset_Summaries:
                Summaries_dict["Site"] = Summaries_dict.get("Site") + [row.Site]
                Summaries_dict["Month"] = Summaries_dict.get("Month") + [row.Month]
                Summaries_dict["Year"] = Summaries_dict.get("Year") + [row.Year]
                Summaries_dict["RecordCountPublished"] = Summaries_dict.get("RecordCountPublished") + [row.RecordCountPublished]
                Summaries_dict["RecordStart"] = Summaries_dict.get("RecordStart") + [row.RecordStart]
                Summaries_dict["RecordEnd"] = Summaries_dict.get("RecordEnd") + [row.RecordEnd]

            for row in fetchset_SyncRecords:
                SyncRecords_dict["Site"] = SyncRecords_dict.get("Site") + [row.Site]
                SyncRecords_dict["Month"] = SyncRecords_dict.get("Month") + [row.Month]
                SyncRecords_dict["Year"] = SyncRecords_dict.get("Year") + [row.Year]
                SyncRecords_dict["RecordCountInDb"] = SyncRecords_dict.get("RecordCountInDb") + [row.RecordCountInDb]

            df_Summaries = pd.DataFrame.from_dict(Summaries_dict)
            df_SyncRecords = pd.DataFrame.from_dict(SyncRecords_dict)
            df_all = df_Summaries.merge(df_SyncRecords, left_on=['Site', 'Month', 'Year'], right_on=['Site', 'Month', 'Year'], how='inner')
            fetchset = df_all.to_dict('index')

            # Ensure we list only the data for one site
            first_row = GridSiteSync.objects.first()
            if first_row is not None:
                if first_row.SiteName != SiteName:
                    GridSiteSync.objects.all().delete()

            for f in fetchset.values():
                rel_diff1 = abs(f.get("RecordCountPublished") - f.get("RecordCountInDb"))/(f.get("RecordCountInDb"))
                rel_diff2 = abs(f.get("RecordCountPublished") - f.get("RecordCountInDb"))/(f.get("RecordCountPublished"))
                if rel_diff1 <= 0.01 or rel_diff2 <= 0.01:
                    f['SyncStatus'] = 'OK'
                else:
                    f['SyncStatus'] = 'Error'

                GridSiteSync.objects.update_or_create(
                    defaults={
                            'RecordStart': f.get("RecordStart"),
                            'RecordEnd': f.get("RecordEnd"),
                            'RecordCountPublished': f.get("RecordCountPublished"),
                            'RecordCountInDb': f.get("RecordCountInDb"),
                            'SyncStatus': f.get("SyncStatus"),
                            },
                    YearMonth=self.get_year_month_string(f.get("Year"), f.get("Month")),
                    SiteName=f.get("Site"),
                    Month=f.get("Month"),
                    Year=f.get("Year"),
                )

        else:
            print('No need to update')

        response = super(GridSiteSyncViewSet, self).list(request)
        response.data = {'records': response.data, 'last_fetched': last_fetched}
        return response


# Needed for passing two parameters to a viewset (GridSiteSyncSubmitHViewSet)
class MultipleFieldLookupMixin:
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
    """
    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs.get(field):
                filter[field] = self.kwargs[field]
        obj = get_object_or_404(queryset, **filter)
        self.check_object_permissions(self.request, obj)
        return obj


class GridSiteSyncSubmitHViewSet(MultipleFieldLookupMixin, viewsets.ReadOnlyModelViewSet):
    queryset = GridSiteSyncSubmitH.objects.all()
    serializer_class = GridSiteSyncSubmitHSerializer
    template_name = 'gridsync_submithost.html'

    def list(self, request):
        response = super(GridSiteSyncSubmitHViewSet, self).list(request)
        response.data = {'submisthosts': response.data, 'last_fetched': last_fetched}
        return response

    def retrieve(self, request, SiteName=None, YearMonth=None):

        lookup_fields = ('SiteName', 'YearMonth')
        last_fetched = GridSiteSyncSubmitH.objects.aggregate(Max('fetched'))['fetched__max']
        Year, Month = YearMonth.replace('-', ' ').split(' ')
        sitename_in_table = None
        yearmonth_in_table = None

        # This is to ensure the data is updated when changing (or clicking on another) month
        if GridSiteSyncSubmitH.objects.count() > 0:
            row_1 = GridSiteSyncSubmitH.objects.filter()[:1].get()
            sitename_in_table = row_1.SiteName
            yearmonth_in_table = row_1.YearMonth

        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))
        if last_fetched is None or last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20)) or (sitename_in_table != SiteName) or (yearmonth_in_table != YearMonth):
            print('Out of date')

            fetchset_Summaries = VSuperSummaries.objects.using('apel').raw("SELECT Site, Month, Year, SUM(NumberOfJobs) AS RecordCountPublished, SubmitHost AS SubmitHostSumm, MIN(EarliestEndTime) AS RecordStart, MAX(LatestEndTime) AS RecordEnd FROM VSuperSummaries WHERE Site='{}' AND Month='{}' AND Year='{}' GROUP BY SubmitHost;".format(SiteName, Month, Year))
            fetchset_SyncRecords = VSyncRecords.objects.using('apel').raw("SELECT Site, Month, Year, SUM(NumberOfJobs) AS RecordCountInDb, SubmitHost AS SubmitHostSync FROM VSyncRecords WHERE Site='{}' AND Month='{}' AND Year='{}' GROUP BY SubmitHost;".format(SiteName, Month, Year))

            Summaries_dict = {"Site": [], "Month": [], "Year": [], "SubmitHostSumm": [], "RecordCountPublished": [], "RecordStart": [], "RecordEnd": []}
            SyncRecords_dict = {"Site": [], "Month": [], "Year": [], "SubmitHostSync": [], "RecordCountInDb": []}

            for row in fetchset_Summaries:
                Summaries_dict["Site"] = Summaries_dict.get("Site") + [row.Site]
                Summaries_dict["Month"] = Summaries_dict.get("Month") + [row.Month]
                Summaries_dict["Year"] = Summaries_dict.get("Year") + [row.Year]
                Summaries_dict["SubmitHostSumm"] = Summaries_dict.get("SubmitHostSumm") + [row.SubmitHostSumm]
                Summaries_dict["RecordCountPublished"] = Summaries_dict.get("RecordCountPublished") + [row.RecordCountPublished]
                Summaries_dict["RecordStart"] = Summaries_dict.get("RecordStart") + [row.RecordStart]
                Summaries_dict["RecordEnd"] = Summaries_dict.get("RecordEnd") + [row.RecordEnd]

            for row in fetchset_SyncRecords:
                SyncRecords_dict["Site"] = SyncRecords_dict.get("Site") + [row.Site]
                SyncRecords_dict["Month"] = SyncRecords_dict.get("Month") + [row.Month]
                SyncRecords_dict["Year"] = SyncRecords_dict.get("Year") + [row.Year]
                SyncRecords_dict["SubmitHostSync"] = SyncRecords_dict.get("SubmitHostSync") + [row.SubmitHostSync]
                SyncRecords_dict["RecordCountInDb"] = SyncRecords_dict.get("RecordCountInDb") + [row.RecordCountInDb]

            df_Summaries = pd.DataFrame.from_dict(Summaries_dict)
            df_SyncRecords = pd.DataFrame.from_dict(SyncRecords_dict)
            df_Summaries.dropna(inplace=True)
            df_SyncRecords.dropna(inplace=True)

            df_all = df_Summaries.merge(df_SyncRecords, left_on=['Site', 'Month', 'Year', 'SubmitHostSumm'], right_on=['Site', 'Month', 'Year', 'SubmitHostSync'], how='outer')
            fetchset = df_all.to_dict('index')

            # This is to list only data for one month
            GridSiteSyncSubmitH.objects.all().delete()

            def get_year_month_string(year, month):
                year_string = str(year)
                month_string = str(month)
                if len(month_string) == 1:
                    month_string = '0' + month_string
                return year_string + '-' + month_string

            for f in fetchset.values():
                GridSiteSyncSubmitH.objects.update_or_create(
                    defaults={
                            'RecordStart': f.get("RecordStart"),
                            'RecordEnd': f.get("RecordEnd"),
                            'RecordCountPublished': f.get("RecordCountPublished"),
                            'RecordCountInDb': f.get("RecordCountInDb"),
                            },
                    SiteName=f.get("Site"),
                    YearMonth=get_year_month_string(f.get("Year"), f.get("Month")),
                    Month=f.get("Month"),
                    Year=f.get("Year"),
                    SubmitHost=f.get("SubmitHostSumm"),
                )

        else:
            print('No need to update')

        response = super(GridSiteSyncSubmitHViewSet, self).list(request)
        response.data = {'submisthosts': response.data, 'last_fetched': last_fetched}
        return response


class CloudSiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CloudSite.objects.all()
    serializer_class = CloudSiteSerializer
    template_name = 'cloudsites.html'

    def list(self, request):
        last_fetched = CloudSite.objects.aggregate(Max('fetched'))['fetched__max']
        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))
        if last_fetched is None or (last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20))):
            print('Out of date')
            fetchset =  VAnonCloudRecord.objects.using('cloud').raw("SELECT b.SiteName, COUNT(DISTINCT VMUUID) as VMs, CloudType, b.UpdateTime FROM (SELECT SiteName, MAX(UpdateTime) AS latest FROM VAnonCloudRecords WHERE UpdateTime>'2018-07-25' GROUP BY SiteName) AS a INNER JOIN VAnonCloudRecords AS b ON b.SiteName = a.SiteName AND b.UpdateTime = a.latest GROUP BY SiteName")
            for f in fetchset:
                CloudSite.objects.update_or_create(defaults={'Vms': f.VMs, 'Script': f.CloudType, 'updated': f.UpdateTime}, SiteName=f.SiteName)
        else:
            print('No need to update')

        response = super(CloudSiteViewSet, self).list(request)
        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            response.data = {'sites': response.data, 'last_fetched': last_fetched}
        return response

    def retrieve(self, request, pk=None):
        last_fetched = CloudSite.objects.aggregate(Max('fetched'))['fetched__max']
        print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))
        if last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20)):
            print('Out of date')
            fetchset =  VAnonCloudRecord.objects.using('cloud').raw("SELECT b.SiteName, COUNT(DISTINCT VMUUID) as VMs, CloudType, b.UpdateTime FROM (SELECT SiteName, MAX(UpdateTime) AS latest FROM VAnonCloudRecords WHERE UpdateTime>'2018-07-25' GROUP BY SiteName) AS a INNER JOIN VAnonCloudRecords AS b ON b.SiteName = a.SiteName AND b.UpdateTime = a.latest GROUP BY SiteName")
            for f in fetchset:
                CloudSite.objects.update_or_create(defaults={'Vms': f.VMs, 'Script': f.CloudType, 'updated': f.UpdateTime}, SiteName=f.SiteName)
        else:
            print('No need to update')

        response = super(CloudSiteViewSet, self).retrieve(request)
        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            # Single result put in list to work with same HTML template.
            response.data = {'sites': [response.data], 'last_fetched': last_fetched}

        response.data['returncode'] = 3
        response.data['stdout'] = "UNKNOWN"

        return response
