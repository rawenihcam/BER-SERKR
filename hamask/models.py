import datetime

from django.db import models
from django.utils import timezone


class Lifter (models.Model):
    first_name = models.CharField (max_length=60)
    last_name = models.CharField (max_length=60)
    email = models.EmailField (max_length=254, unique=True)
    measurement_system_choices = (
        ('IMPER', 'Imperial'),
        ('METRC', 'Metric'),
    )
    measurement_system = models.CharField (max_length=30, choices=measurement_system_choices, default='METRC')
    age = models.PositiveIntegerField (max_length=3, blank=True)
    sex_choices = (('MALE', 'Male'), ('FEML', 'Female'),)
    sex = models.CharField (max_length=30, choices=sex_choices, blank=True)
    
    def __str__(self):
        return self.first_name + ' ' + self.last_name
    
class Exercise (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE)
    name = models.CharField (max_length=60)
    has_stats = models.BooleanField (default=True)
    
    def __str__(self):
        return self.name
        
class Lifter_Stats (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE)
    exercise = models.ForeignKey (Exercise, on_delete=models.PROTECT)
    entry_date = models.DateField (default=date.today)
    reps = models.PositiveIntegerField (max_length=4, blank=True)
    weight = models.PositiveIntegerField (max_length=4, blank=True)
    time = models.PositiveIntegerField (max_length=4, blank=True)

class Program (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE)
    #rep_scheme
    name = models.CharField (max_length=60)
    start_date = models.DateField (blank=True)
    is_current = models.BooleanField (default=False)
    auto_update_stats = models.BooleanField (default=True)
    #block_type
    rounding_choices = (
        ('NO', 'No rounding'),
        ('2.5', '2.5'),
        ('5', '5'),
        ('10', '10'),
        ('LAST_5', 'Last digit is 5'),
    )
    rounding = models.CharField (max_length=30, choices=rounding_choices, default='NO')
    
    def __str__(self):
        return self.name
    
class Workout_Group (models.Model):
    program = models.ForeignKey (Program, on_delete=models.CASCADE)
    name = models.CharField (max_length=60)
    
    def __str__(self):
        return self.name
    
class Workout (models.Model):
    workout_group = models.ForeignKey (Workout_Group, on_delete=models.CASCADE)
    name = models.CharField (max_length=60)
    
    def __str__(self):
        return self.name
        
class Workout_Exercise (models.Model):
    workout = models.ForeignKey (Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey (Exercise, on_delete=models.PROTECT)
    #rep_scheme
    sets = models.PositiveIntegerField (max_length=4, blank=True)
    reps = models.PositiveIntegerField (max_length=4, blank=True)
    weight = models.PositiveIntegerField (max_length=4, blank=True)
    percentage = models.PositiveIntegerField (max_length=3, blank=True)
    rpe = models.PositiveIntegerField (max_length=2, blank=True)
    time = models.PositiveIntegerField (max_length=4, blank=True)
    is_amrap = models.BooleanField (default=False)
    notes = models.TextField (blank=True)