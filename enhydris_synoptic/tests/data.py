import datetime as dt
import textwrap
from io import StringIO

from django.contrib.gis.geos import Point

from model_mommy import mommy

from enhydris.models import Station, Timeseries, TimeZone, Variable
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
        self._create_variables()
        self._create_timeseries()
        self._create_synoptic_timeseries()
        self._create_timeseries_data()

    def _create_stations(self):
        self.station_komboti = mommy.make(
            Station, name="Komboti", geom=Point(x=21.06071, y=39.09518, srid=4326)
        )
        self.station_agios = mommy.make(
            Station,
            name="Άγιος Αθανάσιος",
            geom=Point(x=20.87591, y=39.14904, srid=4326),
        )
        self.station_arta = mommy.make(
            Station, name="Arta", geom=Point(x=20.97527, y=39.15104, srid=4326)
        )

    def _create_synoptic_group(self):
        self.sg1 = mommy.make(
            SynopticGroup,
            slug="mygroup",
            fresh_time_limit=dt.timedelta(minutes=60),
            time_zone=TimeZone.objects.create(code="CET", utc_offset=60),
        )

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

        # We fail to create synoptic time series for the following station, but we
        # have it in the group, to verify it will be ignored.
        self.sgs_arta = mommy.make(
            SynopticGroupStation,
            synoptic_group=self.sg1,
            station=self.station_arta,
            order=3,
        )

    def _create_variables(self):
        self.var_rain = mommy.make(Variable, descr="Rain")
        self.var_temperature = mommy.make(Variable, descr="Temperature")
        self.var_wind_speed = mommy.make(Variable, descr="Wind speed")
        self.var_wind_gust = mommy.make(Variable, descr="Wind gust")

    def _create_timeseries(self):
        self._create_timeseries_for_komboti()
        self._create_timeseries_for_agios()

    def _create_timeseries_for_komboti(self):
        self.ts_komboti_rain = mommy.make(
            Timeseries,
            gentity=self.station_komboti,
            variable=self.var_rain,
            name="Rain",
            precision=0,
            unit_of_measurement__symbol="mm",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )
        self.ts_komboti_temperature = mommy.make(
            Timeseries,
            gentity=self.station_komboti,
            variable=self.var_temperature,
            name="Air temperature",
            precision=0,
            unit_of_measurement__symbol="°C",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )
        self.ts_komboti_wind_speed = mommy.make(
            Timeseries,
            gentity=self.station_komboti,
            variable=self.var_wind_speed,
            name="Wind speed",
            precision=1,
            unit_of_measurement__symbol="m/s",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )
        self.ts_komboti_wind_gust = mommy.make(
            Timeseries,
            gentity=self.station_komboti,
            variable=self.var_wind_gust,
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
            variable=self.var_rain,
            name="Rain",
            precision=1,
            unit_of_measurement__symbol="mm",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )
        self.ts_agios_temperature = mommy.make(
            Timeseries,
            gentity=self.station_agios,
            variable=self.var_temperature,
            name="Air temperature",
            precision=1,
            unit_of_measurement__symbol="°C",
            time_zone__code="EET",
            time_zone__utc_offset=120,
        )
        self.ts_agios_wind_speed = mommy.make(
            Timeseries,
            gentity=self.station_agios,
            variable=self.var_wind_speed,
            name="Wind speed",
            precision=1,
            unit_of_measurement__symbol="m/s",
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
            low_limit=17.1,
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
            high_limit=4,
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
        self.sts2_3 = mommy.make(
            SynopticTimeseries,
            synoptic_group_station=self.sgs_agios,
            timeseries=self.ts_agios_wind_speed,
            order=3,
        )

    def _create_timeseries_data(self):
        self._create_timeseries_data_for_komboti_rain()
        self._create_timeseries_data_for_komboti_temperature()
        self._create_timeseries_data_for_komboti_wind_speed()
        self._create_timeseries_data_for_komboti_wind_gust()
        self._create_timeseries_data_for_agios_rain()
        self._create_timeseries_data_for_agios_temperature()
        self._create_timeseries_data_for_agios_wind_speed()

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

    def _create_timeseries_data_for_agios_wind_speed(self):
        # We had this problem where a station was sending too many null values and was
        # resulting in a RuntimeError. The reason was that we were not running
        # set_xlim() to explicitly set the range of the horizontal axis of the chart.
        # If set_xlim() is not used, matplotlib sets it automatically, but if there are
        # null values at the beginning or end of the time series it doesn't set it as
        # we need, and later it had trouble when setting the ticks (the error was too
        # many ticks). So we add a time series full of nulls to test this case. It still
        # has the problem that in the report it shows "nan m/s" instead of something
        # more elegant, but we'll fix this another time.
        self.ts_agios_wind_speed.set_data(
            StringIO(
                textwrap.dedent(
                    """\
                    2015-10-23 15:00,,
                    2015-10-23 15:10,,
                    2015-10-23 15:20,,
                    """
                )
            )
        )
