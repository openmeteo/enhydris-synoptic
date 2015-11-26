# coding: utf-8

from __future__ import unicode_literals

from datetime import datetime
from six import StringIO
import textwrap

import django.db
from django.core.urlresolvers import reverse
from django.test import override_settings, TestCase

from enhydris.hcore.models import Station, Timeseries
from model_mommy import mommy
import numpy as np
from pthelma.timeseries import Timeseries as PthelmaTimeseries

from enhydris_synoptic.models import (SynopticGroup, SynopticGroupStation,
                                      SynopticTimeseries)


class SynopticTestCase(TestCase):

    def setUp(self):
        # Station
        self.station_komboti = mommy.make(Station, name='Komboti')
        self.station_agios = mommy.make(Station, name='Agios Athanasios')

        # Synoptic group
        self.sg1 = mommy.make(SynopticGroup, name='My Group')

        # SynopticGroupStation
        self.sgs1 = mommy.make(SynopticGroupStation,
                               synoptic_group=self.sg1,
                               station=self.station_komboti,
                               order=1)
        self.sgs2 = mommy.make(SynopticGroupStation,
                               synoptic_group=self.sg1,
                               station=self.station_agios,
                               order=2)

        # Timeseries
        self.ts_komboti_rain = mommy.make(
            Timeseries, gentity=self.station_komboti, name='Rain',
            unit_of_measurement__symbol='mm')
        self.ts_komboti_temperature = mommy.make(
            Timeseries, gentity=self.station_komboti, name='Air temperature',
            unit_of_measurement__symbol='°C')
        self.ts_agios_rain = mommy.make(
            Timeseries, gentity=self.station_agios, name='Rain', precision=1,
            unit_of_measurement__symbol='mm')
        self.ts_agios_temperature = mommy.make(
            Timeseries, gentity=self.station_agios, name='Air temperature',
            precision=1, unit_of_measurement__symbol='°C')

        # SynopticTimeseries
        self.sts1_1 = mommy.make(SynopticTimeseries,
                                 synoptic_group_station=self.sgs1,
                                 timeseries=self.ts_komboti_rain,
                                 order=1)
        self.sts1_2 = mommy.make(SynopticTimeseries,
                                 synoptic_group_station=self.sgs1,
                                 timeseries=self.ts_komboti_temperature,
                                 order=2)
        self.sts2_1 = mommy.make(SynopticTimeseries,
                                 synoptic_group_station=self.sgs2,
                                 timeseries=self.ts_agios_rain,
                                 order=1)
        self.sts2_2 = mommy.make(SynopticTimeseries,
                                 synoptic_group_station=self.sgs2,
                                 timeseries=self.ts_agios_temperature,
                                 order=2)

        # Komboti rain timeseries data
        komboti_rain = PthelmaTimeseries(self.ts_komboti_rain.id)
        komboti_rain.read(StringIO(textwrap.dedent(
            """\
            2015-10-22 15:00,0,
            2015-10-22 15:10,0,
            2015-10-22 15:20,0,
            """)))
        komboti_rain.write_to_db(django.db.connection, commit=False)

        # Komboti temperature timeseries data
        komboti_temperature = PthelmaTimeseries(self.ts_komboti_temperature.id)
        komboti_temperature.read(StringIO(textwrap.dedent(
            """\
            2015-10-22 15:00,15,
            2015-10-22 15:10,16,
            2015-10-22 15:20,17,
            """)))
        komboti_temperature.write_to_db(django.db.connection, commit=False)

        # Agios Athanasios rain timeseries data
        agios_rain = PthelmaTimeseries(self.ts_agios_rain.id)
        agios_rain.read(StringIO(textwrap.dedent(
            """\
            2015-10-23 15:10,0,
            2015-10-23 15:20,0.2,
            2015-10-23 15:30,1.4,
            """)))
        agios_rain.write_to_db(django.db.connection, commit=False)

        # Agios Athanasios temperature timeseries data
        agios_temperature = PthelmaTimeseries(self.ts_agios_temperature.id)
        agios_temperature.read(StringIO(textwrap.dedent(
            """\
            2015-10-23 15:00,40,
            2015-10-23 15:10,39,
            2015-10-23 15:20,38.5,
            """)))
        agios_temperature.write_to_db(django.db.connection, commit=False)

    def test_synoptic_view(self):
        response = self.client.get(reverse('synoptic_view',
                                           kwargs={'slug': 'My Group'}))
        self.assertTemplateUsed(response, 'synopticgroup.html')
        self.assertContains(response, html=True, text=textwrap.dedent(
            """\
            <div class="panel panel-default">
              <div class="panel-heading"><a href="{}">Komboti</a></div>
              <div class="panel-body">
                <dl class="dl-horizontal">
                  <dt>Last update</dt><dd>2015-10-22 15:20  (+0000)</dd>
                  <dt>&nbsp;</dt><dd></dd>
                  <dt>Rain</dt><dd>0 mm</dd>
                  <dt>Air temperature</dt><dd>17 °C</dd>
                </dl>
              </div>
            </div>
            """.format(reverse('synoptic_station_view',
                               kwargs={'pk': self.sgs1.id}))))
        self.assertContains(response, html=True, text=textwrap.dedent(
            """\
            <div class="panel panel-default">
              <div class="panel-heading"><a href="{}">Agios Athanasios</a>
              </div>
              <div class="panel-body">
                <dl class="dl-horizontal">
                  <dt>Last update</dt><dd>2015-10-23 15:20  (+0000)</dd>
                  <dt>&nbsp;</dt><dd></dd>
                  <dt>Rain</dt><dd>0.2 mm</dd>
                  <dt>Air temperature</dt><dd>38.5 °C</dd>
                </dl>
              </div>
            </div>
            """.format(reverse('synoptic_station_view',
                               kwargs={'pk': self.sgs2.id}))))

    def test_synoptic_station_view(self):
        response = self.client.get(reverse('synoptic_station_view',
                                           kwargs={'pk': self.sgs2.id}))
        self.assertTemplateUsed(response, 'synopticgroupstation.html')
        self.assertContains(response, html=True, text=textwrap.dedent(
            """\
            <div class="panel panel-default">
              <div class="panel-heading">Latest measurements</div>
              <div class="panel-body">
                <dl class="dl-horizontal">
                  <dt>Last update</dt><dd>2015-10-23 15:20  (+0000)</dd>
                  <dt>&nbsp;</dt><dd></dd>
                  <dt>Rain</dt><dd>0.2 mm</dd>
                  <dt>Air temperature</dt><dd>38.5 °C</dd>
                </dl>
              </div>
            </div>
            """.format(reverse('synoptic_station_view',
                               kwargs={'pk': self.sgs2.id}))))

    @override_settings(TEST_MATPLOTLIB=True)
    def test_synoptic_chart_view(self):
        # We will not compare a bitmap because it is unreliable; instead, we
        # will verify that an image was returned and that the data that was
        # used in the image creation was correct. See
        # http://stackoverflow.com/questions/27948126#27948646
        # The view knows that it must return the data in an HTTP header
        # because we have set TEST_MATPLOTLIB above.

        # Get response
        response = self.client.get(reverse('synoptic_chart_view',
                                           kwargs={'pk': self.sts2_2.id}))

        # Check that it is a png of substantial length
        self.assertEquals(response['Content-Type'], 'image/png')
        self.assertGreater(len(response.content), 100)

        # Retrieve data
        datastr = response['X-Matplotlib-Data']
        self.assertTrue(datastr.startswith('array('))
        datastr = 'np.' + datastr
        data_array = eval(datastr)

        # Check that the data is correct
        def dt(y, mo, d, h, mi):
            adelta = datetime(y, mo, d, h, mi) - datetime(1, 1, 1)
            return adelta.days + 1 + adelta.seconds / 86400.0
        desired_result = np.array([
            [dt(2015, 10, 23, 15, 00), 40],
            [dt(2015, 10, 23, 15, 10), 39],
            [dt(2015, 10, 23, 15, 20), 38.5],
        ])
        np.testing.assert_allclose(data_array, desired_result)
