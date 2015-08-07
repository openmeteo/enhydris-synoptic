# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SynopticGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='SynopticGroupStation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField()),
                ('station', models.ForeignKey(to='hcore.Station')),
                ('synoptic_group', models.ForeignKey(to='enhydris_synoptic.SynopticGroup')),
            ],
        ),
        migrations.CreateModel(
            name='SynopticTimeseries',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField()),
                ('synoptic_group_station', models.ForeignKey(to='enhydris_synoptic.SynopticGroupStation')),
                ('timeseries', models.ForeignKey(to='hcore.Timeseries')),
            ],
            options={
                'verbose_name_plural': 'Synoptic timeseries',
            },
        ),
        migrations.AddField(
            model_name='synopticgroupstation',
            name='timeseries',
            field=models.ManyToManyField(to='hcore.Timeseries', through='enhydris_synoptic.SynopticTimeseries'),
        ),
        migrations.AddField(
            model_name='synopticgroup',
            name='stations',
            field=models.ManyToManyField(to='hcore.Station', through='enhydris_synoptic.SynopticGroupStation'),
        ),
        migrations.AlterUniqueTogether(
            name='synoptictimeseries',
            unique_together=set([('synoptic_group_station', 'order'), ('synoptic_group_station', 'timeseries')]),
        ),
        migrations.AlterUniqueTogether(
            name='synopticgroupstation',
            unique_together=set([('synoptic_group', 'order')]),
        ),
    ]
