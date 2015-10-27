# coding: utf-8

from __future__ import unicode_literals

from datetime import datetime
from six import StringIO
import textwrap

from django.core.urlresolvers import reverse
import django.db
from django.test import override_settings, TestCase

import numpy as np
from pthelma.timeseries import Timeseries as PthelmaTimeseries

import enhydris.hcore.tests.test_views
from enhydris.hcore.models import Station, Timeseries
from enhydris_synoptic.models import (SynopticGroup, SynopticGroupStation,
                                      SynopticTimeseries)


class SynopticTestCase(TestCase):

    def setUp(self):
        # Create test data in Enhydris
        enhydris.hcore.tests.test_views.create_test_data()
        station1 = Station.objects.get(name='Komboti')
        station2 = Station.objects.get(name='Agios Athanasios')
        timeseries1_1 = Timeseries.objects.get(gentity=station1, name='Rain')
        timeseries1_2 = Timeseries.objects.get(gentity=station1,
                                               name='Air temperature')
        timeseries2_1 = Timeseries.objects.get(gentity=station2, name='Rain')
        timeseries2_1.precision = 1
        timeseries2_1.save()
        timeseries2_2 = Timeseries.objects.get(gentity=station2,
                                               name='Air temperature')
        timeseries2_2.precision = 1
        timeseries2_2.save()

        # Komboti rain timeseries
        komboti_rain = PthelmaTimeseries(timeseries1_1.id)
        komboti_rain.read(StringIO(textwrap.dedent(
            """\
            2015-10-22 15:00,0,
            2015-10-22 15:10,0,
            2015-10-22 15:20,0,
            """)))
        komboti_rain.write_to_db(django.db.connection, commit=False)

        # Komboti temperature timeseries
        komboti_temperature = PthelmaTimeseries(timeseries1_2.id)
        komboti_temperature.read(StringIO(textwrap.dedent(
            """\
            2015-10-22 15:00,15,
            2015-10-22 15:10,16,
            2015-10-22 15:20,17,
            """)))
        komboti_temperature.write_to_db(django.db.connection, commit=False)

        # Agios Athanasios rain timeseries
        agios_rain = PthelmaTimeseries(timeseries2_1.id)
        agios_rain.read(StringIO(textwrap.dedent(
            """\
            2015-10-23 15:10,0,
            2015-10-23 15:20,0.2,
            2015-10-23 15:30,1.4,
            """)))
        agios_rain.write_to_db(django.db.connection, commit=False)

        # Agios Athanasios temperature timeseries
        agios_temperature = PthelmaTimeseries(timeseries2_2.id)
        agios_temperature.read(StringIO(textwrap.dedent(
            """\
            2015-10-23 15:00,40,
            2015-10-23 15:10,39,
            2015-10-23 15:20,38.5,
            """)))
        agios_temperature.write_to_db(django.db.connection, commit=False)

        # SynopticGroup
        sg1 = SynopticGroup.objects.create(name='My Group')

        # SynopticGroupStation
        self.sgs1 = SynopticGroupStation.objects.create(
            synoptic_group=sg1, station=station1, order=1)
        self.sgs2 = SynopticGroupStation.objects.create(
            synoptic_group=sg1, station=station2, order=2)

        # SynopticTimeseries
        self.sts1_1 = SynopticTimeseries.objects.create(
            synoptic_group_station=self.sgs1, timeseries=timeseries1_1,
            order=1)
        self.sts1_2 = SynopticTimeseries.objects.create(
            synoptic_group_station=self.sgs1, timeseries=timeseries1_2,
            order=2)
        self.sts2_1 = SynopticTimeseries.objects.create(
            synoptic_group_station=self.sgs2, timeseries=timeseries2_1,
            order=1)
        self.sts2_2 = SynopticTimeseries.objects.create(
            synoptic_group_station=self.sgs2, timeseries=timeseries2_2,
            order=2)

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
