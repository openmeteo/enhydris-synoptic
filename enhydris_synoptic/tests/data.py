import textwrap
from io import StringIO

from enhydris.models import Station, Timeseries
from model_mommy import mommy

from enhydris_synoptic.models import (
    SynopticGroup,
    SynopticGroupStation,
    SynopticTimeseries,
)


class TestData:
    def __init__(self):
        self._create_stations()
        self._create_synoptic_group()
        self._create_synoptic_group_stations()
        self._create_timeseries()
        self._create_synoptic_timeseries()
        self._create_timeseries_data()

    def _create_stations(self):
        self.station_komboti = mommy.make(Station, name="Komboti")
        self.station_agios = mommy.make(Station, name="Agios Athanasios")

    def _create_synoptic_group(self):
        self.sg1 = mommy.make(SynopticGroup, slug="mygroup")

    def _create_synoptic_group_stations(self):
        self.sgs_komboti = mommy.make(
            SynopticGroupStation,
            synoptic_group=self.sg1,
            station=self.station_komboti,
            order=1,
        )
        self.sgs_agios = mommy.make(
            SynopticGroupStation,
            synoptic_group=self.sg1,
            station=self.station_agios,
            order=2,
        )

    def _create_timeseries(self):
        self._create_timeseries_for_komboti()
        self._create_timeseries_for_agios()

    def _create_timeseries_for_komboti(self):
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

    def _create_timeseries_for_agios(self):
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

    def _create_synoptic_timeseries(self):
        self._create_synoptic_timeseries_for_komboti()
        self._create_synoptic_timeseries_for_agios()

    def _create_synoptic_timeseries_for_komboti(self):
        self.sts1_1 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs_komboti,
            timeseries=self.ts_komboti_rain,
            order=1,
        )
        self.sts1_2 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs_komboti,
            timeseries=self.ts_komboti_temperature,
            order=2,
        )
        self.sts1_3 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs_komboti,
            timeseries=self.ts_komboti_wind_speed,
            title="Wind",
            subtitle="speed",
            order=3,
        )
        self.sts1_4 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs_komboti,
            timeseries=self.ts_komboti_wind_gust,
            title="Wind",
            subtitle="gust",
            group_with=self.sts1_3,
            order=4,
        )

    def _create_synoptic_timeseries_for_agios(self):
        self.sts2_1 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs_agios,
            timeseries=self.ts_agios_rain,
            order=1,
        )
        self.sts2_2 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs_agios,
            timeseries=self.ts_agios_temperature,
            order=2,
        )

    def _create_timeseries_data(self):
        self._create_timeseries_data_for_komboti_rain()
        self._create_timeseries_data_for_komboti_temperature()
        self._create_timeseries_data_for_komboti_wind_speed()
        self._create_timeseries_data_for_komboti_wind_gust()
        self._create_timeseries_data_for_agios_rain()
        self._create_timeseries_data_for_agios_temperature()

    def _create_timeseries_data_for_komboti_rain(self):
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

    def _create_timeseries_data_for_komboti_temperature(self):
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

    def _create_timeseries_data_for_komboti_wind_speed(self):
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

    def _create_timeseries_data_for_komboti_wind_gust(self):
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

    def _create_timeseries_data_for_agios_rain(self):
        self.ts_agios_rain.set_data(
            StringIO(
                textwrap.dedent(
                    """\
            2015-10-22 15:00,0,
            2015-10-23 15:10,0,
            2015-10-23 15:20,0.2,
            2015-10-23 15:30,1.4,
            """
                )
            )
        )

    def _create_timeseries_data_for_agios_temperature(self):
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
