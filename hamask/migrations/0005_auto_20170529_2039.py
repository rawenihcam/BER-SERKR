# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-30 00:39
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hamask', '0004_auto_20170522_1542'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='lifter_stats',
            name='entry_date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
