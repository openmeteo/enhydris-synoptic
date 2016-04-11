from __future__ import absolute_import

import os
import platform
import sys
import time

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpRequest

from enhydris_synoptic.celery import app
from enhydris_synoptic.models import (SynopticGroup, SynopticGroupStation,
                                      SynopticTimeseries)
from enhydris_synoptic.views import (ChartView, SynopticStationView,
                                     SynopticView)


def write_result_to_file(request, response):
    """Write response content to a static file.

       The resulting output file name is the concatenation of
       ENHYDRIS_SYNOPTIC_OUTPUT_DIR plus request.path plus "index.html",
       unless request.path ends in a file name such as "1.png"; in this case
       "index.html" is not appended.
    """
    # Determine the output file name
    output_relative_path = os.path.normpath(request.path[1:])
    if output_relative_path.endswith('/'):
        output_relative_path += 'index.html'
    output_file = os.path.join(settings.ENHYDRIS_SYNOPTIC_OUTPUT_DIR,
                               output_relative_path)

    # Make sure the directory exists
    dirname = os.path.dirname(output_file)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # Render the response
    if hasattr(response, 'render'):
        response.render()

    # Write result to temporary file
    temporary_file = output_file + '.1'
    with open(temporary_file, 'w') as f:
        f.write(response.content)

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


def create_group_static_file(synoptic_group):
    """Create static html file for the synoptic group page."""
    request = HttpRequest()
    request.method = 'GET'
    request.path = reverse('synoptic_view',
                           kwargs={'slug': synoptic_group.name})
    response = SynopticView.as_view()(request, slug=synoptic_group.name)
    write_result_to_file(request, response)


def create_station_static_file(sgroupstation):
    """Create static html file for the synoptic group station page."""
    request = HttpRequest()
    request.method = 'GET'
    request.path = reverse('synoptic_station_view',
                           kwargs={'pk': sgroupstation.id})
    response = SynopticStationView.as_view()(request, pk=sgroupstation.id)
    write_result_to_file(request, response)


def create_chart(stimeseries):
    """Create static png file for the synoptic char view page."""
    request = HttpRequest()
    request.method = 'GET'
    request.path = reverse('synoptic_chart_view',
                           kwargs={'pk': stimeseries.id})
    response = ChartView.as_view()(request, pk=stimeseries.id)
    write_result_to_file(request, response)


@app.task
def create_static_files():
    """Create static html files for all enhydris-synoptic."""
    for stimeseries in SynopticTimeseries.objects.all():
        create_chart(stimeseries)
    for sgroupstation in SynopticGroupStation.objects.all():
        create_station_static_file(sgroupstation)
    for sgroup in SynopticGroup.objects.all():
        create_group_static_file(sgroup)
