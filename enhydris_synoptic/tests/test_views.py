# coding: utf-8

from __future__ import unicode_literals

from six import StringIO
import textwrap

from django.core.urlresolvers import reverse
import django.db
from django.test import TestCase

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
        timeseries2_2 = Timeseries.objects.get(gentity=station2,
                                               name='Air temperature')

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
            2015-10-23 15:00,0.2,
            2015-10-23 15:10,0,
            2015-10-23 15:20,1.4,
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
        SynopticTimeseries.objects.create(synoptic_group_station=self.sgs1,
                                          timeseries=timeseries1_1, order=1)
        SynopticTimeseries.objects.create(synoptic_group_station=self.sgs1,
                                          timeseries=timeseries1_2, order=2)
        SynopticTimeseries.objects.create(synoptic_group_station=self.sgs2,
                                          timeseries=timeseries2_1, order=1)
        SynopticTimeseries.objects.create(synoptic_group_station=self.sgs2,
                                          timeseries=timeseries2_2, order=2)

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
