import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0037_timeseries_groups"),
        ("enhydris_synoptic", "0005_synopticgroup_time_zone"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="SynopticTimeseries", new_name="SynopticTimeseriesGroup"
        ),
        migrations.AlterModelOptions(
            name="synoptictimeseriesgroup",
            options={"ordering": ["synoptic_group_station", "order"]},
        ),
        migrations.AddField(
            model_name="synopticgroupstation",
            name="timeseries_groups",
            field=models.ManyToManyField(
                through="enhydris_synoptic.SynopticTimeseriesGroup",
                to="enhydris.TimeseriesGroup",
            ),
        ),
        migrations.AddField(
            model_name="synoptictimeseriesgroup",
            name="timeseries_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.TimeseriesGroup",
                null=True,
            ),
            preserve_default=False,
        ),
    ]
