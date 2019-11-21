import datetime as dt

from django.db import IntegrityError, models
from django.utils.translation import ugettext as _

from enhydris.models import Station, Timeseries, TimeZone


class SynopticGroup(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, help_text="Identifier to be used in URL")
    stations = models.ManyToManyField(Station, through="SynopticGroupStation")
    time_zone = models.ForeignKey(TimeZone, on_delete=models.CASCADE)
    fresh_time_limit = models.DurationField(
        help_text=(
            "Maximum time that may have elapsed for the data to be considered fresh. "
            "For data older than this the date on the map shows red; for fresh data it "
            "shows green. Specify it in seconds or in the format 'DD HH:MM:SS'."
        )
    )

    def __str__(self):
        return self.name


class SynopticGroupStation(models.Model):
    synoptic_group = models.ForeignKey(SynopticGroup, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()
    timeseries = models.ManyToManyField(Timeseries, through="SynopticTimeseries")

    class Meta:
        unique_together = (("synoptic_group", "order"),)
        ordering = ["synoptic_group", "order"]

    def __str__(self):
        return str(self.station)

    def check_timeseries_integrity(self, *args, **kwargs):
        """
        This method checks whether the timeseries.through.order field starts
        with 1 and is contiguous, and that groupped time series are in order.
        I wrote it thinking I could use it somewhere, but I don't think it's
        possible (see http://stackoverflow.com/questions/33500336/). However,
        since I wrote it, I keep it, although I'm not using it anywhere. Mind
        you, it's unit-tested.
        """
        # Check that time series are in order
        expected_order = 0
        for syn_ts in self.synoptictimeseries_set.order_by("order"):
            expected_order += 1
            if syn_ts.order != expected_order:
                raise IntegrityError(
                    _(
                        "The order of the time series must start from 1 and be "
                        "continuous."
                    )
                )

        # Check that grouped time series are in order
        current_group_leader = None
        previous_synoptictimeseries = None
        for syn_ts in self.synoptictimeseries_set.order_by("order"):
            if not syn_ts.group_with:
                current_group_leader = None
                continue
            current_group_leader = current_group_leader or previous_synoptictimeseries
            if syn_ts.group_with.id != current_group_leader.id:
                raise IntegrityError(
                    _("Groupped time series must be ordered together.")
                )
            previous_synoptictimeseries = syn_ts

        super(SynopticGroupStation, self).save(*args, **kwargs)

    @property
    def synoptic_timeseries(self):
        """List of synoptic timeseries objects with data.

        The objects in the list have attribute "data", which is a pandas dataframe with
        the last 24 hours preceding the last common date, "value", which is the
        value at the last common date, and "value_status" which is the string "ok",
        "high" or "low", depending on where "value" is compared to low_limit and
        high_limit.
        """
        if not hasattr(self, "_synoptic_timeseries"):
            self._determine_timeseries()
        return self._synoptic_timeseries

    def _determine_timeseries(self):
        if self.last_common_date is None:
            self._synoptic_timeseries = []
            return
        start_date = self.last_common_date - dt.timedelta(minutes=1339)
        self._synoptic_timeseries = list(self.synoptictimeseries_set.all())
        self.error = False  # This may be changed by _set_ts_value()
        for asynts in self._synoptic_timeseries:
            asynts.data = asynts.timeseries.get_data(
                start_date=start_date, end_date=self.last_common_date
            ).data
            self._set_ts_value(asynts)
            self._set_ts_value_status(asynts)

    def _set_ts_value(self, asynts):
        try:
            asynts.value = asynts.data.loc[self.last_common_date.replace(tzinfo=None)][
                "value"
            ]
        except KeyError:
            self.error = True

    def _set_ts_value_status(self, asynts):
        if not hasattr(asynts, "value") or asynts.value is None:
            asynts.value_status = "error"
        elif asynts.low_limit is not None and asynts.value < asynts.low_limit:
            asynts.value_status = "low"
        elif asynts.high_limit is not None and asynts.value > asynts.high_limit:
            asynts.value_status = "high"
        else:
            asynts.value_status = "ok"

    @property
    def last_common_date(self):
        if not hasattr(self, "_last_common_date"):
            self._determine_last_common_date()
        return self._last_common_date

    def _determine_last_common_date(self):
        # We don't actually get the last common date, which would be difficult; instead,
        # we get the minimum of the last dates of the timeseries, which will usually be
        # the last common date. station is an enhydris_synoptic.models.Station object.
        last_common_date = None
        for asynts in self.synoptictimeseries_set.all():
            end_date = asynts.timeseries.end_date
            if end_date and ((not last_common_date) or (end_date < last_common_date)):
                last_common_date = end_date
        self._last_common_date = last_common_date

    @property
    def last_common_date_pretty(self):
        return self.last_common_date and self.last_common_date.strftime(
            "%d %b %Y %H:%M %Z (%z)"
        )

    @property
    def last_common_date_pretty_without_timezone(self):
        return self.last_common_date and self.last_common_date.astimezone(
            self.synoptic_group.time_zone.as_tzinfo
        ).strftime("%d %b %Y %H:%M")

    @property
    def freshness(self):
        if self.last_common_date is None:
            return "old"
        oldness = dt.datetime.now(dt.timezone.utc) - self.last_common_date
        is_old = oldness > self.synoptic_group.fresh_time_limit
        return "old" if is_old else "recent"


class SynopticTimeseriesManager(models.Manager):
    def primary(self):
        """Return only time series that don't have group_with."""
        return self.filter(group_with__isnull=True)


class SynopticTimeseries(models.Model):
    synoptic_group_station = models.ForeignKey(
        SynopticGroupStation, on_delete=models.CASCADE
    )
    timeseries = models.ForeignKey(Timeseries, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()
    title = models.CharField(
        max_length=50,
        blank=True,
        help_text=_(
            "Used as the chart title and as the time series title in the report. "
            "Time series in different stations with the same title will show as a "
            "layer on the map. Leave empty to use the time series name."
        ),
    )
    low_limit = models.FloatField(
        blank=True,
        null=True,
        help_text=_(
            "If the variable goes lower than this, it will be shown red on the map."
        ),
    )
    high_limit = models.FloatField(
        blank=True,
        null=True,
        help_text=_(
            "If the variable goes higher than this, it will be shown red on the map."
        ),
    )
    group_with = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text=_(
            "Specify this field if you want to group this time series with "
            "another in the same chart and in the report."
        ),
    )
    subtitle = models.CharField(
        max_length=50,
        blank=True,
        help_text=_(
            "If time series are grouped, this is shows in the legend of the chart "
            "and in the report, in brackets."
        ),
    )
    default_chart_min = models.FloatField(
        blank=True,
        null=True,
        help_text=_(
            "Minimum value of the y axis of the chart. If the variable goes "
            "lower, the chart will automatically expand. If empty, the chart will "
            "always expand just enough to accomodate the value."
        ),
    )
    default_chart_max = models.FloatField(
        blank=True,
        null=True,
        help_text=_(
            "Maximum value of the y axis of the chart. If the variable goes "
            "lower, the chart will automatically expand. If empty, the chart will "
            "always expand just enough to accomodate the value."
        ),
    )

    objects = SynopticTimeseriesManager()

    class Meta:
        unique_together = (
            ("synoptic_group_station", "timeseries"),
            ("synoptic_group_station", "order"),
        )
        ordering = ["synoptic_group_station", "order"]
        verbose_name_plural = "Synoptic timeseries"

    def __str__(self):
        return str(self.synoptic_group_station) + " - " + self.full_name

    def get_title(self):
        return self.title or self.timeseries.name

    def get_subtitle(self):
        return self.subtitle or self.timeseries.name

    @property
    def full_name(self):
        result = self.get_title()
        if self.subtitle:
            result += " (" + self.subtitle + ")"
        return result
