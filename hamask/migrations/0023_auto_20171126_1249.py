# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-11-26 17:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hamask', '0022_lifter_weight'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workout_exercise',
            name='rpe',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='workout_exercise',
            name='weight',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='workout_exercise_log',
            name='rpe',
            field=models.FloatField(blank=True, null=True),
        ),
    ]