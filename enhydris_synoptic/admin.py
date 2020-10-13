from django.contrib import admin

from enhydris.models import TimeseriesGroup
from enhydris_synoptic.models import SynopticGroup, SynopticGroupStation


class StationInline(admin.TabularInline):
    model = SynopticGroup.stations.through

    def get_formset(self, request, obj=None, **kwargs):
        """
        Override the get_formset method to remove the add/change buttons beside the
        foreign key pull-down menus in the inline.
        """
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form
        widget = form.base_fields["station"].widget
        widget.can_add_related = False
        widget.can_change_related = False
        return formset


@admin.register(SynopticGroup)
class GroupAdmin(admin.ModelAdmin):
    inlines = [StationInline]
    exclude = ["stations"]


class SynopticTimeseriesGroupInline(admin.TabularInline):
    model = SynopticGroupStation.timeseries_groups.through

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name in ("timeseries_group", "group_with"):
            synopticgroupstation_id = int(request.resolver_match.kwargs["object_id"])
            station = SynopticGroupStation.objects.get(
                id=synopticgroupstation_id
            ).station
            kwargs["queryset"] = TimeseriesGroup.objects.filter(gentity_id=station)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(SynopticGroupStation)
class GroupStationAdmin(admin.ModelAdmin):
    inlines = [SynopticTimeseriesGroupInline]
    exclude = ["synoptic_group", "station", "order", "timeseries_group"]
    list_filter = ["synoptic_group"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
        pass
