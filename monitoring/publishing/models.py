# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class GridSite(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    SiteName = models.CharField(max_length=255, primary_key=True)
    updated = models.DateTimeField()


class VSuperSummaries(models.Model):
    Site = models.CharField(max_length=255, primary_key=True)
    LatestPublish = models.DateTimeField()
    Month = models.IntegerField()
    Year = models.IntegerField()
    RecordStart = models.DateTimeField()                                                           
    RecordEnd = models.DateTimeField()    
    RecordCountPublished = models.IntegerField()                                                  
                                                               
    class Meta:
        managed = False
        db_table = 'VSuperSummaries'


class GridSiteSync(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    SiteName = models.CharField(max_length=255)
    YearMonth = models.CharField(max_length=255)
    Year = models.IntegerField()
    Month = models.IntegerField()
    RecordStart = models.DateTimeField()                                                           
    RecordEnd = models.DateTimeField()  
    RecordCountPublished = models.IntegerField()
    RecordCountInDb = models.IntegerField()
    SyncStatus = models.CharField(max_length=255)

    class Meta:
        # Descending order of Year and Month to display latest data first
        ordering = ('SiteName', '-Year', '-Month')
        unique_together = ('SiteName', 'YearMonth')
        

class VSyncRecords(models.Model):
    Site = models.CharField(max_length=255, primary_key=True)
    RecordCountInDb = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'VSyncRecords'


class CloudSite(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    SiteName = models.CharField(max_length=255, primary_key=True)
    Vms = models.IntegerField(default=0)
    Script = models.CharField(max_length=255)
    updated = models.DateTimeField()

    class Meta:
        ordering = ('SiteName',)


class VAnonCloudRecord(models.Model):
    SiteName = models.CharField(max_length=255, primary_key=True)
    VMs = models.IntegerField()
    CloudType = models.CharField(max_length=255)
    UpdateTime = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'vanoncloudrecords'

    def __str__(self):
        return '%s running "%s" updated at %s with %s records' % (
                                                    self.SiteName,
                                                    self.CloudType,
                                                    self.UpdateTime,
                                                    self.VMs)
   
                                                    
class GridSiteSyncSubmitH(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    SiteName = models.CharField(max_length=255)
    YearMonth = models.CharField(max_length=255)
    Year = models.IntegerField()
    Month = models.IntegerField()
    RecordStart = models.DateTimeField()                                                           
    RecordEnd = models.DateTimeField()  
    RecordCountPublished = models.IntegerField()
    RecordCountInDb = models.IntegerField()
    SubmitHost = models.CharField(max_length=255)

    class Meta:
        ordering = ('SiteName',  '-Year', '-Month')
        unique_together = ('SiteName', 'YearMonth', 'SubmitHost')