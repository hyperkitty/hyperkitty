# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def find_starting_email(apps, schema_editor): # pylint: disable-msg=unused-argument
    # We can't import the Thread model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Thread = apps.get_model("hyperkitty", "Thread")
    Email = apps.get_model("hyperkitty", "Email")
    for thread in Thread.objects.all():
        try:
            thread.starting_email = thread.emails.get(parent_id__isnull=True)
        except Email.DoesNotExist:
            thread.starting_email = thread.emails.order_by("date").first()
        thread.save()

class Migration(migrations.Migration):

    dependencies = [
        ('hyperkitty', '0002_auto_20150311_0913'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='starting_email',
            field=models.OneToOneField(related_name='started_thread', null=True, to='hyperkitty.Email'),
        ),
        migrations.RunPython(find_starting_email),
    ]
