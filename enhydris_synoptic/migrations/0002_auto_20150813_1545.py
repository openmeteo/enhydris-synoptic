# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('enhydris_synoptic', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='synopticgroupstation',
            options={'ordering': ['synoptic_group', 'order']},
        ),
        migrations.AlterModelOptions(
            name='synoptictimeseries',
            options={'ordering': ['synoptic_group_station', 'order'], 'verbose_name_plural': 'Synoptic timeseries'},
        ),
    ]
