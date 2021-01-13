import datetime as dt
import textwrap
from io import StringIO

from django.db import IntegrityError
from django.test import TestCase

from freezegun import freeze_time
from model_mommy import mommy

from enhydris.models import Station, Timeseries, TimeseriesGroup, TimeZone
from enhydris_synoptic.models import (
    SynopticGroup,
    SynopticGroupStation,
    SynopticTimeseriesGroup,
)

from .data import TestData


class SynopticGroupTestCase(TestCase):
    def test_create(self):
        sg = SynopticGroup(
            name="hello",
            slug="world",
            fresh_time_limit=dt.timedelta(minutes=60),
            time_zone=TimeZone.objects.create(code="EET", utc_offset=120),
        )
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
        self.timeseries_group_rain = mommy.make(
            TimeseriesGroup, gentity=self.station_komboti, name="Rain"
        )
        self.timeseries_group_temperature1 = mommy.make(
            TimeseriesGroup, gentity=self.station_komboti, name="Temperature"
        )
        self.timeseries_group_temperature2 = mommy.make(
            TimeseriesGroup, gentity=self.station_komboti, name="Temperature"
        )

        # Create SynopticGroup
        sg1 = SynopticGroup.objects.create(
            slug="mygroup",
            fresh_time_limit=dt.timedelta(minutes=10),
            time_zone=TimeZone.objects.create(code="EET", utc_offset=120),
        )

        # Create SynopticGroupStation
        self.sgs1 = SynopticGroupStation.objects.create(
            synoptic_group=sg1, station=self.station_komboti, order=1
        )

        # SynopticTimeseries
        self.stsg1_1 = SynopticTimeseriesGroup.objects.create(
            synoptic_group_station=self.sgs1,
            timeseries_group=self.timeseries_group_rain,
            order=1,
        )
        self.stsg1_2 = SynopticTimeseriesGroup.objects.create(
            synoptic_group_station=self.sgs1,
            timeseries_group=self.timeseries_group_temperature1,
            order=2,
        )

    def test_check_timeseries_groups_integrity(self):
        self.sgs1.check_timeseries_groups_integrity()  # No exception thrown

    def test_raises_error_if_there_are_gaps_in_the_order(self):
        self.stsg1_2.order = 3
        self.stsg1_2.save()
        with self.assertRaises(IntegrityError):
            self.sgs1.check_timeseries_groups_integrity()

    def test_raises_error_if_numbering_does_not_start_with_1(self):
        self.stsg1_1.order = 3
        self.stsg1_1.save()
        with self.assertRaises(IntegrityError):
            self.sgs1.check_timeseries_groups_integrity()

    def test_raises_error_if_two_timeseries_have_same_order(self):
        self.stsg1_2.order = 1
        with self.assertRaises(IntegrityError):
            self.stsg1_2.save()

    def test_third_timeseries_is_added_without_problem(self):
        self.stsg1_3 = SynopticTimeseriesGroup.objects.create(
            synoptic_group_station=self.sgs1,
            timeseries_group=self.timeseries_group_temperature2,
            order=3,
        )
        self.sgs1.check_timeseries_groups_integrity()  # No exception thrown


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

    def test_last_common_date_pretty(self):
        self.assertEqual(
            self.data.sgs_agios.last_common_date_pretty, "23 Oct 2015 15:20 EET (+0200)"
        )

    def test_last_common_date_pretty_without_timezone(self):
        self.assertEqual(
            self.data.sgs_agios.last_common_date_pretty_without_timezone,
            "23 Oct 2015 14:20",
        )


class SynopticGroupStationSynopticTimeseriesGroupTestCase(TestCase):
    def setUp(self):
        self.data = TestData()

    def test_value(self):
        self.assertAlmostEqual(
            self.data.sgs_agios.synoptic_timeseries_groups[0].value, 0.2
        )

    def test_data(self):
        self.assertEqual(len(self.data.sgs_agios.synoptic_timeseries_groups[0].data), 2)


class FreshnessTestCase(TestCase):
    def setUp(self):
        self.stg = mommy.make(
            SynopticTimeseriesGroup,
            synoptic_group_station__synoptic_group__fresh_time_limit=dt.timedelta(
                minutes=60
            ),
            timeseries_group__time_zone__code="EET",
            timeseries_group__time_zone__utc_offset=120,
        )
        mommy.make(
            Timeseries,
            timeseries_group=self.stg.timeseries_group,
            type=Timeseries.INITIAL,
        )
        self.stg.timeseries_group.default_timeseries.set_data(
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

    @freeze_time("2015-10-22 14:19:59")
    def test_data_is_recent(self):
        self.assertEqual(self.stg.synoptic_group_station.freshness, "recent")

    @freeze_time("2015-10-22 14:20:01")
    def test_data_is_old(self):
        self.assertEqual(self.stg.synoptic_group_station.freshness, "old")


class SynopticTimeseriesGroupTestCase(TestCase):
    def test_create(self):
        sgs = mommy.make(SynopticGroupStation)
        timeseries_group = mommy.make(TimeseriesGroup)
        stg = SynopticTimeseriesGroup(
            synoptic_group_station=sgs,
            timeseries_group=timeseries_group,
            order=1,
            title="hello",
        )
        stg.save()
        self.assertEqual(SynopticTimeseriesGroup.objects.first().title, "hello")

    def test_update(self):
        mommy.make(SynopticTimeseriesGroup)
        stg = SynopticTimeseriesGroup.objects.first()
        stg.title = "hello"
        stg.save()
        self.assertEqual(SynopticTimeseriesGroup.objects.first().title, "hello")

    def test_delete(self):
        mommy.make(SynopticTimeseriesGroup)
        stg = SynopticTimeseriesGroup.objects.first()
        stg.delete()
        self.assertFalse(SynopticTimeseriesGroup.objects.exists())

    def test_str_when_subtitle_is_empty(self):
        stg = mommy.make(
            SynopticTimeseriesGroup,
            synoptic_group_station__station__name="mystation",
            title="mysynoptictimeseriesgroup",
            subtitle="",
            timeseries_group__name="",
        )
        self.assertEqual(str(stg), "mystation - mysynoptictimeseriesgroup")

    def test_str_when_subtitle_is_specified(self):
        stg = mommy.make(
            SynopticTimeseriesGroup,
            synoptic_group_station__station__name="mystation",
            title="mysynoptictimeseriesgroup",
            subtitle="mysubtitle",
            timeseries__name="mytimeseriesgroup",
        )
        self.assertEqual(str(stg), "mystation - mysynoptictimeseriesgroup (mysubtitle)")

    def test_str_when_title_is_unspecified(self):
        stg = mommy.make(
            SynopticTimeseriesGroup,
            synoptic_group_station__station__name="mystation",
            title="",
            subtitle="mysubtitle",
            timeseries_group__name="mytimeseriesgroup",
        )
        self.assertEqual(str(stg), "mystation - mytimeseriesgroup (mysubtitle)")
