# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-04 21:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sms', '0004_tip_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='tip',
            name='new',
            field=models.BooleanField(default=True),
        ),
    ]