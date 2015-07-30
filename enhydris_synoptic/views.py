from django import db
from django.views.generic.detail import DetailView

from pthelma.timeseries import Timeseries

from enhydris_synoptic import models


class SynopticView(DetailView):
    model = models.SynopticGroup
    slug_field = 'name'
    template_name = 'synopticgroup.html'

    def get_last_common_date(self, station):
        # We don't actually return the last common date, which would be
        # difficult; instead, we return the minimum of the last dates of the
        # timeseries, which will usually be the last common date. station is
        # an enhydris_synoptic.models.Station object.
        result = None
        for timeseries in station.synopticgroupstation_set.get(
                synoptic_group=self.object).timeseries.all():
            end_date = timeseries.end_date
            if end_date and ((not result) or (end_date < result)):
                result = end_date
        return result

    def get_context_data(self, **kwargs):
        context = super(SynopticView, self).get_context_data(**kwargs)
        context['stations'] = self.object.stations.all()[:]
        for station in context['stations']:
            station.last_common_date = self.get_last_common_date(
                station)
            station.synoptic_timeseries = []
            for timeseries in station.synopticgroupstation_set.get(
                    synoptic_group=self.object).timeseries.all():
                station.error = False
                tsrecords = Timeseries(timeseries.id)
                tsrecords.read_from_db(db.connection)
                try:
                    timeseries.value = tsrecords[station.last_common_date]
                except KeyError:
                    station.error = True
                    continue
                station.synoptic_timeseries.append(timeseries)
        return context
