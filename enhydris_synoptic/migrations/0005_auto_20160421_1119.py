# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enhydris_synoptic', '0004_auto_20151104_1345'),
    ]

    operations = [
        migrations.RenameField(
            model_name='synopticgroup',
            old_name='name',
            new_name='slug',
        ),
        migrations.AlterField(
            model_name='synopticgroup',
            name='slug',
            field=models.SlugField(unique=True, help_text='Identifier to be used in URL'),
        ),
        migrations.AddField(
            model_name='synopticgroup',
            name='name',
            field=models.CharField(default='needs migration', max_length=50),
            preserve_default=False,
        ),
    ]
