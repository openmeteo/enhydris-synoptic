from six import StringIO

from django import db
from django.conf import settings
from django.http import HttpResponse
from django.views.generic.base import View
from django.views.generic.detail import DetailView, SingleObjectMixin

import matplotlib; matplotlib.use('AGG')  # NOQA
from matplotlib.dates import DateFormatter, DayLocator, HourLocator
import matplotlib.pyplot as plt
import pandas as pd
from pthelma.timeseries import Timeseries

from enhydris_synoptic import models


def get_last_common_date(synoptic_timeseries):
    # We don't actually return the last common date, which would be
    # difficult; instead, we return the minimum of the last dates of the
    # timeseries, which will usually be the last common date. station is
    # an enhydris_synoptic.models.Station object.
    result = None
    for asynts in synoptic_timeseries:
        end_date = asynts.timeseries.end_date
        if end_date and ((not result) or (end_date < result)):
            result = end_date
    return result


def add_synoptic_group_station_context(synoptic_group_station):
    synoptic_timeseries = models.SynopticTimeseries.objects.filter(
        synoptic_group_station=synoptic_group_station)[:]
    synoptic_group_station.last_common_date = get_last_common_date(
        synoptic_timeseries)
    synoptic_group_station.synoptic_timeseries = []
    for asynts in synoptic_timeseries:
        synoptic_group_station.error = False
        tsrecords = Timeseries(asynts.timeseries.id)
        tsrecords.read_from_db(db.connection)
        try:
            asynts.value = tsrecords[synoptic_group_station.last_common_date]
        except KeyError:
            synoptic_group_station.error = True
            continue
        synoptic_group_station.synoptic_timeseries.append(asynts)


class SynopticView(DetailView):
    model = models.SynopticGroup
    slug_field = 'name'
    template_name = 'synopticgroup.html'

    def get_context_data(self, **kwargs):
        context = super(SynopticView, self).get_context_data(**kwargs)
        synoptic_group_stations = models.SynopticGroupStation.objects.filter(
            synoptic_group=self.object)[:]
        for synoptic_group_station in synoptic_group_stations:
            add_synoptic_group_station_context(synoptic_group_station)
        context['synoptic_group_stations'] = synoptic_group_stations
        return context


class SynopticStationView(DetailView):
    model = models.SynopticGroupStation
    template_name = 'synopticgroupstation.html'

    def get_context_data(self, **kwargs):
        context = super(SynopticStationView, self).get_context_data(**kwargs)
        add_synoptic_group_station_context(self.object)
        return context


class ChartView(SingleObjectMixin, View):
    model = models.SynopticTimeseries

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Read the last 144 records of the time series into a pandas object
        ts = Timeseries(self.object.timeseries.id)
        ts.read_from_db(db.connection)
        buff = StringIO()
        ts.write(buff)
        buff.seek(0)
        tsdata = pd.read_csv(buff, parse_dates=[0], usecols=[0, 1],
                             index_col=0, header=None)[-144:]

        # Setup plot
        fig = plt.figure()
        fig.set_dpi(100)
        fig.set_size_inches(3.2, 2)
        fig.subplots_adjust(left=0.10, right=0.99, bottom=0.15, top=0.97)
        matplotlib.rcParams.update({'font.size': 7})
        ax = fig.add_subplot(1, 1, 1)

        # Draw line. We use matplotlib's plot() instead of pandas's wrapper,
        # because otherwise there is trouble modifying the x axis labels
        # (see http://stackoverflow.com/questions/12945971/).
        xdata = tsdata.index.to_pydatetime()
        ydata = tsdata.values.transpose()[0]
        ax.plot(xdata, ydata, color='r')

        # Change plot limits as needed
        xmin, xmax, ymin, ymax = ax.axis()
        if self.object.default_chart_min:
            ymin = min(self.object.default_chart_min, ymin)
        if self.object.default_chart_max:
            ymax = max(self.object.default_chart_max, ymax)
        ax.set_ylim([ymin, ymax])

        # Fill
        ax.fill_between(xdata, ydata, ymin, color='#ffff00')

        # X ticks and labels
        ax.xaxis.set_minor_locator(HourLocator(byhour=range(0, 24, 3)))
        ax.xaxis.set_minor_formatter(DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(DayLocator())
        ax.xaxis.set_major_formatter(
            DateFormatter('\n    %Y-%m-%d $\\rightarrow$'))

        # Gridlines
        ax.grid(b=True, which='both', color='b', linestyle=':')

        # Create plot
        result = HttpResponse(content_type="image/png")
        fig.savefig(result)

        # If unit testing, also return some data
        if hasattr(settings, 'TEST_MATPLOTLIB') and settings.TEST_MATPLOTLIB:
            result['X-Matplotlib-Data'] = repr(
                ax.lines[0].get_xydata()).replace('\n', ' ')

        return result
