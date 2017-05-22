# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-22 17:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hamask', '0002_auto_20170516_1143'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercise',
            name='lifter',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='hamask.Lifter'),
        ),
        migrations.AlterField(
            model_name='lifter_stats',
            name='reps',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='lifter_stats',
            name='time',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='lifter_stats',
            name='weight',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]