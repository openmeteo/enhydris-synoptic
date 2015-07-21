from django.db import models

from enhydris.hcore.models import (Station as EnhydrisStation,
                                   Timeseries as EnhydrisTimeseries)


class View(models.Model):
    name = models.SlugField(unique=True)
    stations = models.ManyToManyField(EnhydrisStation, through='Station')


class Station(models.Model):
    synoptic_view = models.ForeignKey(SynopticView)
    station = models.ForeignKey(EnhydrisStation)
    order = models.PositiveSmallIntegerField()
    timeseries = models.ManyToManyField(EnhydrisTimeseries,
                                        through='Timeseries')

    class Meta:
        unique_together = (('synoptic_view', 'order'),)


class Timeseries(models.Model):
    station = models.ForeignKey(Station)
    timeseries = models.ForeignKey(EnhydrisTimeseries)
    order = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = (('station', 'timeseries'),
                           ('station', 'order'),
                           )
