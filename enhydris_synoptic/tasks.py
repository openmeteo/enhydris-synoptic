from __future__ import absolute_import, unicode_literals

import os
import platform
from six import BytesIO, StringIO
import sys
import time

from django import db
from django.conf import settings
from django.template.loader import render_to_string

import matplotlib; matplotlib.use('AGG')  # NOQA
from matplotlib.dates import DateFormatter, DayLocator, HourLocator
import matplotlib.pyplot as plt
import pandas as pd
from pthelma.timeseries import Timeseries

from enhydris_synoptic.celery import app
from enhydris_synoptic import models
from enhydris_synoptic.models import (SynopticGroup, SynopticGroupStation,
                                      SynopticTimeseries)


def write_output_to_file(relative_filename, s, binary=False):
    """Write string (or bytes) to a file.

       The resulting output file name is the concatenation of
       ENHYDRIS_SYNOPTIC_ROOT plus relative_filename.
    """
    # Determine the output file name
    output_file = os.path.join(settings.ENHYDRIS_SYNOPTIC_ROOT,
                               relative_filename)

    # Make sure the directory exists
    dirname = os.path.dirname(output_file)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # Write result to temporary file
    temporary_file = output_file + '.1'
    s = s if binary else s.encode('utf8')
    mode = 'wb' if binary else 'w'
    with open(temporary_file, mode) as f:
        f.write(s)

    # Replace final file, atomically if possible
    if sys.version_info[0] >= '3':
        os.replace(temporary_file, output_file)
    elif platform.system() == 'Windows':
        if os.path.exists(output_file):
            removed = False
            for i in range(0, 100):
                try:
                    os.remove(output_file)
                    removed = True
                    break
                except:
                    time.sleep(0.001)
            if not removed:
                os.remove(output_file)  # This time raise the exception
        os.rename(temporary_file, output_file)
    else:
        os.rename(temporary_file, output_file)


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


def render_synoptic_group(synoptic_group):
    synoptic_group_stations = models.SynopticGroupStation.objects.filter(
        synoptic_group=synoptic_group)[:]
    for synoptic_group_station in synoptic_group_stations:
        add_synoptic_group_station_context(synoptic_group_station)
    output = render_to_string(
        'synopticgroup.html',
        context={'object': synoptic_group,
                 'synoptic_group_stations': synoptic_group_stations,
                 })
    filename = os.path.join(synoptic_group.name, 'index.html')
    write_output_to_file(filename, output)


def render_synoptic_station(sgroupstation):
    add_synoptic_group_station_context(sgroupstation)
    output = render_to_string('synopticgroupstation.html',
                              context={'object': sgroupstation})
    filename = os.path.join('station', str(sgroupstation.id), 'index.html')
    write_output_to_file(filename, output)


def get_color(i):
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


def render_chart(a_synoptic_timeseries):
    # Get all synoptic time series to put in the chart; i.e. the
    # requested one plus the ones that are grouped with it.
    synoptic_timeseries = [a_synoptic_timeseries]
    synoptic_timeseries.extend(models.SynopticTimeseries.objects.filter(
        group_with=a_synoptic_timeseries.id))

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
        ax.plot(xdata, ydata, color=get_color(i),
                label=s.get_subtitle())
        if i == 0:
            # We will later need the data of the first time series, in
            # order to fill the chart
            gydata = ydata

    # Change plot limits as needed
    xmin, xmax, ymin, ymax = ax.axis()
    if a_synoptic_timeseries.default_chart_min:
        ymin = min(a_synoptic_timeseries.default_chart_min, ymin)
    if a_synoptic_timeseries.default_chart_max:
        ymax = max(a_synoptic_timeseries.default_chart_max, ymax)
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

    # Create and save plot
    f = BytesIO()
    fig.savefig(f)
    filename = os.path.join('chart', str(a_synoptic_timeseries.id) + '.png')
    write_output_to_file(filename, f.getvalue(), binary=True)
    f.close()

    # Return the data, for unit testing
    data = [repr(line.get_xydata()).replace('\n', ' ')
            for line in ax.lines]
    return '(' + ', '.join(data) + ')'


@app.task
def create_static_files():
    """Create static html files for all enhydris-synoptic."""
    for stimeseries in SynopticTimeseries.objects.all():
        render_chart(stimeseries)
    for sgroupstation in SynopticGroupStation.objects.all():
        render_synoptic_station(sgroupstation)
    for sgroup in SynopticGroup.objects.all():
        render_synoptic_group(sgroup)
