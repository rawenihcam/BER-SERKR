import datetime

from math import floor
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Max
from django.utils import timezone

from .control import IncompleteProgram

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
        
    def get_programs(self):
        programs = Program.objects.filter(lifter__exact=self.id)
        return programs
        
    def get_started_programs(self):
        programs = self.get_programs().filter(start_date__isnull=False
                    ).filter(end_date__isnull=True)
        return programs

    def get_next_workouts(self):
        programs = self.get_started_programs()
        workouts = []
        
        for program in programs:
            workout = program.get_next_workout()
            if workout:
                workouts.append(workout)
            
        return workouts
        
    def get_last_workouts(self):
        workouts = Workout_Log.objects.filter(workout__workout_group__program__lifter__exact=self.id
                    ).order_by('-workout_date', '-id')[:50]
        return workouts
    
    
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
        
    def get_max(self, exercise):
        max = Lifter_Stats.objects.filter(lifter__exact=self.id
                ).filter(reps__exact=1
                ).filter(exercise__exact=exercise.id
                ).order_by('-entry_date', '-weight'
                ).first()
                
        return max
        
    def get_prs(self):
        stats = Lifter_Stats.objects.filter(lifter__exact=self.id)
        exercise_combos = stats.values('exercise','reps').annotate(max_weight=Max('weight'))
        prs = Lifter_Stats.objects.filter(lifter__exact=0)
                            
        # Possibly a way to do this without loop and with queryset, but idk, TODO
        for exercise_combo in exercise_combos:
            pr = stats.filter(exercise__exact=exercise_combo['exercise']
                    ).filter(reps__exact=exercise_combo['reps']
                    ).filter(weight__exact=exercise_combo['max_weight'])
                    
            prs = prs.union (pr, all=True)
        
        return prs
        
    def get_pr(self, exercise, reps):
        pr = Lifter_Stats.objects.filter(lifter__exact=self.id
                ).filter(exercise__exact=exercise
                ).filter(reps__exact=reps
                ).order_by('-weight'
                ).first()
         
        return pr
    
    def get_last_prs(self):
        prs = Lifter_Stats.objects.raw('''select * 
                                             from hamask_lifter_stats ls 
                                            where weight = (select max(ls2.weight) 
                                                              from hamask_lifter_stats ls2 
                                                             where ls2.exercise_id = ls.exercise_id 
                                                               and ls2.reps = ls.reps) 
                                                             order by ls.entry_date desc''')[:5]
        
        return prs
        
    def get_stats(self):
        stats = Lifter_Stats.objects.filter(lifter__exact=self.id
                    ).order_by('-entry_date', 'exercise__name')
                    
        return stats
        
    def get_weight_unit(self):
        unit = ''
        if self.measurement_system == 'METRC':
            unit = 'kg'
        elif self.measurement_system == 'IMPER':
            unit = 'lbs'
            
        return unit;
    
class Exercise (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE, blank=True, null=True, editable=False)
    name = models.CharField (max_length=60)
    has_stats = models.BooleanField (default=True)
    
    def __str__(self):
        return self.name
    
class Program (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE)
    rep_scheme_choices = (
        ('MAX_PERCENTAGE', '% of Max'),
        ('RPE', 'RPE'),
        ('WEIGHT', 'Weight'),
    )
    rep_scheme = models.CharField (max_length=30, choices=rep_scheme_choices, blank=True, null=True)
    name = models.CharField (max_length=60)
    start_date = models.DateField (blank=True, null=True)
    end_date = models.DateField (blank=True, null=True)
    is_current = models.BooleanField (default=False)
    auto_update_stats = models.BooleanField (default=True)
    repeatable = models.BooleanField (default=False)
    rounding_choices = (
        ('NO', 'No rounding'),
        ('0.5', '0.5'),
        ('5', '5'),
        ('10', '10'),
        ('LAST_5', 'Last digit is 5'),
    )
    rounding = models.CharField (max_length=30, choices=rounding_choices, default='NO')
    
    def __str__(self):
        return self.name
        
    def start(self):
        self.start_date = timezone.now()
        self.save()
        
    def end(self):
        self.end_date = timezone.now()
        self.save()
    
    def get_workout_groups(self):
        groups = Workout_Group.objects.filter(program__exact=self.id
                    ).order_by('order')
        
        return groups
    
    def get_next_workout_group_order(self):
        groups = self.get_workout_groups()
        
        if groups.exists():
            order = groups.aggregate(max_order=Max('order'))['max_order'] + 1
        else:
            order = 0
        
        return order
        
    def get_workouts(self):
        workouts = Workout.objects.filter(workout_group__program__exact=self.id)
        return workouts
        
    def get_workout_logs(self):
        logs = Workout_Log.objects.filter(workout__workout_group__program__exact=self.id)
        return logs
        
    def get_last_workout_log(self):
        logs = Workout_Log.objects.filter(workout__workout_group__program__exact=self.id
                ).order_by('-workout_date').first()
        return logs
    
    def get_workout_logs_list(self):
        logs = self.get_workout_logs().values_list('id', flat=True)
        return logs
        
        
    def get_next_workout(self):
        if self.start_date and not self.end_date:
            if self.repeatable:
                log = self.get_last_workout_log()
                
                try:
                    workout = Workout.objects.filter(program__exact=self.id
                                ).filter(order__exact=log.workout.order + 1
                                ).get()
                except ObjectDoesNotExist:
                    None
                else:
                    workout = Workout.objects.filter(program__exact=self.id
                                ).filter(order__exact=1
                                ).get()
            else:
                workouts = self.get_workouts()  
                logs = self.get_workout_logs_list()
                
                workout = workouts.exclude(id__in=list(logs)
                            ).first()
        else:
            workout = None
            
        return workout
        
    def is_ready(self):
        ready = False
        
        try:
            # Must have at least 1 block
            groups = self.get_workout_groups()
            
            if not groups.exists():
                raise IncompleteProgram
            else:
                for group in groups:
                    # Blocks must have at least 1 workout
                    if not group.get_workouts().exists():
                        raise IncompleteProgram
                        
                    # If block uses % of max, lifter must have maxes (though will not validate per exercise)
                    if group.uses_max() and not self.lifter.get_maxes().exists():
                        raise IncompleteProgram
            
        except IncompleteProgram:
            ready = False
        else:
            ready = True
        
        return ready
        
    def complete(self):
        if not self.get_next_workout():
            self.end()
    
class Workout_Group (models.Model):
    program = models.ForeignKey (Program, on_delete=models.CASCADE)
    name = models.CharField (max_length=60)
    order = models.PositiveIntegerField ()
    
    def __str__(self):
        return self.name
        
    def delete(self, *args, **kwargs):
        # Reorder groups
        next_groups = Workout_Group.objects.filter(program__exact=self.program.id
                            ).filter(order__gt=self.order)
                            
        for group in next_groups:
            group.order -= 1
            group.save()
        
        # Call the "real" delete() method
        super(Workout_Group, self).delete(*args, **kwargs)
        
    #def copy(self, *args, **kwargs):
        #
        
        
    def get_workouts(self):
        workouts = Workout.objects.filter(workout_group__exact=self.id
                    ).order_by('order')
        
        return workouts
    
    def get_next_workout_order(self):
        workouts = self.get_workouts()
        
        if workouts.exists():
            order = workouts.aggregate(max_order=Max('order'))['max_order'] + 1
        else:
            order = 0
        
        return order        
    
    def set_order_up(self):
        previous = Workout_Group.objects.filter(program__exact=self.program.id
                    ).filter(order__exact=self.order - 1
                    ).get()
                    
        previous.order += 1
        self.order -= 1
        previous.save()
        self.save()
        
    def set_order_down(self):
        next = Workout_Group.objects.filter(program__exact=self.program.id
                    ).filter(order__exact=self.order + 1
                    ).get()
                  
        next.order -= 1
        self.order += 1
        next.save()
        self.save()
        
    def uses_max(self):
        max = False
        
        if Workout_Exercise.objects.filter(workout__workout_group__exact=self.id
            ).filter(rep_scheme__exact='MAX_PERCENTAGE').exists():
            max = True
            
        return max
    
class Workout (models.Model):
    workout_group = models.ForeignKey (Workout_Group, on_delete=models.CASCADE)
    name = models.CharField (max_length=60)
    order = models.PositiveIntegerField ()
    day_of_week_choices = (
        ('1', 'Sunday'),
        ('2', 'Monday'),
        ('3', 'Tuesday'),
        ('4', 'Wednesday'),
        ('5', 'Thursday'),
        ('6', 'Friday'),
        ('7', 'Saturday'),
    )
    day_of_week = models.CharField (max_length=30, choices=day_of_week_choices, blank=True, null=True)
    
    def __str__(self):
        return self.name
        
    def delete(self, *args, **kwargs):
        # Reorder workouts
        next_workouts = Workout.objects.filter(workout_group__exact=self.workout_group.id
                            ).filter(order__gt=self.order)
                            
        for workout in next_workouts:
            workout.order -= 1
            workout.save()
        
        # Call the "real" delete() method
        super(Workout, self).delete(*args, **kwargs)
        
    def get_workout_exercises(self):
        exercises = Workout_Exercise.objects.filter(workout__exact=self.id
                        ).order_by('order')
        return exercises
        
    def get_next_exercise_order(self):
        exercises = self.get_workout_exercises()
        
        if exercises.exists():
            order = exercises.aggregate(max_order=Max('order'))['max_order'] + 1
        else:
            order = 0
        
        return order
        
    def get_log_create(self):
        # Get existing log or create new
        try:
            log = Workout_Log.objects.get(workout__exact=self.id)
        except ObjectDoesNotExist:
            log = Workout_Log(workout=self.id, workout_date=timezone.now(), status='IN_PROGR')
            log.save()
        
        return log
    
    def log(self, status):
        # Create new log
        log = Workout_Log(workout=self, workout_date=timezone.now(), status=status)  
        log.save()
        
        # Log exercises
        exercises = self.get_workout_exercises()
        for exercise in exercises:
            exercise.log(log)
            
        # Check if program is completed
        self.workout_group.program.complete()
        
    @property
    def full_name(self):
        full_name = self.name
        if self.day_of_week:
            full_name += ' - ' + self.get_day_of_week_display()
            
        return full_name
        
class Workout_Exercise (models.Model):
    workout = models.ForeignKey (Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey (Exercise, on_delete=models.PROTECT)
    rep_scheme_choices = (
        ('MAX_PERCENTAGE', '% of Max'),
        ('RPE', 'RPE'),
        ('WEIGHT', 'Weight'),
    )
    rep_scheme = models.CharField (max_length=30, choices=rep_scheme_choices)
    order = models.PositiveIntegerField ()
    sets = models.PositiveIntegerField (blank=True, null=True)
    reps = models.PositiveIntegerField (blank=True, null=True)
    weight = models.PositiveIntegerField (blank=True, null=True)
    percentage = models.PositiveIntegerField (blank=True, null=True)
    rpe = models.PositiveIntegerField (blank=True, null=True)
    time = models.PositiveIntegerField (blank=True, null=True)
    is_amrap = models.BooleanField (default=False)
    notes = models.TextField (blank=True, null=True)
    
    def delete(self, *args, **kwargs):
        # Reorder exercises
        next_exercises = Workout_Exercise.objects.filter(workout__exact=self.workout.id
                            ).filter(order__gt=self.order)
                            
        for exercise in next_exercises:
            exercise.order -= 1
            exercise.save()
        
        # Call the "real" delete() method
        super(Workout_Exercise, self).delete(*args, **kwargs)
    
    def set_order_up(self):
        previous = Workout_Exercise.objects.filter(workout__exact=self.workout.id
                    ).filter(order__exact=self.order - 1
                    ).get()
                    
        previous.order += 1
        self.order -= 1
        previous.save()
        self.save()
        
    def set_order_down(self):
        next = Workout_Exercise.objects.filter(workout__exact=self.workout.id
                    ).filter(order__exact=self.order + 1
                    ).get()
                  
        next.order -= 1
        self.order += 1
        next.save()
        self.save()
        
    def log(self, workout_log):
        log = Workout_Exercise_Log(workout_log=workout_log
                ,workout_exercise=self
                ,exercise=self.exercise
                ,order=self.order
                ,sets=self.sets
                ,reps=self.reps
                ,weight=self.loading_weight
                ,percentage=self.percentage
                ,rpe=self.rpe
                ,time=self.time
                ,is_amrap=self.is_amrap
                ,notes=self.notes)
                
        log.save()
    
    @property
    def loading(self):
        if not hasattr(self, '_loading'):
            if self.rep_scheme == 'MAX_PERCENTAGE': 
                if self.percentage:
                    self._loading = str(self.percentage) + '%'
                else:
                    self._loading = ''
            elif self.rep_scheme == 'RPE':
                if self.rpe:
                    self._loading = 'RPE ' + str(self.rpe)
                else:
                    self._loading = ''
            elif self.rep_scheme == 'WEIGHT':
                if self.weight:
                    self._loading = str(self.weight) + self.workout.workout_group.program.lifter.get_weight_unit()
                else:
                    self._loading = ''
        
        return self._loading
    
    @property
    def loading_weight(self):
        if not hasattr(self, '_loading_weight'):
            self._loading_weight = None
            if self.rep_scheme == 'MAX_PERCENTAGE': 
                if self.percentage:
                    program = self.workout.workout_group.program
                    lifter = program.lifter
                    max = lifter.get_max(self.exercise)
                    
                    if max:
                        weight = max.weight * (self.percentage / 100)
                        rounding = program.rounding
                        
                        if rounding == '0.5':
                            weight = round(weight * 2) / 2
                        else:
                            weight = round(weight)
                            if rounding == '5':
                                weight = 5 * round(weight / 5)
                            elif rounding == '10':
                                weight = round(weight, -1)
                            elif rounding == 'LAST_5':
                                weight = (floor(weight / 10) * 10) + 5                            
                        
                        self._loading_weight = weight
        
        return self._loading_weight
        
    @property
    def loading_weight_formt(self):
        if not hasattr(self, '_loading_weight_formt'):
            if self.loading_weight:
                self._loading_weight_formt = str(self.loading_weight
                    ) + self.workout.workout_group.program.lifter.get_weight_unit()
            else:
                self._loading_weight_formt = 'No max defined'
        
        return self._loading_weight_formt
        
    @property
    def is_pr(self):
        if not hasattr(self, '_is_pr'):
            self._is_pr = False
            
            pr = program.lifter.get_pr(self.exercise, self.reps)
            if pr and self.weight:
                if self.weight > pr.weight:
                    self._is_pr = True
        
        return self._is_pr
    
class Workout_Log (models.Model):
    workout = models.ForeignKey (Workout, on_delete=models.SET_NULL, blank=True, null=True)
    workout_date = models.DateField ()
    status_choices = (
        ('COMPL', 'Completed'),
        ('SKIPD', 'Skipped'),
        ('IN_PROGR', 'In Progress'),
    )
    status = models.CharField (max_length=30, choices=status_choices)
    notes = models.TextField (blank=True, null=True)
    
    def get_exercise_log(self):
        exercise_log = Workout_Exercise_Log.objects.filter(workout_log__exact=self.id
                        ).order_by('order')
                        
        return exercise_log
    
    def get_exercise_log_formt(self):
        exercise_log = self.get_exercise_log
        list_formt = exercise_log.values_list('exercise', flat=True)
        
        return list_formt
    
class Workout_Exercise_Log (models.Model):
    workout_log = models.ForeignKey (Workout_Log, on_delete=models.CASCADE)
    workout_exercise = models.ForeignKey (Workout_Exercise, on_delete=models.SET_NULL, blank=True, null=True)    
    exercise = models.ForeignKey (Exercise, on_delete=models.PROTECT)
    order = models.PositiveIntegerField ()
    sets = models.PositiveIntegerField (blank=True, null=True)
    reps = models.PositiveIntegerField (blank=True, null=True)
    weight = models.FloatField (blank=True, null=True)
    percentage = models.PositiveIntegerField (blank=True, null=True)
    rpe = models.PositiveIntegerField (blank=True, null=True)
    time = models.PositiveIntegerField (blank=True, null=True)
    is_amrap = models.BooleanField (default=False)
    notes = models.TextField (blank=True, null=True)
    
    def save(self, *args, **kwargs):        
        # Call the "real" save() method
        super(Workout_Exercise_Log, self).save(*args, **kwargs)
        
        # Log PR if applicable
        if self.workout_exercise and self.workout_log.status == 'COMPL':
            program = Program.objects.get(pk=self.workout_exercise.workout.workout_group.program.id)
            
            if program.auto_update_stats:
                # Clean referencing stat
                try:
                    old_stat = Lifter_Stats.objects.get(workout_exercise_log__exact=self.id)
                except ObjectDoesNotExist:
                    None
                else:
                    old_stat.delete()
                
                #Log PR
                pr = program.lifter.get_pr(self.exercise, self.reps)
                if pr and self.weight:
                    if self.weight > pr.weight:
                        stat = Lifter_Stats(lifter=program.lifter
                                ,exercise=self.exercise
                                ,workout_exercise_log=self.id
                                ,reps=self.reps
                                ,weight=self.weight)
                                
                        stat.save()
    
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