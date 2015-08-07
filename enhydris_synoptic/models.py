import six

from django.db import models

from enhydris.hcore.models import Station, Timeseries


@six.python_2_unicode_compatible
class SynopticGroup(models.Model):
    name = models.SlugField(unique=True)
    stations = models.ManyToManyField(Station, through='SynopticGroupStation')

    def __str__(self):
        return self.name


@six.python_2_unicode_compatible
class SynopticGroupStation(models.Model):
    synoptic_group = models.ForeignKey(SynopticGroup)
    station = models.ForeignKey(Station)
    order = models.PositiveSmallIntegerField()
    timeseries = models.ManyToManyField(Timeseries,
                                        through='SynopticTimeseries')

    class Meta:
        unique_together = (('synoptic_group', 'order'),)
        ordering = ['synoptic_group', 'order']

    def __str__(self):
        return str(self.station)


class SynopticTimeseries(models.Model):
    synoptic_group_station = models.ForeignKey(SynopticGroupStation)
    timeseries = models.ForeignKey(Timeseries)
    order = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = (('synoptic_group_station', 'timeseries'),
                           ('synoptic_group_station', 'order'),
                           )
        ordering = ['synoptic_group_station', 'order']
        verbose_name_plural = 'Synoptic timeseries'
