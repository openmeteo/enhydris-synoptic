import datetime as dt

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, models
from django.utils.translation import ugettext as _

from enhydris.models import Station, TimeseriesGroup, TimeZone

# NOTE: Confusingly, there are three distinct uses of "group" here. They refer to
# different things:
# - A "timeseries group" refers to an Enhydris time series group. See Enhydris's
#   database documentation for details on what this is.
# - A "synoptic group" means a report prepared by this app. It has a slug (e.g. "ntua")
#   so that visitors can view the report at a URL (e.g.
#   "https://openmeteo.org/synoptic/ntua/"). It was named thus because it is a report
#   about a group of stations, so "synoptic group" actually means "a group of stations
#   for which we create a synoptic report".
# - In a given synoptic group, two timeseries groups may be "groupped" together; that
#   is, shown in the same chart. This is achieved with
#   SynopticTimeseriesGroup.group_with.
#
# SynopticTimeseriesGroup means "a timeseries group used in a synoptic station".
#
# Yes, this sucks. Ideas on improving it are welcome.


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

    def queue_warning(self, asyntsg):
        if not hasattr(self, "early_warnings"):
            self.early_warnings = {}
        timestamp = asyntsg.synoptic_group_station.last_common_date.replace(tzinfo=None)
        self.early_warnings[asyntsg.get_title()] = {
            "station": asyntsg.synoptic_group_station.station.name,
            "timestamp": timestamp.isoformat(sep=" ", timespec="minutes"),
            "variable": asyntsg.get_title(),
            "value": asyntsg.value,
            "low_limit": asyntsg.low_limit,
            "high_limit": asyntsg.high_limit,
        }

    def send_early_warning_emails(self):
        if len(getattr(self, "early_warnings", {})) == 0:
            return
        emails = [x.email for x in self.earlywarningemail_set.all()]
        content = ""
        for var in self.early_warnings:
            content += self._get_early_warning_line(self.early_warnings[var])
        subject = self._get_warning_email_subject()
        send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, emails)

    def _get_warning_email_subject(self):
        stations = ", ".join({v["station"] for k, v in self.early_warnings.items()})
        return _("Enhydris early warning ({})").format(stations)

    def _get_early_warning_line(self, data):
        station = data["station"]
        variable = data["variable"]
        value = data["value"]
        timestamp = data["timestamp"]
        if data["high_limit"] is not None and value > data["high_limit"]:
            lowhigh = "high"
            limit = data["high_limit"]
        else:
            lowhigh = "low"
            limit = data["low_limit"]
        return f"{station} {timestamp} {variable} {value} ({lowhigh} limit {limit})\n"


class EarlyWarningEmail(models.Model):
    synoptic_group = models.ForeignKey(SynopticGroup, on_delete=models.CASCADE)
    email = models.EmailField()

    class Meta:
        verbose_name = _("Email address to send early warnings")
        verbose_name_plural = _("Where to send early warnings")


class SynopticGroupStation(models.Model):
    synoptic_group = models.ForeignKey(SynopticGroup, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()
    timeseries_groups = models.ManyToManyField(
        TimeseriesGroup, through="SynopticTimeseriesGroup"
    )

    class Meta:
        unique_together = (("synoptic_group", "order"),)
        ordering = ["synoptic_group", "order"]

    def __str__(self):
        return str(self.station)

    def check_timeseries_groups_integrity(self, *args, **kwargs):
        """
        This method checks whether the timeseries_groups.through.order field starts with
        1 and is contiguous, and that groupped time series are in order.  I wrote it
        thinking I could use it somewhere, but I don't think it's possible (see
        http://stackoverflow.com/questions/33500336/). However, since I wrote it, I keep
        it, although I'm not using it anywhere. Mind you, it's unit-tested.
        """
        # Check that time series are in order
        expected_order = 0
        for syn_ts in self.synoptictimeseriesgroup_set.order_by("order"):
            expected_order += 1
            if syn_ts.order != expected_order:
                raise IntegrityError(
                    _("The order of the data must start from 1 and be continuous.")
                )

        # Check that grouped time series are in order
        current_synopticgroup_leader = None
        previous_synoptictimeseriesgroup = None
        for syn_tsg in self.synoptictimeseriesgroup_set.order_by("order"):
            if not syn_tsg.group_with:
                current_synopticgroup_leader = None
                continue
            current_synopticgroup_leader = (
                current_synopticgroup_leader or previous_synoptictimeseriesgroup
            )
            if syn_tsg.group_with.id != current_synopticgroup_leader.id:
                raise IntegrityError(
                    _("Groupped time series must be ordered together.")
                )
            previous_synoptictimeseriesgroup = syn_tsg

        super(SynopticGroupStation, self).save(*args, **kwargs)

    @property
    def synoptic_timeseries_groups(self):
        """List of synoptic timeseries group objects with data.

        The objects in the list have attribute "data", which is a pandas dataframe with
        the last 24 hours preceding the last common date, "value", which is the
        value at the last common date, and "value_status" which is the string "ok",
        "high" or "low", depending on where "value" is compared to low_limit and
        high_limit.
        """
        if not hasattr(self, "_synoptic_timeseries_groups"):
            self._determine_timeseries_groups()
        return self._synoptic_timeseries_groups

    def _determine_timeseries_groups(self):
        if self.last_common_date is None:
            self._synoptic_timeseries_groups = []
            return
        start_date = self.last_common_date - dt.timedelta(minutes=1439)
        self._synoptic_timeseries_groups = list(self.synoptictimeseriesgroup_set.all())
        self.error = False  # This may be changed by _set_ts_value()
        for asyntsg in self._synoptic_timeseries_groups:
            asyntsg.data = asyntsg.timeseries_group.default_timeseries.get_data(
                start_date=start_date, end_date=self.last_common_date
            ).data
            self._set_tsg_value(asyntsg)
            self._set_tsg_value_status(asyntsg)

    def _set_tsg_value(self, asyntsg):
        try:
            asyntsg.value = asyntsg.data.loc[
                self.last_common_date.replace(tzinfo=None)
            ]["value"]
        except KeyError:
            self.error = True

    def _set_tsg_value_status(self, asyntsg):
        if not hasattr(asyntsg, "value") or asyntsg.value is None:
            asyntsg.value_status = "error"
        elif asyntsg.low_limit is not None and asyntsg.value < asyntsg.low_limit:
            asyntsg.value_status = "low"
            self.synoptic_group.queue_warning(asyntsg)
        elif asyntsg.high_limit is not None and asyntsg.value > asyntsg.high_limit:
            asyntsg.value_status = "high"
            self.synoptic_group.queue_warning(asyntsg)
        else:
            asyntsg.value_status = "ok"

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
        for asyntsg in self.synoptictimeseriesgroup_set.all():
            end_date = asyntsg.timeseries_group.default_timeseries.end_date
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

    @property
    def target_url(self):
        target = getattr(
            settings,
            "ENHYDRIS_SYNOPTIC_STATION_LINK_TARGET",
            "station/{station.id}/",
        )
        return target.format(station=self.station)


class SynopticTimeseriesGroupManager(models.Manager):
    def primary(self):
        """Return only time series groups that don't have group_with."""
        return self.filter(group_with__isnull=True)


class SynopticTimeseriesGroup(models.Model):
    synoptic_group_station = models.ForeignKey(
        SynopticGroupStation, on_delete=models.CASCADE
    )
    timeseries_group = models.ForeignKey(TimeseriesGroup, on_delete=models.CASCADE)
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

    objects = SynopticTimeseriesGroupManager()

    class Meta:
        unique_together = (
            ("synoptic_group_station", "timeseries_group"),
            ("synoptic_group_station", "order"),
        )
        ordering = ["synoptic_group_station", "order"]

    def __str__(self):
        return str(self.synoptic_group_station) + " - " + self.full_name

    def get_title(self):
        return self.title or self.timeseries_group.get_name()

    def get_subtitle(self):
        return self.subtitle or self.timeseries_group.get_name()

    @property
    def full_name(self):
        result = self.get_title()
        if self.subtitle:
            result += " (" + self.subtitle + ")"
        return result
