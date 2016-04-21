# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def setup_group_names(apps, schema_editor):
    """Set the name of each group to be the slug with a capital initial."""
    SynopticGroup = apps.get_model("enhydris_synoptic", "SynopticGroup")
    for synoptic_group in SynopticGroup.objects.all():
        synoptic_group.name = synoptic_group.slug.title()
        synoptic_group.save()


class Migration(migrations.Migration):

    dependencies = [
        ('enhydris_synoptic', '0005_auto_20160421_1119'),
    ]

    operations = [
        migrations.RunPython(setup_group_names,
                             reverse_code=migrations.RunPython.noop),
    ]
