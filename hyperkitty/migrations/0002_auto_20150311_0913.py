# -*- coding: utf-8 -*-
# pylint: skip-file
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hyperkitty', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='email',
            name='in_reply_to',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
    ]
