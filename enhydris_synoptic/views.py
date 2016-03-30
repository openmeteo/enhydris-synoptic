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

    def get_color(self, i):
        """Return the color to be used for line with sequence i

        The first line to be drawn uses red, so self.get_color(0)='red';
        the second one uses green, so self.get_color(1)='green'; and there are
        also one or two more colors. We assume the user will not attempt to
        group more than a few time series together. However, if this happens,
        we recycle the colors starting from red again, to make sure we don't
        have an index error or anything.
        """
        colors = ['red', 'green', 'blue', 'magenta']
        return colors[i % len(colors)]

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Get all synoptic time series to put in the chart; i.e. the
        # requested one plus the ones that are grouped with it.
        synoptic_timeseries = [self.object]
        synoptic_timeseries.extend(models.SynopticTimeseries.objects.filter(
            group_with=self.object.id))

        # Read the last 144 records of each time series into a pandas object
        for t in synoptic_timeseries:
            ats = Timeseries(t.timeseries.id)
            ats.read_from_db(db.connection)
            buff = StringIO()
            ats.write(buff)
            buff.seek(0)
            t.pandas_object = pd.read_csv(buff, parse_dates=[0],
                                          usecols=[0, 1], index_col=0,
                                          header=None)[-144:]

        # Reorder them so that the greatest is at the top
        synoptic_timeseries.sort(key=lambda x: float(x.pandas_object.sum()),
                                 reverse=True)

        # Setup plot
        fig = plt.figure()
        fig.set_dpi(100)
        fig.set_size_inches(3.2, 2)
        fig.subplots_adjust(left=0.10, right=0.99, bottom=0.15, top=0.97)
        matplotlib.rcParams.update({'font.size': 7})
        ax = fig.add_subplot(1, 1, 1)

        # Draw lines. We use matplotlib's plot() instead of pandas's wrapper,
        # because otherwise there is trouble modifying the x axis labels
        # (see http://stackoverflow.com/questions/12945971/).
        for i, s in enumerate(synoptic_timeseries):
            xdata = s.pandas_object.index.to_pydatetime()
            ydata = s.pandas_object.values.transpose()[0]
            ax.plot(xdata, ydata, color=self.get_color(i),
                    label=s.get_subtitle())
            if i == 0:
                # We will need later the data of the first time series, in
                # order to fill the chart
                gydata = ydata

        # Change plot limits as needed
        xmin, xmax, ymin, ymax = ax.axis()
        if self.object.default_chart_min:
            ymin = min(self.object.default_chart_min, ymin)
        if self.object.default_chart_max:
            ymax = max(self.object.default_chart_max, ymax)
        ax.set_ylim([ymin, ymax])

        # Fill
        ax.fill_between(xdata, gydata, ymin, color='#ffff00')

        # X ticks and labels
        ax.xaxis.set_minor_locator(HourLocator(byhour=range(0, 24, 3)))
        ax.xaxis.set_minor_formatter(DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(DayLocator())
        ax.xaxis.set_major_formatter(
            DateFormatter('\n    %Y-%m-%d $\\rightarrow$'))

        # Gridlines and legend
        ax.grid(b=True, which='both', color='b', linestyle=':')
        if len(synoptic_timeseries) > 1:
            ax.legend()

        # Create plot
        result = HttpResponse(content_type="image/png")
        fig.savefig(result)

        # If unit testing, also return some data
        if hasattr(settings, 'TEST_MATPLOTLIB') and settings.TEST_MATPLOTLIB:
            data = [repr(line.get_xydata()).replace('\n', ' ')
                    for line in ax.lines]
            result['X-Matplotlib-Data'] = '(' + ', '.join(data) + ')'

        return result
