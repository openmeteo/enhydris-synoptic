from django.db import migrations


def populate_synoptictimeseriesgroup_timeseriesgroup(apps, schema_editor):
    SynopticTimeseriesGroup = apps.get_model(
        "enhydris_synoptic", "SynopticTimeseriesGroup"
    )
    for stsg in SynopticTimeseriesGroup.objects.all():
        stsg.timeseries_group = stsg.timeseries.timeseries_group
        stsg.save()


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0037_timeseries_groups"),
        ("enhydris_synoptic", "0006_timeseries_groups"),
    ]

    operations = [
        migrations.RunPython(populate_synoptictimeseriesgroup_timeseriesgroup)
    ]
