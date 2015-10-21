# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('enhydris_synoptic', '0002_auto_20150813_1545'),
    ]

    operations = [
        migrations.AddField(
            model_name='synoptictimeseries',
            name='default_chart_max',
            field=models.FloatField(help_text='Maximum value of the y axis of the chart. If the variable goes lower, the chart will automatically expand. If empty, the chart will always expand just enough to accomodate the value.', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='synoptictimeseries',
            name='default_chart_min',
            field=models.FloatField(help_text='Minimum value of the y axis of the chart. If the variable goes lower, the chart will automatically expand. If empty, the chart will always expand just enough to accomodate the value.', null=True, blank=True),
        ),
    ]
