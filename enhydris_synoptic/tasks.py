from datetime import timedelta
from io import BytesIO
import os

from django.conf import settings
from django.template.loader import render_to_string

import matplotlib; matplotlib.use('AGG')  # NOQA
from matplotlib.dates import DateFormatter, DayLocator, HourLocator
import matplotlib.pyplot as plt

from enhydris_synoptic.celery import app
from enhydris_synoptic import models
from enhydris_synoptic.models import SynopticGroup, SynopticGroupStation


def write_output_to_file(relative_filename, s):
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
    mode = 'wb' if isinstance(s, bytes) else 'w'
    with open(temporary_file, mode) as f:
        f.write(s)

    # Replace final file atomically
    os.replace(temporary_file, output_file)


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


def get_timeseries_for_synoptic_group_station(sgroupstation):
    """Return list with synoptic timeseries.

    For each synoptic timeseries in the given synoptic group station,
    grab the last 24 hours preceding the last common date, attach these
    records to the synoptic timeseries object, and attach these time series
    to the sgroupstation object as the synoptic_timeseries attribute.
    """
    synoptic_timeseries = list(models.SynopticTimeseries.objects.filter(
        synoptic_group_station=sgroupstation))
    sgroupstation.last_common_date = get_last_common_date(synoptic_timeseries)
    start_date = sgroupstation.last_common_date - timedelta(minutes=1339)
    for asynts in synoptic_timeseries:
        asynts.data = asynts.timeseries.get_data(
            start_date=start_date, end_date=sgroupstation.last_common_date)
    sgroupstation.synoptic_timeseries = synoptic_timeseries


def add_synoptic_group_station_context(synoptic_group_station):
    for asynts in synoptic_group_station.synoptic_timeseries:
        synoptic_group_station.error = False
        try:
            asynts.value = asynts.data.loc[
                synoptic_group_station.last_common_date.replace(tzinfo=None)][
                    'value']
        except KeyError:
            synoptic_group_station.error = True
            continue


def render_synoptic_group(synoptic_group, all_sgroupstations):
    subset = [x
              for x in all_sgroupstations
              if x.synoptic_group.id == synoptic_group.id]
    output = render_to_string(
        'synopticgroup.html',
        context={'object': synoptic_group,
                 'synoptic_group_stations': subset,
                 })
    filename = os.path.join(synoptic_group.slug, 'index.html')
    write_output_to_file(filename, output)


def render_synoptic_station(sgroupstation):
    output = render_to_string('synopticgroupstation.html',
                              context={'object': sgroupstation})
    filename = os.path.join(sgroupstation.synoptic_group.slug,
                            'station', str(sgroupstation.id), 'index.html')
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


def render_chart(a_synoptic_timeseries, all_synoptic_timeseries):
    # Get all synoptic time series to put in the chart; i.e. the
    # requested one plus the ones that are grouped with it.
    synoptic_timeseries = [
        x for x in all_synoptic_timeseries
        if (x.id == a_synoptic_timeseries.id)
        or (x.group_with and (x.group_with.id == a_synoptic_timeseries.id))]

    # Reorder them so that the greatest is at the top
    synoptic_timeseries.sort(key=lambda x: float(x.data.value.sum()),
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
        xdata = s.data.index.to_pydatetime()
        ydata = s.data['value']
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
    plt.close(fig)  # Release some memory
    filename = os.path.join('chart', str(a_synoptic_timeseries.id) + '.png')
    write_output_to_file(filename, f.getvalue())
    f.close()

    # If unit testing, write the data to a file.
    if hasattr(settings, 'TEST_MATPLOTLIB') and settings.TEST_MATPLOTLIB:
        filename = os.path.join('chart',
                                str(a_synoptic_timeseries.id) + '.dat')
        data = [repr(line.get_xydata()).replace('\n', ' ')
                for line in ax.lines]
        write_output_to_file(filename, '(' + ', '.join(data) + ')')


@app.task
def create_static_files():
    """Create static html files for all enhydris-synoptic."""
    # Create a list of all synoptic group stations
    all_sgroupstations = []
    for sgroupstation in SynopticGroupStation.objects.all():
        get_timeseries_for_synoptic_group_station(sgroupstation)
        add_synoptic_group_station_context(sgroupstation)
        all_sgroupstations.append(sgroupstation)

    # For each station, create its reports and its charts
    for sgroupstation in all_sgroupstations:
        render_synoptic_station(sgroupstation)
        for t in sgroupstation.synoptic_timeseries:
            render_chart(t, sgroupstation.synoptic_timeseries)

    # Finally create the reports for each synoptic group
    for sgroup in SynopticGroup.objects.all():
        render_synoptic_group(sgroup, all_sgroupstations)
