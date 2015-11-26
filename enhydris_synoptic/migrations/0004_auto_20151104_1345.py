# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('enhydris_synoptic', '0003_auto_20151021_1041'),
    ]

    operations = [
        migrations.AddField(
            model_name='synoptictimeseries',
            name='group_with',
            field=models.ForeignKey(blank=True, to='enhydris_synoptic.SynopticTimeseries', help_text='Specify this field if you want to group this time series with another in the same chart and in the report.', null=True),
        ),
        migrations.AddField(
            model_name='synoptictimeseries',
            name='subtitle',
            field=models.CharField(help_text='If time series are grouped, this is shows in the legend of the chart and in the report, in brackets.', max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='synoptictimeseries',
            name='title',
            field=models.CharField(help_text='Used as the chart title and as the time series title in the report. Leave empty to use the time series name.', max_length=50, blank=True),
        ),
    ]
