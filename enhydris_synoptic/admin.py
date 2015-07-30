from django.contrib import admin

from enhydris.hcore.models import Timeseries

from enhydris_synoptic.models import SynopticGroup, SynopticGroupStation


class StationInline(admin.TabularInline):
    model = SynopticGroup.stations.through
    show_change_link = True


@admin.register(SynopticGroup)
class GroupAdmin(admin.ModelAdmin):
    inlines = [
        StationInline,
    ]
    exclude = ['stations']


class TimeseriesInline(admin.TabularInline):
    model = SynopticGroupStation.timeseries.through

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'timeseries':
            synopticgroupstation_id = int(request.resolver_match.args[0])
            station = SynopticGroupStation.objects.get(
                id=synopticgroupstation_id).station
            kwargs["queryset"] = Timeseries.objects.filter(gentity_id=station)
        return super(TimeseriesInline, self).formfield_for_foreignkey(
            db_field, request, **kwargs)


@admin.register(SynopticGroupStation)
class GroupStationAdmin(admin.ModelAdmin):
    inlines = [TimeseriesInline]
    exclude = ['synoptic_group', 'station', 'order', 'timeseries']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
        pass
