# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-20 18:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hamask', '0011_auto_20170615_1520'),
    ]

    operations = [
        migrations.AddField(
            model_name='workout',
            name='day_of_week',
            field=models.CharField(blank=True, choices=[('1', 'Sunday'), ('2', 'Monday'), ('3', 'Tuesday'), ('4', 'Wednesday'), ('5', 'Thursday'), ('6', 'Friday'), ('7', 'Saturday')], max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='program',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]