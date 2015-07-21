from django import db
from django.views.generic.detail import DetailView

from enhydris_synoptic import models


class SynopticView(DetailView):
    model = models.View

    def get_last_common_date(self, station):
        # We don't actually return the last common date, which would be
        # difficult; instead, we return the minimum of the last dates of the
        # timeseries, which will usually be the last common date. station is
        # an enhydris_synoptic.models.Station object.
        result = None
        for timeseries in station.timeseries:
            end_date = timeseries.end_date
            if end_date and ((not result) or (end_date < result)):
                result = end_date
        return result

    def get_context_data(self, **kwargs):
        context = super(SynopticView, self).get_context_data(self, **kwargs)
        for station in self.object.stations:
            station.last_common_date = self.get_last_common_date(station)
            for timeseries in station.timeseries:
                tsrecords = Timeseries(timeseries.id)
                tsrecords.read_from_db(db.connection)
                timeseries.value = tsrecords[station.last_common_date]
        return context
