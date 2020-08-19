import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0037_timeseries_groups"),
        ("enhydris_synoptic", "0007_timeseries_groups_b"),
    ]

    operations = [
        migrations.RemoveField(model_name="synopticgroupstation", name="timeseries"),
        migrations.AlterField(
            model_name="synoptictimeseriesgroup",
            name="timeseries_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="enhydris.TimeseriesGroup",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="synoptictimeseriesgroup",
            unique_together={
                ("synoptic_group_station", "order"),
                ("synoptic_group_station", "timeseries_group"),
            },
        ),
        migrations.RemoveField(
            model_name="synoptictimeseriesgroup", name="timeseries",
        ),
    ]
