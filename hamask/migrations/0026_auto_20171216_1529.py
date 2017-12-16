# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-16 21:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('hamask', '0025_program_training_max_percentage'),
    ]

    operations = [
        migrations.CreateModel(
            name='Program_Instance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='program',
            name='creation_date',
            field=models.DateField(default=django.utils.timezone.now, editable=False),
        ),
        migrations.AddField(
            model_name='program_instance',
            name='program',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hamask.Program'),
        ),
        migrations.AddField(
            model_name='workout_log',
            name='program_instance',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='hamask.Program_Instance'),
        ),
    ]