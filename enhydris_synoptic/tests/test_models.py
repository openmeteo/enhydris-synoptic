import datetime as dt

from django.db import IntegrityError
from django.test import TestCase

from enhydris.models import Station, Timeseries
from enhydris.tests import RandomEnhydrisTimeseriesDataDir
from model_mommy import mommy

from enhydris_synoptic.models import (
    SynopticGroup,
    SynopticGroupStation,
    SynopticTimeseries,
)

from .data import TestData


class SynopticGroupTestCase(TestCase):
    def test_create(self):
        sg = SynopticGroup(name="hello", slug="world")
        sg.save()
        self.assertEqual(SynopticGroup.objects.first().slug, "world")

    def test_update(self):
        mommy.make(SynopticGroup, slug="hello")
        sg = SynopticGroup.objects.first()
        sg.name = "hello world"
        sg.save()
        self.assertEqual(SynopticGroup.objects.first().name, "hello world")

    def test_delete(self):
        mommy.make(SynopticGroup)
        sg = SynopticGroup.objects.first()
        sg.delete()
        self.assertFalse(SynopticGroup.objects.exists())

    def test_str(self):
        sg = mommy.make(SynopticGroup, name="hello world")
        self.assertEqual(str(sg), "hello world")


class SynopticGroupStationTestCase(TestCase):
    def test_create(self):
        sg = mommy.make(SynopticGroup)
        station = mommy.make(Station)
        sgs = SynopticGroupStation(synoptic_group=sg, order=1, station=station)
        sgs.save()
        self.assertEqual(SynopticGroupStation.objects.first().order, 1)

    def test_update(self):
        mommy.make(SynopticGroupStation, order=1)
        sgs = SynopticGroupStation.objects.first()
        sgs.order = 2
        sgs.save()
        self.assertEqual(SynopticGroupStation.objects.first().order, 2)

    def test_delete(self):
        mommy.make(SynopticGroupStation)
        sgs = SynopticGroupStation.objects.first()
        sgs.delete()
        self.assertFalse(SynopticGroupStation.objects.exists())

    def test_str(self):
        sgs = mommy.make(SynopticGroupStation, station__name="hello")
        self.assertEqual(str(sgs), "hello")


class SynopticGroupStationCheckIntegrityTestCase(TestCase):
    def setUp(self):
        self.station_komboti = mommy.make(Station, name="Komboti")
        self.timeseries_rain = mommy.make(
            Timeseries, gentity=self.station_komboti, name="Rain"
        )
        self.timeseries_temperature1 = mommy.make(
            Timeseries, gentity=self.station_komboti, name="Temperature"
        )
        self.timeseries_temperature2 = mommy.make(
            Timeseries, gentity=self.station_komboti, name="Temperature"
        )

        # Create SynopticGroup
        sg1 = SynopticGroup.objects.create(slug="mygroup")

        # Create SynopticGroupStation
        self.sgs1 = SynopticGroupStation.objects.create(
            synoptic_group=sg1, station=self.station_komboti, order=1
        )

        # SynopticTimeseries
        self.sts1_1 = SynopticTimeseries.objects.create(
            synoptic_group_station=self.sgs1, timeseries=self.timeseries_rain, order=1
        )
        self.sts1_2 = SynopticTimeseries.objects.create(
            synoptic_group_station=self.sgs1,
            timeseries=self.timeseries_temperature1,
            order=2,
        )

    def test_check_timeseries_integrity(self):
        self.sgs1.check_timeseries_integrity()  # No exception thrown

    def test_raises_error_if_there_are_gaps_in_the_order(self):
        self.sts1_2.order = 3
        self.sts1_2.save()
        with self.assertRaises(IntegrityError):
            self.sgs1.check_timeseries_integrity()

    def test_raises_error_if_numbering_does_not_start_with_1(self):
        self.sts1_1.order = 3
        self.sts1_1.save()
        with self.assertRaises(IntegrityError):
            self.sgs1.check_timeseries_integrity()

    def test_raises_error_if_two_timeseries_have_same_order(self):
        self.sts1_2.order = 1
        with self.assertRaises(IntegrityError):
            self.sts1_2.save()

    def test_third_timeseries_is_added_without_problem(self):
        self.sts1_3 = SynopticTimeseries.objects.create(
            synoptic_group_station=self.sgs1,
            timeseries=self.timeseries_temperature2,
            order=3,
        )
        self.sgs1.check_timeseries_integrity()  # No exception thrown


@RandomEnhydrisTimeseriesDataDir()
class LastCommonDateTestCase(TestCase):
    def setUp(self):
        self.data = TestData()

    def test_last_common_date(self):
        self.assertEqual(
            self.data.sgs_agios.last_common_date,
            dt.datetime(
                2015, 10, 23, 15, 20, tzinfo=dt.timezone(dt.timedelta(hours=2), "EET")
            ),
        )


@RandomEnhydrisTimeseriesDataDir()
class SynopticGroupStationSynopticTimeseriesTestCase(TestCase):
    def setUp(self):
        self.data = TestData()

    def test_value(self):
        self.assertAlmostEqual(self.data.sgs_agios.synoptic_timeseries[0].value, 0.2)

    def test_data(self):
        self.assertEqual(len(self.data.sgs_agios.synoptic_timeseries[0].data), 2)


class SynopticTimeseriesTestCase(TestCase):
    def test_create(self):
        sgs = mommy.make(SynopticGroupStation)
        timeseries = mommy.make(Timeseries)
        st = SynopticTimeseries(
            synoptic_group_station=sgs, timeseries=timeseries, order=1, title="hello"
        )
        st.save()
        self.assertEqual(SynopticTimeseries.objects.first().title, "hello")

    def test_update(self):
        mommy.make(SynopticTimeseries)
        st = SynopticTimeseries.objects.first()
        st.title = "hello"
        st.save()
        self.assertEqual(SynopticTimeseries.objects.first().title, "hello")

    def test_delete(self):
        mommy.make(SynopticTimeseries)
        st = SynopticTimeseries.objects.first()
        st.delete()
        self.assertFalse(SynopticTimeseries.objects.exists())

    def test_str_when_subtitle_is_empty(self):
        st = mommy.make(
            SynopticTimeseries,
            synoptic_group_station__station__name="mystation",
            title="mysynoptictimeseries",
            subtitle="",
            timeseries__name="",
        )
        self.assertEqual(str(st), "mystation - mysynoptictimeseries")

    def test_str_when_subtitle_is_specified(self):
        st = mommy.make(
            SynopticTimeseries,
            synoptic_group_station__station__name="mystation",
            title="mysynoptictimeseries",
            subtitle="mysubtitle",
            timeseries__name="mytimeseries",
        )
        self.assertEqual(str(st), "mystation - mysynoptictimeseries (mysubtitle)")

    def test_str_when_title_is_unspecified(self):
        st = mommy.make(
            SynopticTimeseries,
            synoptic_group_station__station__name="mystation",
            title="",
            subtitle="mysubtitle",
            timeseries__name="mytimeseries",
        )
        self.assertEqual(str(st), "mystation - mytimeseries (mysubtitle)")
