import datetime as dt
import os
import shutil
import tempfile
import textwrap
from io import StringIO

from django.conf import settings
from django.http import HttpResponse
from django.test import TestCase, override_settings

import numpy as np
from model_mommy import mommy

from enhydris.models import Station, Timeseries
from enhydris_synoptic.models import (
    SynopticGroup,
    SynopticGroupStation,
    SynopticTimeseries,
)
from enhydris_synoptic.tasks import create_static_files


class RandomEnhydrisTimeseriesDataDir(override_settings):
    """
    Override ENHYDRIS_TIMESERIES_DATA_DIR to a temporary directory.

    Specifying "@RandomEnhydrisTimeseriesDataDir()" as a decorator is the same
    as "@override_settings(ENHYDRIS_TIMESERIES_DATA_DIR=tempfile.mkdtemp())",
    except that in the end it removes the temporary directory.
    """

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp()
        super(RandomEnhydrisTimeseriesDataDir, self).__init__(
            ENHYDRIS_TIMESERIES_DATA_DIR=self.tmpdir
        )

    def disable(self):
        super(RandomEnhydrisTimeseriesDataDir, self).disable()
        shutil.rmtree(self.tmpdir)


class RandomSynopticRoot(override_settings):
    """
    Override ENHYDRIS_SYNOPTIC_ROOT to a temporary directory.

    Specifying "@RandomSynopticRoot()" as a decorator is the same as
    "@override_settings(ENHYDRIS_SYNOPTIC_ROOT=tempfile.mkdtemp())", except
    that in the end it removes the temporary directory.
    """

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp()
        super(RandomSynopticRoot, self).__init__(ENHYDRIS_SYNOPTIC_ROOT=self.tmpdir)

    def disable(self):
        super(RandomSynopticRoot, self).disable()
        shutil.rmtree(self.tmpdir)


def days_since_epoch(y, mo, d, h, mi):
    adelta = dt.datetime(y, mo, d, h, mi) - dt.datetime(1, 1, 1)
    return adelta.days + 1 + adelta.seconds / 86400.0


@RandomEnhydrisTimeseriesDataDir()
class SynopticTestCase(TestCase):
    def assertHtmlContains(self, filename, text):
        """Check if a file contains an HTML extract.

        This is pretty much the same as self.assertContains() with html=True,
        but uses a filename instead of a response.
        """
        # We implement it by converting to an HTTPResponse, because there is
        # no better way to use self.assertContains() to do the actual job.
        with open(filename) as f:
            response = HttpResponse(f.read())
        self.assertContains(response, text, html=True)

    def setUp(self):
        # Station
        self.station_komboti = mommy.make(Station, name="Komboti")
        self.station_agios = mommy.make(Station, name="Agios Athanasios")

        # Synoptic group
        self.sg1 = mommy.make(SynopticGroup, slug="mygroup")

        # SynopticGroupStation
        self.sgs1 = mommy.make(
            SynopticGroupStation,
            synoptic_group=self.sg1,
            station=self.station_komboti,
            order=1,
        )
        self.sgs2 = mommy.make(
            SynopticGroupStation,
            synoptic_group=self.sg1,
            station=self.station_agios,
            order=2,
        )

        # Timeseries
        self.ts_komboti_rain = mommy.make(
            Timeseries,
            gentity=self.station_komboti,
            name="Rain",
            unit_of_measurement__symbol="mm",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )
        self.ts_komboti_temperature = mommy.make(
            Timeseries,
            gentity=self.station_komboti,
            name="Air temperature",
            unit_of_measurement__symbol="°C",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )
        self.ts_komboti_wind_speed = mommy.make(
            Timeseries,
            gentity=self.station_komboti,
            name="Wind speed",
            precision=1,
            unit_of_measurement__symbol="m/s",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )
        self.ts_komboti_wind_gust = mommy.make(
            Timeseries,
            gentity=self.station_komboti,
            name="Wind gust",
            precision=1,
            unit_of_measurement__symbol="m/s",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )
        self.ts_agios_rain = mommy.make(
            Timeseries,
            gentity=self.station_agios,
            name="Rain",
            precision=1,
            unit_of_measurement__symbol="mm",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )
        self.ts_agios_temperature = mommy.make(
            Timeseries,
            gentity=self.station_agios,
            name="Air temperature",
            precision=1,
            unit_of_measurement__symbol="°C",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )

        # SynopticTimeseries
        self.sts1_1 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs1,
            timeseries=self.ts_komboti_rain,
            order=1,
        )
        self.sts1_2 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs1,
            timeseries=self.ts_komboti_temperature,
            order=2,
        )
        self.sts1_3 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs1,
            timeseries=self.ts_komboti_wind_speed,
            title="Wind",
            subtitle="speed",
            order=3,
        )
        self.sts1_4 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs1,
            timeseries=self.ts_komboti_wind_gust,
            title="Wind",
            subtitle="gust",
            group_with=self.sts1_3,
            order=4,
        )
        self.sts2_1 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs2,
            timeseries=self.ts_agios_rain,
            order=1,
        )
        self.sts2_2 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs2,
            timeseries=self.ts_agios_temperature,
            order=2,
        )

        # Komboti rain timeseries data
        self.ts_komboti_rain.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2015-10-22 15:00,0,
            2015-10-22 15:10,0,
            2015-10-22 15:20,0,
            """
                )
            )
        )

        # Komboti temperature timeseries data
        self.ts_komboti_temperature.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2015-10-22 15:00,15,
            2015-10-22 15:10,16,
            2015-10-22 15:20,17,
            """
                )
            )
        )

        # Komboti wind speed data
        self.ts_komboti_wind_speed.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2015-10-22 15:00,2.9,
            2015-10-22 15:10,3.2,
            2015-10-22 15:20,3,
            """
                )
            )
        )

        # Komboti wind gust data
        self.ts_komboti_wind_gust.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2015-10-22 15:00,3.7,
            2015-10-22 15:10,4.5,
            2015-10-22 15:20,4.1,
            """
                )
            )
        )

        # Agios Athanasios rain timeseries data
        self.ts_agios_rain.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2015-10-23 15:10,0,
            2015-10-23 15:20,0.2,
            2015-10-23 15:30,1.4,
            """
                )
            )
        )

        # Agios Athanasios temperature timeseries data
        self.ts_agios_temperature.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2015-10-23 15:00,40,
            2015-10-23 15:10,39,
            2015-10-23 15:20,38.5,
            """
                )
            )
        )

    @RandomSynopticRoot()
    @override_settings(TEST_MATPLOTLIB=True)
    def test_synoptic_group(self):
        create_static_files()
        filename = os.path.join(
            settings.ENHYDRIS_SYNOPTIC_ROOT, self.sg1.slug, "index.html"
        )
        self.assertHtmlContains(
            filename,
            text=textwrap.dedent(
                """\
            <div class="panel panel-default">
              <div class="panel-heading">
                <a href="station/{}/">Komboti</a>
              </div>
              <div class="panel-body">
                <dl class="dl-horizontal">
                  <dt>Last update</dt><dd>2015-10-22 15:20 EET (+0200)</dd>
                  <dt>&nbsp;</dt><dd></dd>
                  <dt>Rain</dt><dd>0 mm</dd>
                  <dt>Air temperature</dt><dd>17 °C</dd>
                  <dt>Wind (speed)</dt><dd>3.0 m/s</dd>
                  <dt>Wind (gust)</dt><dd>4.1 m/s</dd>
                </dl>
              </div>
            </div>
            """.format(
                    self.sgs1.id
                )
            ),
        )
        self.assertHtmlContains(
            filename,
            text=textwrap.dedent(
                """\
            <div class="panel panel-default">
              <div class="panel-heading">
                <a href="station/{}/">Agios Athanasios</a>
              </div>
              <div class="panel-body">
                <dl class="dl-horizontal">
                  <dt>Last update</dt><dd>2015-10-23 15:20 EET (+0200)</dd>
                  <dt>&nbsp;</dt><dd></dd>
                  <dt>Rain</dt><dd>0.2 mm</dd>
                  <dt>Air temperature</dt><dd>38.5 °C</dd>
                </dl>
              </div>
            </div>
            """.format(
                    self.sgs2.id
                )
            ),
        )

    @RandomSynopticRoot()
    @override_settings(TEST_MATPLOTLIB=True)
    def test_synoptic_station(self):
        create_static_files()
        filename = os.path.join(
            settings.ENHYDRIS_SYNOPTIC_ROOT,
            self.sg1.slug,
            "station",
            str(self.sgs2.id),
            "index.html",
        )
        self.assertHtmlContains(
            filename,
            text=textwrap.dedent(
                """\
            <div class="panel panel-default">
              <div class="panel-heading">Latest measurements</div>
              <div class="panel-body">
                <dl class="dl-horizontal">
                  <dt>Last update</dt><dd>2015-10-23 15:20 EET (+0200)</dd>
                  <dt>&nbsp;</dt><dd></dd>
                  <dt>Rain</dt><dd>0.2 mm</dd>
                  <dt>Air temperature</dt><dd>38.5 °C</dd>
                </dl>
              </div>
            </div>
            """
            ),
        )

    @RandomSynopticRoot()
    @override_settings(TEST_MATPLOTLIB=True)
    def test_chart(self):
        # We will not compare a bitmap because it is unreliable; instead, we
        # will verify that an image was created and that the data that was used
        # in the image creation was correct. See
        # http://stackoverflow.com/questions/27948126#27948646

        # Do the job
        create_static_files()

        # Check that it is a png of substantial length
        filename = os.path.join(
            settings.ENHYDRIS_SYNOPTIC_ROOT, "chart", str(self.sts2_2.id) + ".png"
        )
        self.assertTrue(filename.endswith(".png"))
        self.assertGreater(os.stat(filename).st_size, 100)

        # Retrieve data
        datastr = open(filename.replace("png", "dat")).read()
        self.assertTrue(datastr.startswith("(array("))
        datastr = datastr.replace("array", "np.array")
        data_array = eval(datastr)

        # Check that the data is correct
        desired_result = np.array(
            [
                [days_since_epoch(2015, 10, 23, 15, 00), 40],
                [days_since_epoch(2015, 10, 23, 15, 10), 39],
                [days_since_epoch(2015, 10, 23, 15, 20), 38.5],
            ]
        )
        np.testing.assert_allclose(data_array, desired_result)

    @RandomSynopticRoot()
    @override_settings(TEST_MATPLOTLIB=True)
    def test_grouped_chart(self):
        # Here we test the wind speed chart, which is grouped with wind gust.
        # See the comment in test_chart() above; the same applies here.

        # Do the job
        create_static_files()

        # Check that it is a png of substantial length
        filename = os.path.join(
            settings.ENHYDRIS_SYNOPTIC_ROOT, "chart", str(self.sts1_3.id) + ".png"
        )
        self.assertTrue(filename.endswith(".png"))
        self.assertGreater(os.stat(filename).st_size, 100)

        # Retrieve data
        datastr = open(filename.replace("png", "dat")).read()
        self.assertTrue(datastr.startswith("(array("))
        datastr = datastr.replace("array", "np.array")
        data_array = eval(datastr)

        desired_result = (
            np.array(
                [
                    [days_since_epoch(2015, 10, 22, 15, 00), 3.7],
                    [days_since_epoch(2015, 10, 22, 15, 10), 4.5],
                    [days_since_epoch(2015, 10, 22, 15, 20), 4.1],
                ]
            ),
            np.array(
                [
                    [days_since_epoch(2015, 10, 22, 15, 00), 2.9],
                    [days_since_epoch(2015, 10, 22, 15, 10), 3.2],
                    [days_since_epoch(2015, 10, 22, 15, 20), 3],
                ]
            ),
        )
        np.testing.assert_allclose(data_array[0], desired_result[0])
        np.testing.assert_allclose(data_array[1], desired_result[1])
