from django.db import IntegrityError
from django.test import TestCase

from enhydris.hcore.models import Station, Timeseries
from model_mommy import mommy

from enhydris_synoptic.models import (SynopticGroup, SynopticGroupStation,
                                      SynopticTimeseries)


class SynopticGroupStationTestCase(TestCase):

    def setUp(self):
        self.station_komboti = mommy.make(Station, name='Komboti')
        self.timeseries_rain = mommy.make(
            Timeseries, gentity=self.station_komboti, name='Rain')
        self.timeseries_temperature1 = mommy.make(
            Timeseries, gentity=self.station_komboti, name='Temperature')
        self.timeseries_temperature2 = mommy.make(
            Timeseries, gentity=self.station_komboti, name='Temperature')

    def test_check_timeseries_integrity(self):
        # Create SynopticGroup
        sg1 = SynopticGroup.objects.create(slug='mygroup')

        # Create SynopticGroupStation
        self.sgs1 = SynopticGroupStation.objects.create(
            synoptic_group=sg1, station=self.station_komboti, order=1)

        # SynopticTimeseries
        self.sts1_1 = SynopticTimeseries.objects.create(
            synoptic_group_station=self.sgs1,
            timeseries=self.timeseries_rain, order=1)
        self.sts1_2 = SynopticTimeseries.objects.create(
            synoptic_group_station=self.sgs1,
            timeseries=self.timeseries_temperature1, order=2)

        # So far the integrity is fine
        self.sgs1.check_timeseries_integrity()  # No exception thrown

        # Mess up the order in various ways and verify an error is thrown
        self.sts1_2.order = 3
        self.sts1_2.save()
        self.assertRaises(IntegrityError, self.sgs1.check_timeseries_integrity)
        self.sts1_1.order = 2
        self.sts1_1.save()
        self.assertRaises(IntegrityError, self.sgs1.check_timeseries_integrity)

        # Go back to a state with integrity, and add a third time series
        self.sts1_1.order = 1
        self.sts1_1.save()
        self.sts1_2.order = 2
        self.sts1_2.save()
        self.sts1_3 = SynopticTimeseries.objects.create(
            synoptic_group_station=self.sgs1,
            timeseries=self.timeseries_temperature2, order=3)
        self.sgs1.check_timeseries_integrity()  # No exception thrown
