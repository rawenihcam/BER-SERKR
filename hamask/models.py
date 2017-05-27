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
    age = models.PositiveIntegerField (blank=True)
    sex_choices = (('MALE', 'Male'), ('FEML', 'Female'),)
    sex = models.CharField (max_length=30, choices=sex_choices, blank=True)
    
    def __str__(self):
        return self.first_name + ' ' + self.last_name
        
    def get_maxes(self):
        s = Lifter_Stats.objects.filter(lifter__exact=self.id
                ).filter(reps__exact=1
                ).filter(exercise__name__exact='Squat'
                ).order_by('-entry_date', '-weight')[:1]
        b = Lifter_Stats.objects.filter(lifter__exact=self.id
                ).filter(reps__exact=1
                ).filter(exercise__name__exact='Bench Press'
                ).order_by('-entry_date', '-weight')[:1]
        d = Lifter_Stats.objects.filter(lifter__exact=self.id
                ).filter(reps__exact=1
                ).filter(exercise__name__exact='Deadlift'
                ).order_by('-entry_date', '-weight')[:1]
            
        maxes = s.union (b, d, all=True)
        
        return maxes
        
    def get_last_prs(self):
        prs = Lifter_Stats.objects.filter(lifter__exact=self.id
                ).order_by('-entry_date')[:5]
            
        return prs
        
    def get_stats(self):
        stats = Lifter_Stats.objects.filter(lifter__exact=self.id
                    ).order_by('-entry_date', 'exercise__name')
                    
        return stats
    
class Exercise (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE, blank=True, null=True, editable=False)
    name = models.CharField (max_length=60)
    has_stats = models.BooleanField (default=True)
    
    def __str__(self):
        return self.name

class Rep_Scheme (models.Model):
    code = models.CharField (max_length=30)
    name = models.CharField (max_length=60)
    
class Program (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE)
    rep_scheme = models.ForeignKey (Rep_Scheme, on_delete=models.SET_NULL, blank=True, null=True)
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
    rep_scheme = models.ForeignKey (Rep_Scheme, on_delete=models.PROTECT)
    sets = models.PositiveIntegerField (blank=True)
    reps = models.PositiveIntegerField (blank=True)
    weight = models.PositiveIntegerField (blank=True)
    percentage = models.PositiveIntegerField (blank=True)
    rpe = models.PositiveIntegerField (blank=True)
    time = models.PositiveIntegerField (blank=True)
    is_amrap = models.BooleanField (default=False)
    notes = models.TextField (blank=True)
    
class Workout_Log (models.Model):
    workout = models.ForeignKey (Workout, on_delete=models.SET_NULL, blank=True, null=True)
    workout_date = models.DateField ()
    notes = models.TextField (blank=True)
    
class Workout_Exercise_Log (models.Model):
    Workout_Log = models.ForeignKey (Workout_Log, on_delete=models.CASCADE)
    Workout_Exercise = models.ForeignKey (Workout_Exercise, on_delete=models.SET_NULL, blank=True, null=True)
    sets = models.PositiveIntegerField (blank=True)
    reps = models.PositiveIntegerField (blank=True)
    weight = models.PositiveIntegerField (blank=True)
    percentage = models.PositiveIntegerField (blank=True)
    rpe = models.PositiveIntegerField (blank=True)
    time = models.PositiveIntegerField (blank=True)
    is_amrap = models.BooleanField (default=False)
    notes = models.TextField (blank=True)
    
class Lifter_Stats (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE)
    exercise = models.ForeignKey (Exercise, on_delete=models.PROTECT)
    workout_exercise_log = models.ForeignKey (Workout_Exercise_Log, on_delete=models.SET_NULL, blank=True, null=True)
    entry_date = models.DateField (default=datetime.date.today)
    reps = models.PositiveIntegerField (blank=True, null=True)
    weight = models.PositiveIntegerField (blank=True, null=True)
    time = models.PositiveIntegerField (blank=True, null=True)
    
    def __str__(self):
        return str(self.weight)