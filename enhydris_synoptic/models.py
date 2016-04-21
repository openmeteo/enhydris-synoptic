from __future__ import unicode_literals

import six

from django.db import IntegrityError, models
from django.utils.translation import ugettext as _

from enhydris.hcore.models import Station, Timeseries


@six.python_2_unicode_compatible
class SynopticGroup(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True,
                            help_text='Identifier to be used in URL')
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

    def check_timeseries_integrity(self, *args, **kwargs):
        """
        This method checks whether the timeseries.through.order field starts
        with 1 and is contiguous, and that groupped time series are in order.
        I wrote it thinking I could use it somewhere, but I don't think it's
        possible (see http://stackoverflow.com/questions/33500336/). However,
        since I wrote it, I keep it, although I'm not using it anywhere. Mind
        you, it's unit-tested.
        """
        # Check that time series are in order
        expected_order = 0
        for syn_ts in self.synoptictimeseries_set.order_by('order'):
            expected_order += 1
            if syn_ts.order != expected_order:
                raise IntegrityError(_(
                    "The order of the time series must start from 1 and be "
                    "continuous."))

        # Check that grouped time series are in order
        current_group_leader = None
        previous_synoptictimeseries = None
        for syn_ts in self.synoptictimeseries_set.order_by('order'):
            if not syn_ts.group_with:
                current_group_leader = None
                continue
            current_group_leader = current_group_leader or \
                previous_synoptictimeseries
            if syn_ts.group_with.id != current_group_leader.id:
                raise IntegrityError(_(
                    "Groupped time series must be ordered together."))
            previous_synoptictimeseries = syn_ts

        super(SynopticGroupStation, self).save(*args, **kwargs)


class SynopticTimeseriesManager(models.Manager):

    def primary(self):
        """Return only time series that don't have group_with."""
        return self.filter(group_with__isnull=True)


class SynopticTimeseries(models.Model):
    synoptic_group_station = models.ForeignKey(SynopticGroupStation)
    timeseries = models.ForeignKey(Timeseries)
    order = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=50, blank=True, help_text=_(
        "Used as the chart title and as the time series title in the report. "
        "Leave empty to use the time series name."))
    group_with = models.ForeignKey('self', blank=True, null=True, help_text=_(
        "Specify this field if you want to group this time series with "
        "another in the same chart and in the report."))
    subtitle = models.CharField(max_length=50, blank=True, help_text=_(
        "If time series are grouped, this is shows in the legend of the chart "
        "and in the report, in brackets."))
    default_chart_min = models.FloatField(blank=True, null=True, help_text=_(
        "Minimum value of the y axis of the chart. If the variable goes "
        "lower, the chart will automatically expand. If empty, the chart will "
        "always expand just enough to accomodate the value."))
    default_chart_max = models.FloatField(blank=True, null=True, help_text=_(
        "Maximum value of the y axis of the chart. If the variable goes "
        "lower, the chart will automatically expand. If empty, the chart will "
        "always expand just enough to accomodate the value."))

    objects = SynopticTimeseriesManager()

    class Meta:
        unique_together = (('synoptic_group_station', 'timeseries'),
                           ('synoptic_group_station', 'order'),
                           )
        ordering = ['synoptic_group_station', 'order']
        verbose_name_plural = 'Synoptic timeseries'

    def __str__(self):
        return str(self.synoptic_group_station) + ' - ' + self.get_full_name()

    def get_title(self):
        return self.title or self.timeseries.name

    def get_subtitle(self):
        return self.subtitle or self.timeseries.name

    def get_full_name(self):
        result = self.get_title()
        if self.subtitle:
            result += ' (' + self.subtitle + ')'
        return result
