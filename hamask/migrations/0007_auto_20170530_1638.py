# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-30 20:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hamask', '0006_auto_20170530_1415'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workout',
            name='order',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='workout_group',
            name='order',
            field=models.PositiveIntegerField(),
        ),
    ]
