import datetime

from math import floor
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Max, Avg, Q, Sum, Count
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
        programs = Program.objects.raw('''
                        select s.id
                          from (select p.id, 1 qmark, rank() over (order by pi.start_date desc) row_order 
                                  from hamask_program p,
                                       (select pi.program_id, 
                                               pi.start_date,
                                               rank() over (partition by pi.program_id order by pi.start_date desc) row_order
                                          from hamask_program_instance pi) pi
                                 where p.id = pi.program_id
                                   and pi.row_order = 1
                                   and p.lifter_id = %(p_lifter)s
                                union all
                                select p.id, 2 qmark, rank() over (order by p.name) row_order
                                  from hamask_program p
                                 where not exists(select 1 from hamask_program_instance pi where pi.program_id = p.id)
                                   and p.lifter_id = %(p_lifter)s) s
                         order by s.qmark, s.row_order'''
                        , {'p_lifter': self.id})
        return programs
        
    def get_all_programs(self):
        programs = Program.objects.filter(lifter__exact=self)
        return programs
        
    def get_started_programs(self):
        running_programs = Program_Instance.objects.filter(program__lifter__exact=self.id
                                ).filter(start_date__isnull=False
                                ).filter(end_date__isnull=True
                                ).values('program')
        programs = Program.objects.filter(id__in=running_programs)
        return programs

    def get_next_workouts(self):
        programs = self.get_started_programs()
        workouts = []
        
        for program in programs:
            workout = program.get_next_workout()
            if workout:
                workouts.append(workout)
            
        return workouts
        
    def get_last_workout(self):
        workouts = Workout_Log.objects.filter(Q(workout__workout_group__program__lifter__exact=self.id) | Q(lifter__exact=self.id)
                    ).filter(status__exact='COMPL'
                    ).order_by('-workout_date', '-id').first()
        return workouts
    
    def get_last_workouts(self):
        workouts = Workout_Log.objects.filter(Q(workout__workout_group__program__lifter__exact=self.id) | Q(lifter__exact=self.id)
                    ).order_by('-workout_date', '-id')[:50]
        return workouts
        
    def get_exercise_logs(self, exercise):
        logs = Workout_Exercise_Log.objects.filter(Q(workout_log__workout__workout_group__program__lifter__exact=self.id) | Q(workout_log__lifter__exact=self.id)
                ).filter(exercise__exact=exercise
                ).filter(workout_log__status__exact='COMPL'
                ).order_by('-workout_log__workout_date')[:50]
                
        return logs    
    
    def get_pl_maxes(self):
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
        
    def get_pl_total(self):
        return self.get_pl_total_at_date(timezone.now())
        
    def get_pl_total_at_date(self, date):
        s = Lifter_Stats.objects.filter(lifter__exact=self.id
                ).filter(reps__exact=1
                ).filter(exercise__name__exact='Squat'
                ).filter(entry_date__lte=date
                ).order_by('-entry_date', '-weight'
                ).first()
        b = Lifter_Stats.objects.filter(lifter__exact=self.id
                ).filter(reps__exact=1
                ).filter(exercise__name__exact='Bench Press'
                ).filter(entry_date__lte=date
                ).order_by('-entry_date', '-weight'
                ).first()
        d = Lifter_Stats.objects.filter(lifter__exact=self.id
                ).filter(reps__exact=1
                ).filter(exercise__name__exact='Deadlift'                
                ).filter(entry_date__lte=date
                ).order_by('-entry_date', '-weight'
                ).first()
                
        return getattr(s, 'weight', 0) + getattr(b, 'weight', 0) + getattr(d, 'weight', 0)
        
    def get_pl_total_chart(self):
        chart = []
        squat = Exercise.objects.get(name__exact='Squat')
        bench = Exercise.objects.get(name__exact='Bench Press')
        deadlift = Exercise.objects.get(name__exact='Deadlift')
        
        maxes = Lifter_Stats.objects.raw('''select 1 id, s.entry_date, sum(s.squat) squat, sum(s.bench) bench, sum(s.deadlift) deadlift
                                              from (select ls.entry_date entry_date, max(ls.weight) squat, 0.0 bench, 0.0 deadlift
                                                     from hamask_lifter_stats ls,
                                                          hamask_exercise e                                             
                                                    where ls.lifter_id = %(p_lifter)s
                                                      and ls.reps = 1
                                                      and e.id = ls.exercise_id
                                                      and e.name = 'Squat'
                                                    group by ls.entry_date
                                                    union all
                                                    select ls.entry_date entry_date, 0.0 squat, max(ls.weight) bench, 0.0 deadlift
                                                     from hamask_lifter_stats ls,
                                                          hamask_exercise e                                             
                                                    where ls.lifter_id = %(p_lifter)s
                                                      and ls.reps = 1
                                                      and e.id = ls.exercise_id
                                                      and e.name = 'Bench Press'
                                                    group by ls.entry_date
                                                    union all
                                                    select ls.entry_date entry_date, 0.0 squat, 0.0 bench, max(ls.weight) deadlift
                                                     from hamask_lifter_stats ls,
                                                          hamask_exercise e                                             
                                                    where ls.lifter_id = %(p_lifter)s
                                                      and ls.reps = 1
                                                      and e.id = ls.exercise_id
                                                      and e.name = 'Deadlift'
                                                    group by ls.entry_date) s
                                             group by s.entry_date
                                             order by entry_date'''
                                            , {'p_lifter': self.id}) 

        for max in maxes:
            if max.squat == 0:
                max.squat = getattr(self.get_max_at_date(max.entry_date, squat), "weight", None)
            if max.bench == 0:
                max.bench = getattr(self.get_max_at_date(max.entry_date, bench), "weight", None)
            if max.deadlift == 0:
                max.deadlift = getattr(self.get_max_at_date(max.entry_date, deadlift), "weight", None)

            if max.squat and max.bench and max.deadlift:
                chart.append({'x': max.entry_date, 'y': max.squat + max.bench + max.deadlift})
                    
        return chart
        
    def get_maxes_chart(self, exercise):
        maxes = Lifter_Stats.objects.raw('''select ls.id, ls.entry_date x, ls.weight y
                                             from hamask_lifter_stats ls 
                                            where ls.lifter_id = %s
                                              and ls.reps = 1
                                              and ls.exercise_id = %s
                                            order by ls.entry_date, ls.weight'''
                                            , [self.id, exercise.id])          
                    
        return maxes
        
    def get_max(self, exercise):
        max = Lifter_Stats.objects.filter(lifter__exact=self.id
                    ).filter(reps__exact=1
                    ).filter(exercise__exact=exercise.id
                    ).order_by('-entry_date', '-weight').first()
                
        return max
        
    def get_max_at_date(self, date, exercise):
        max = Lifter_Stats.objects.filter(lifter__exact=self.id
                    ).filter(reps__exact=1
                    ).filter(exercise__exact=exercise
                    ).filter(entry_date__lte=date
                    ).order_by('-entry_date', '-weight').first()

        return max
        
    def get_prs(self):
        prs = Lifter_Stats.objects.raw('''select ls.id,
                                                  ls.entry_date,
                                                  e.name exercise,
                                                  ls.weight,
                                                  ls.reps
                                             from hamask_lifter_stats ls,
                                                  hamask_exercise e                                             
                                            where ls.lifter_id = %s
                                              and e.id = ls.exercise_id
                                              and weight = (select max(ls2.weight) 
                                                              from hamask_lifter_stats ls2 
                                                             where ls2.lifter_id = ls.lifter_id
                                                               and ls2.exercise_id = ls.exercise_id 
                                                               and ls2.reps = ls.reps) 
                                            order by ls.entry_date desc'''
                                            , [self.id])
        
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
                                            where ls.lifter_id = %s
                                              and weight = (select max(ls2.weight) 
                                                              from hamask_lifter_stats ls2 
                                                             where ls2.lifter_id = ls.lifter_id
                                                               and ls2.exercise_id = ls.exercise_id 
                                                               and ls2.reps = ls.reps) 
                                            order by ls.entry_date desc'''
                                            , [self.id])[:6]
        
        return prs
        
    def get_exercise_prs(self, exercise_id):
        prs = Lifter_Stats.objects.raw('''select s.id
                                            from (select ls.id, ls.reps, rank() over (partition by ls.reps order by ls.weight desc) row_order
                                                    from hamask_lifter_stats ls 
                                                   where ls.lifter_id = %(p_lifter)s
                                                     and ls.exercise_id = %(p_exercise)s) s
                                           where s.row_order = 1
                                           order by s.reps'''
                                            , {'p_lifter': self.id, 'p_exercise': exercise_id})
                    
        return prs
        
    def get_exercise_volume_chart(self, exercise):
        volume = Workout_Log.objects.raw('''  select 1 id, s.x,
                                                         round ( (cast (s.y as decimal) / cast (max_volume.volume as decimal)) * 100) y
                                                    from (  select wl.workout_date x, sum (wel.sets * wel.reps * wel.weight) y
                                                              from hamask_workout_log wl, hamask_workout_exercise_log wel
                                                             where wl.lifter_id = %(p_lifter)s
                                                               and wl.status = 'COMPL'
                                                               and wel.workout_log_id = wl.id
                                                               and wel.exercise_id = %(p_exercise)s
                                                               and wel.weight is not null
                                                          group by wl.workout_date
                                                          union all
                                                            select wl.workout_date,
                                                                   sum (wel.sets * wel.reps * wel.weight) y
                                                              from hamask_program p,
                                                                   hamask_workout_group wg,
                                                                   hamask_workout w,
                                                                   hamask_workout_log wl,
                                                                   hamask_workout_exercise_log wel
                                                             where p.lifter_id = %(p_lifter)s
                                                               and wg.program_id = p.id
                                                               and w.workout_group_id = wg.id
                                                               and wl.workout_id = w.id
                                                               and wl.status = 'COMPL'
                                                               and wel.workout_log_id = wl.id
                                                               and wel.exercise_id = %(p_exercise)s
                                                               and wel.weight is not null
                                                          group by wl.workout_date) s,
                                                         (select max (m.volume) volume
                                                            from (  select sum (wel.sets * wel.reps * wel.weight) volume
                                                                      from hamask_workout_log wl, hamask_workout_exercise_log wel
                                                                     where wl.lifter_id = %(p_lifter)s
                                                                       and wl.status = 'COMPL'
                                                                       and wel.workout_log_id = wl.id
                                                                       and wel.exercise_id = %(p_exercise)s
                                                                       and wel.weight is not null
                                                                  group by wl.workout_date
                                                                  union all
                                                                    select sum (wel.sets * wel.reps * wel.weight) volume
                                                                      from hamask_program p,
                                                                           hamask_workout_group wg,
                                                                           hamask_workout w,
                                                                           hamask_workout_log wl,
                                                                           hamask_workout_exercise_log wel
                                                                     where p.lifter_id = %(p_lifter)s
                                                                       and wg.program_id = p.id
                                                                       and w.workout_group_id = wg.id
                                                                       and wl.workout_id = w.id
                                                                       and wl.status = 'COMPL'
                                                                       and wel.workout_log_id = wl.id
                                                                       and wel.exercise_id = %(p_exercise)s
                                                                       and wel.weight is not null
                                                                  group by wl.workout_date) m) max_volume
                                                  where s.y is not null
                                                    and coalesce(max_volume.volume, 0) != 0
                                                  order by s.x'''
                                            , {'p_lifter': self.id, 'p_exercise': exercise.id})          
                    
                    
        return volume
        
    def get_exercise_intensity_chart(self, exercise):
        intensity = Workout_Log.objects.raw('''  select 1 id, wl.workout_date x,
                                                         round (
                                                           sum (wel.sets * wel.reps * wel.weight)
                                                           / (sum (wel.sets * wel.reps)
                                                              * (select max (max.weight)
                                                                   from (select ls.weight,
                                                                                rank () over (order by ls.entry_date desc)
                                                                                  stat_order
                                                                           from hamask_lifter_stats ls
                                                                          where ls.lifter_id = %(p_lifter)s
                                                                            and ls.exercise_id = %(p_exercise)s
                                                                            and ls.reps = 1
                                                                            and ls.entry_date <= wl.workout_date) max
                                                                  where stat_order = 1))
                                                           * 100) y
                                                    from hamask_workout_log wl, hamask_workout_exercise_log wel
                                                   where wl.lifter_id = %(p_lifter)s
                                                     and wl.status = 'COMPL'
                                                     and wel.workout_log_id = wl.id
                                                     and wel.exercise_id = %(p_exercise)s
                                                     and wel.weight is not null
                                                group by wl.workout_date
                                                union all
                                                select 1 id, wl.workout_date x, round (
                                                           sum (wel.sets * wel.reps * wel.weight)
                                                           / (sum (wel.sets * wel.reps)
                                                              * (select max (max.weight)
                                                                   from (select ls.weight,
                                                                                rank () over (order by ls.entry_date desc)
                                                                                  stat_order
                                                                           from hamask_lifter_stats ls
                                                                          where ls.lifter_id = %(p_lifter)s
                                                                            and ls.exercise_id = %(p_exercise)s
                                                                            and ls.reps = 1
                                                                            and ls.entry_date <= wl.workout_date) max
                                                                  where stat_order = 1))
                                                           * 100) y
                                                  from hamask_program p,
                                                       hamask_workout_group wg,
                                                       hamask_workout w,
                                                       hamask_workout_log wl,
                                                       hamask_workout_exercise_log wel
                                                 where p.lifter_id = %(p_lifter)s
                                                   and wg.program_id = p.id
                                                   and w.workout_group_id = wg.id
                                                   and wl.workout_id = w.id
                                                   and wl.status = 'COMPL'
                                                   and wel.workout_log_id = wl.id
                                                   and wel.exercise_id = %(p_exercise)s
                                                   and wel.weight is not null
                                                 group by wl.workout_date
                                                 order by x'''
                        , {'p_lifter': self.id, 'p_exercise': exercise.id})          
                        
        return intensity
        
    def get_stats(self):
        stats = Lifter_Stats.objects.filter(lifter__exact=self.id
                    ).order_by('-entry_date', 'exercise__name')
                    
        return stats
        
    def get_exercise_stats(self, exercise_id):
        stats = Lifter_Stats.objects.filter(lifter__exact=self.id
                    ).filter(exercise__exact=exercise_id
                    ).order_by('-entry_date', '-id')
                    
        return stats
        
    def get_all_bodyweights(self):
        weights = Lifter_Weight.objects.filter(lifter__exact=self.id
                    ).order_by('-entry_date','-id')[:50]
                    
        return weights
        
    def get_current_bodyweight(self):
        weight = self.get_all_bodyweights().first()
        
        return weight
        
    def get_bodyweight_at_date(self, date):
        weight = Lifter_Weight.objects.filter(lifter__exact=self.id
                    ).filter(entry_date__lte=date
                    ).order_by('-entry_date', '-id'
                    ).first()
        
        return weight
        
    def get_bodyweight_chart(self):
        chart = Lifter_Weight.objects.raw('''select 1 id, lw.entry_date x, avg(lw.weight) y
                                               from hamask_lifter_weight lw 
                                              where lw.lifter_id = %s
                                              group by lw.entry_date
                                              order by lw.entry_date'''
                                            , [self.id])          
                    
        return chart
        
    def get_wilks_coefficient(self, bodyweight):
        a, b, c, d, e, f = None, None, None, None, None, None
        x = bodyweight
        
        if self.sex == 'MALE':
            a = -216.0475144
            b = 16.2606339
            c = -0.002388645
            d = -0.00113732
            e = 7.01863e-06
            f = -1.291e-08
        else:
            a = 594.31747775582
            b = -27.23842536447
            c = 0.82112226871
            d = -0.00930733913
            e = 4.731582e-05
            f = -9.054e-08

        return 500 / (a + (b*x) + (c*x**2) + (d*x**3) + (e*x**4) + (f*x**5))
    
    def get_current_wilks(self):
        total, wilks = None, None
        bodyweight = self.get_weight_kilo(getattr(self.get_current_bodyweight(), 'weight', None))
        if bodyweight:
            total = self.get_weight_kilo(self.get_pl_total())
        if total:
            wilks = round(total * self.get_wilks_coefficient(bodyweight), 2)          
        
        return wilks
        
    def get_wilks(self, total, bodyweight):
        wilks = self.get_weight_kilo(total) * self.get_wilks_coefficient(self.get_weight_kilo(bodyweight))
        
        return wilks
    
    def get_wilks_chart(self):
        chart = []
        entries = Lifter_Stats.objects.raw('''select 1 id, lw.entry_date entry_date, avg(lw.weight) bodyweight
                                              from hamask_lifter_weight lw 
                                             where lw.lifter_id = %(p_lifter)s
                                             group by lw.entry_date
                                             union all
                                             select 2 id, ls.entry_date entry_date, null bodyweight 
                                             from hamask_lifter_stats ls,
                                                  hamask_exercise e                                             
                                            where ls.lifter_id = %(p_lifter)s
                                              and ls.reps = 1
                                              and e.id = ls.exercise_id
                                              and e.name in ('Squat', 'Bench Press', 'Deadlift')
                                            group by ls.entry_date
                                            order by entry_date'''
                                            , {'p_lifter': self.id})

        for entry in entries:
            if not entry.bodyweight:
                entry.bodyweight = getattr(self.get_bodyweight_at_date(entry.entry_date), 'weight', None)
            total = self.get_pl_total_at_date(entry.entry_date)
                
            if entry.bodyweight and total:
                wilks = self.get_wilks(total, entry.bodyweight)
                chart.append({'x': entry.entry_date, 'y': round(wilks, 2)})
                    
        return chart
        
    def get_weight_unit(self):
        unit = ''
        if self.measurement_system == 'METRC':
            unit = 'kg'
        elif self.measurement_system == 'IMPER':
            unit = 'lbs'
            
        return unit;
        
    def get_converted_weight_unit(self):
        unit = ''
        if self.measurement_system == 'METRC':
            unit = 'lbs'
        elif self.measurement_system == 'IMPER':
            unit = 'kg'
            
        return unit;

    def get_weight_kilo(self, weight):
        if weight:
            return weight if self.measurement_system == 'METRC' else weight / 2.2
        else:
            return None
            
    def convert_weight(self, weight):
        if weight:
            return weight * 2.2 if self.measurement_system == 'METRC' else weight / 2.2
        else:
            return None
    
class Lifter_Weight (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE)
    entry_date = models.DateField ()
    weight = models.FloatField ()
    
    def __str__(self):
        return str(self.weight) + self.lifter.get_weight_unit()
    
    @property
    def weight_formt(self):
        if not hasattr(self, '_weight_formt'):
            self._weight_formt = str(self.weight) + self.lifter.get_weight_unit()
        
        return self._weight_formt
    
class Exercise (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE, blank=True, null=True, editable=False)
    name = models.CharField (max_length=60, unique=True)
    category_choices = (
        ('MAIN', 'Main Lift'),
        ('MAIN_VARTN', 'Main Lift Variation'),
        ('COMPN_ACESR', 'Compound Accessory'),
        ('STRON', 'Strongman'),
        ('ISOLT_ACESR', 'Isolation'),
    )
    category = models.CharField (max_length=30, choices=category_choices, blank=True, null=True)
    has_stats = models.BooleanField (default=True)
    
    def __str__(self):
        return self.name
    
    @staticmethod
    def get_exercises(category, lifter_id):
        return Exercise.objects.filter(category__exact=category
                ).filter(Q(lifter__exact=lifter_id) | Q(lifter__isnull=True)
                ).order_by('name')
    
    @staticmethod
    def get_lifter_exercises(lifter):
        return Exercise.objects.filter(lifter__exact=lifter.id
                ).order_by('name')
    
    @staticmethod
    def get_exercise_select(lifter_id=None):
        # Create a 2 level list (1. Category, 2. Exercise)
        select = [['', '---------']]
        
        for category in Exercise.category_choices:
            exercise_list = []
            
            for exercise in Exercise.get_exercises(category[0], lifter_id):
                exercise_list.append([exercise.id, exercise.name])

            if exercise_list:
                select.append([category[1], exercise_list])        

        return select
    
class Program (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE)
    rep_scheme_choices = (
        ('MAX_PERCENTAGE', '% of Max'),
        ('RPE', 'RPE'),
        ('WEIGHT', 'Weight'),
    )
    rep_scheme = models.CharField (max_length=30, choices=rep_scheme_choices, blank=True, null=True)
    name = models.CharField (max_length=60)
    creation_date = models.DateField(default=timezone.now, editable=False)
    auto_update_stats = models.BooleanField (default=True)
    repeatable = models.BooleanField (default=False)
    is_public = models.BooleanField (default=False)
    rounding_choices = (
        ('NO', 'No rounding'),
        ('0.5', '0.5'),
        ('5', '5'),
        ('10', '10'),
        ('LAST_5', 'Last digit is 5'),
    )
    rounding = models.CharField (max_length=30, choices=rounding_choices, default='NO')
    training_max_percentage = models.PositiveIntegerField (blank=True, null=True)
    
    def __str__(self):
        return self.name
        
    def start_date(self):
        return self.get_current_instance().start_date if self.get_current_instance() else None    

    def end_date(self):
        return self.get_current_instance().end_date if self.get_current_instance() else None
    
    def start(self):
        current_instance = self.get_current_instance()
        if current_instance:
            current_instance.end()

        Program_Instance.start(self)
        
    def end(self):
        current_instance = self.get_current_instance()
        if current_instance:
            current_instance.end()
        
    def restart(self):
        self.start()
        
    def get_current_instance(self):
        instance = Program_Instance.objects.filter(program__exact=self.id
                    ).order_by('-start_date').first()

        return instance
    
    def copy_program(self, lifter=None):
        if not lifter:
            lifter = self.lifter
        
        program = Program(lifter=lifter
                            ,rep_scheme=self.rep_scheme
                            ,name=self.name + ' (Copy)'
                            ,auto_update_stats=self.auto_update_stats
                            ,repeatable=self.repeatable
                            ,rounding=self.rounding)
        program.save()

        for group in self.get_workout_groups():
            group.copy_group(program)

        return program
    
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
        workouts = Workout.objects.filter(workout_group__program__exact=self.id
                    ).order_by('workout_group__order', 'order')
        return workouts
        
    def get_first_workout(self):
        workout = self.get_workouts().first()
        return workout
        
    def get_last_workout_log(self):
        logs = Workout_Log.objects.filter(workout__workout_group__program__exact=self.id
                ).filter(program_instance__exact=self.get_current_instance()
                ).order_by('-workout_date', '-id').first()
        return logs
        
    def get_last_workout_log_by_id(self):
        logs = Workout_Log.objects.filter(workout__workout_group__program__exact=self.id
                ).filter(program_instance__exact=self.get_current_instance()
                ).order_by('-id').first()
        return logs
        
    def get_next_workout(self):
        if self.start_date() and not self.end_date():
            try:
                # Get last workout done
                log = self.get_last_workout_log_by_id()
                if not log:
                    raise ObjectDoesNotExist
                
                # Get next workout according to order
                workout = Workout.objects.raw('''select * 
                                                 from hamask_workout w,
                                                      hamask_workout_group wg
                                                where w.workout_group_id = wg.id
                                                  and wg.program_id = %s
                                                  and (wg.order * 10000) + w.order > cast(%s as integer)
                                                order by wg.order, w.order'''
                                            , [self.id, (log.workout.workout_group.order * 10000) + log.workout.order])[0]            
                            
            # No last workout, get first
            except ObjectDoesNotExist:
                workout = self.get_first_workout()
                
            # Last workout of program, repeat if needed
            except IndexError:
                if self.repeatable:
                    workout = self.get_first_workout()
                else:
                    workout = None
                    
        # Program not started or ended
        else:
            workout = None
            
        return workout
        
    def get_next_workouts(self):
        if self.start_date() and not self.end_date():
            group_order = 0
            order = 0
            
            # Get last workout done
            log = self.get_last_workout_log()
            if not log:
                order = -1
            else:
                group_order = log.workout.workout_group.order
                order = log.workout.order
            
            # Get next workout according to order
            workouts = Workout.objects.raw('''select * 
                                                from hamask_workout w,
                                                     hamask_workout_group wg
                                               where w.workout_group_id = wg.id
                                                 and wg.program_id = %s
                                                 and (wg.order * 10000) + w.order > cast(%s as integer)
                                               order by wg.order, w.order'''
                                        , [self.id, (group_order * 10000) + order])  

            # Check if last workout
            try:
                workout = workouts[0]
            
            # Last workout of program, repeat if needed
            except IndexError:
                if self.repeatable:
                    workouts = self.get_workouts()
                else:    
                    workouts = None
                    
        # Program not started or ended
        else:
            workouts = None
            
        return workouts
        
    def get_workouts_count(self):
        count = Workout.objects.filter(workout_group__program__exact=self.id).count()
        return count
    
    def get_intensity_chart(self):
        intensity = Lifter_Stats.objects.raw('''select w.id,
                                                       row_number() over (order by ((wg.order + 1) * 10000) + w.order) x,
                                                       round(cast(avg(we.percentage) as decimal), 2) y
                                             from hamask_workout_group wg,
                                                  hamask_workout w,
                                                  hamask_workout_exercise we
                                            where wg.program_id = %s
                                              and w.workout_group_id = wg.id
                                              and we.workout_id = w.id
                                              and we.percentage is not null
                                            group by wg.order, w.id, w.order
                                            order by ((wg.order + 1) * 10000) + w.order'''
                                            , [self.id])          
                    
        return intensity
    
    def get_volume_chart(self):
        intensity = Lifter_Stats.objects.raw('''select s.id, s.x, round(cast((s.y / max_volume.volume) * 100 as decimal), 2) y
                                                  from (select w.id,
                                                               row_number() over (order by ((wg.order + 1) * 10000) + w.order) x,
                                                               sum(we.sets * we.reps * we.percentage) y
                                                          from hamask_workout_group wg,
                                                               hamask_workout w,
                                                               hamask_workout_exercise we
                                                         where wg.program_id = %s
                                                           and w.workout_group_id = wg.id
                                                           and we.workout_id = w.id
                                                           and we.percentage is not null
                                                           and we.sets is not null
                                                           and we.reps is not null
                                                         group by wg.id, wg.order, w.id, w.order
                                                         order by ((wg.order + 1) * 10000) + w.order) s,
                                                       (select max(s2.volume) volume
                                                          from (select sum(we.sets * we.reps * we.percentage) volume
                                                                  from hamask_workout_group wg,
                                                                       hamask_workout w,
                                                                       hamask_workout_exercise we
                                                                 where wg.program_id = %s
                                                                   and w.workout_group_id = wg.id
                                                                   and we.workout_id = w.id
                                                                   and we.percentage is not null
                                                                   and we.sets is not null
                                                                   and we.reps is not null
                                                                 group by we.workout_id) s2) max_volume
                                                order by s.x'''
                                            , [self.id, self.id])          
                    
        return intensity
        
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
                    if group.uses_max() and not self.lifter.get_pl_maxes().exists():
                        raise IncompleteProgram
            
        except IncompleteProgram:
            ready = False
        else:
            ready = True
        
        return ready
        
    def complete(self):
        if not self.get_next_workout():
            self.end()

    def get_public_programs():
        programs = Program.objects.filter(is_public__exact=True).order_by('name')
        return programs

class Program_Instance (models.Model):
    program = models.ForeignKey (Program, on_delete=models.CASCADE)	
    start_date = models.DateField ()
    end_date = models.DateField (blank=True, null=True)

    def end(self):
        self.end_date = timezone.now()
        self.save()

    def start(program):
        instance = Program_Instance(program=program, start_date=timezone.now())
        instance.save()

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
        
    def copy_group(self, program):
        name = ""
        
        # Create new group
        if not program:
            program = self.program
        else:
            name = self.name
            
        order = program.get_next_workout_group_order()
        name = 'Block ' + str(order + 1) if not name else name
        group = Workout_Group(program=program, name=name, order=order)
        group.save()
        
        # Copy workouts
        for workout in self.get_workouts():
            workout.copy_workout(group)
        
        
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
        
    def copy_workout(self, group):
        name = ""
        
        # Create new workout
        if not group:
            group = self.workout_group
        else:
            name = self.name
        
        order = group.get_next_workout_order()
        name = 'Day ' + str(order + 1) if not name else name
        workout = Workout(workout_group=group
                            , name=name
                            , order=order
                            , day_of_week=self.day_of_week)
        workout.save()
        
        # Copy exercises
        for exercise in self.get_workout_exercises():
            exercise_copy = Workout_Exercise(workout=workout
                                            ,exercise=exercise.exercise
                                            ,rep_scheme=exercise.rep_scheme
                                            ,order=exercise.order
                                            ,sets=exercise.sets
                                            ,reps=exercise.reps
                                            ,weight=exercise.weight
                                            ,percentage=exercise.percentage
                                            ,rpe=exercise.rpe
                                            ,time=exercise.time
                                            ,is_amrap=exercise.is_amrap
                                            ,notes=exercise.notes)
            exercise_copy.save()
        
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
        
    def get_average_intensity(self):
        intensity = Workout_Exercise.objects.filter(workout__exact=self.id
                        ).filter(percentage__isnull=False
                        ).aggregate(intensity=Avg('percentage'))
        return intensity
    
    def log(self, status):
        # Create new log
        program_instance = self.workout_group.program.get_current_instance()
        log = Workout_Log(workout=self
                , program_instance=program_instance
                , workout_date=timezone.now()
                , status=status)  
        log.save()
        
        # Log exercises
        exercises = self.get_workout_exercises()
        for exercise in exercises:
            exercise.log(log)
            
        # Check if program is completed
        self.workout_group.program.complete()
        
        return log
        
    def full_name(self):
        full_name = self.name
        if self.day_of_week:
            full_name += ' - ' + self.get_day_of_week_display()
            
        return full_name
        
    def expected_date(self):
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
    weight = models.FloatField (blank=True, null=True)
    percentage = models.FloatField (blank=True, null=True)
    rpe = models.FloatField (blank=True, null=True)
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
                    self._loading = 'RPE ' + (str(self.rpe)[:-2] if str(self.rpe)[-2:] == '.0' else str(self.rpe))
                else:
                    self._loading = ''
            elif self.rep_scheme == 'WEIGHT':
                if self.weight is not None:
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
                        weight = max.weight * (program.training_max_percentage / 100) * (self.percentage / 100) if program.training_max_percentage else max.weight * (self.percentage / 100)
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
            elif self.rep_scheme == 'WEIGHT':
                self._loading_weight = self.weight
                
        return self._loading_weight
        
    @property
    def loading_weight_formt(self):
        if not hasattr(self, '_loading_weight_formt'):
            if self.loading_weight and self.rep_scheme != 'WEIGHT':
                self._loading_weight_formt = str(self.loading_weight
                    ) + self.workout.workout_group.program.lifter.get_weight_unit()
            elif self.rep_scheme == 'MAX_PERCENTAGE':
                self._loading_weight_formt = 'No max defined'
            else:
                self._loading_weight_formt = ''
        
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
        
    def notes_formt(self):
        notes = ''
        
        if self.notes:
            if len(self.notes) > 10:
                notes = self.notes[:7] + '...'
            else:
                notes = self.notes
                
        return notes
    
class Workout_Log (models.Model):
    workout = models.ForeignKey (Workout, on_delete=models.SET_NULL, blank=True, null=True)
    program_instance = models.ForeignKey (Program_Instance, on_delete=models.SET_NULL, blank=True, null=True)
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE, blank=True, null=True)
    workout_date = models.DateField (default=datetime.date.today)
    status_choices = (
        ('COMPL', 'Completed'),
        ('SKIPD', 'Skipped'),
    )
    status = models.CharField (max_length=30, choices=status_choices)
    notes = models.TextField (blank=True, null=True)
    
    def get_exercise_log(self):
        exercise_log = Workout_Exercise_Log.objects.filter(workout_log__exact=self.id
                        ).order_by('order')
                        
        return exercise_log
    
    def get_exercise_log_formt(self):
        exercise_log = self.get_exercise_log()
        list_formt = ', '.join(list(exercise_log.order_by('exercise__name'
                        ).values_list('exercise__name', flat=True
                        ).distinct('exercise__name')))
        
        return list_formt
        
    def get_next_exercise_order(self):
        exercises = self.get_exercise_log()
        
        if exercises.exists():
            order = exercises.aggregate(max_order=Max('order'))['max_order'] + 1
        else:
            order = 0
        
        return order
        
    def get_lifter(self):
        if self.lifter:
            lifter = self.lifter
        elif self.workout:
            lifter = self.workout.workout_group.program.lifter
        else:
            lifter = None
        
        return lifter
    
class Workout_Exercise_Log (models.Model):
    workout_log = models.ForeignKey (Workout_Log, on_delete=models.CASCADE)
    workout_exercise = models.ForeignKey (Workout_Exercise, on_delete=models.SET_NULL, blank=True, null=True)    
    exercise = models.ForeignKey (Exercise, on_delete=models.PROTECT)
    order = models.PositiveIntegerField ()
    sets = models.PositiveIntegerField (blank=True, null=True)
    reps = models.PositiveIntegerField (blank=True, null=True)
    weight = models.FloatField (blank=True, null=True)
    percentage = models.FloatField (blank=True, null=True)
    rpe = models.FloatField (blank=True, null=True)
    time = models.PositiveIntegerField (blank=True, null=True)
    is_amrap = models.BooleanField (default=False)
    notes = models.TextField (blank=True, null=True)
    
    def save(self, *args, **kwargs):        
        # Call the "real" save() method
        super(Workout_Exercise_Log, self).save(*args, **kwargs)
        
        # Log PR if applicable
        if self.weight and self.workout_exercise and self.exercise.has_stats and self.workout_log.status == 'COMPL':
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
                if (pr and self.weight > pr.weight) or not pr:
                    stat = Lifter_Stats(lifter=program.lifter
                            ,exercise=self.exercise
                            ,workout_exercise_log=self
                            ,reps=self.reps
                            ,weight=self.weight)
                            
                    stat.save()
                        
    def delete(self, *args, **kwargs):
        # Reorder exercise logs
        next_logs = Workout_Exercise_Log.objects.filter(workout_log__exact=self.workout_log.id
                        ).filter(order__gt=self.order)
                            
        for log in next_logs:
            log.order -= 1
            log.save()
        
        # Call the "real" delete() method
        super(Workout_Exercise_Log, self).delete(*args, **kwargs)
    
    def set_order_up(self):
        previous = Workout_Exercise_Log.objects.filter(workout_log__exact=self.workout_log.id
                    ).filter(order__exact=self.order - 1
                    ).get()
                    
        previous.order += 1
        self.order -= 1
        previous.save()
        self.save()
        
    def set_order_down(self):
        next = Workout_Exercise_Log.objects.filter(workout_log__exact=self.workout_log.id
                    ).filter(order__exact=self.order + 1
                    ).get()
                  
        next.order -= 1
        self.order += 1
        next.save()
        self.save()
        
    @property
    def loading(self):
        if not hasattr(self, '_loading'):
            if self.rpe: 
                self._loading = 'RPE ' + (str(self.rpe)[:-2] if str(self.rpe)[-2:] == '.0' else str(self.rpe))
            elif self.percentage:
                self._loading = str(self.percentage) + '%'
            else:
                self._loading = ''
        
        return self._loading
    
    @property
    def weight_formt(self):
        if not hasattr(self, '_weight_formt'):
            if self.weight:
                self._weight_formt = str(self.weight
                    ) + self.workout_log.get_lifter().get_weight_unit()
            else:
                self._weight_formt = ''
        
        return self._weight_formt
        
    @property
    def volume(self):
        if not hasattr(self, '_volume'):
            if self.weight:
                self._volume = str(self.sets * self.reps * self.weight
                    ) + self.workout_log.get_lifter().get_weight_unit()
            else:
                self._volume = ''
        
        return self._volume
        
    def notes_formt(self):
        notes = ''
        
        if self.notes:
            if len(self.notes) > 10:
                notes = self.notes[:7] + '...'
            else:
                notes = self.notes
                
        return notes
    
class Lifter_Stats (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE)
    exercise = models.ForeignKey (Exercise, on_delete=models.PROTECT)
    workout_exercise_log = models.ForeignKey (Workout_Exercise_Log, on_delete=models.SET_NULL, blank=True, null=True)
    entry_date = models.DateField (default=datetime.date.today)
    reps = models.PositiveIntegerField (blank=True, null=True)
    weight = models.FloatField (blank=True, null=True)
    time = models.PositiveIntegerField (blank=True, null=True)
    
    def __str__(self):
        return str(self.weight)
        
class Meet_Planner (models.Model):
    lifter = models.ForeignKey (Lifter, on_delete=models.CASCADE)
    bodyweight = models.FloatField (blank=True, null=True)
    squat_1 = models.FloatField (blank=True, null=True)
    squat_2 = models.FloatField (blank=True, null=True)
    squat_3 = models.FloatField (blank=True, null=True)
    bench_1 = models.FloatField (blank=True, null=True)
    bench_2 = models.FloatField (blank=True, null=True)
    bench_3 = models.FloatField (blank=True, null=True)
    deadlift_1 = models.FloatField (blank=True, null=True)
    deadlift_2 = models.FloatField (blank=True, null=True)
    deadlift_3 = models.FloatField (blank=True, null=True)
    
    attempt_1_factor = 0.91
    attempt_2_factor = 0.97
    attempt_3_factor = 1.03
    
    def total(self):
        return getattr(self, 'squat_3', 0) + getattr(self, 'bench_3', 0) + getattr(self, 'deadlift_3', 0)
        
    def wilks(self):
        wilks = None
        total = self.total()
        
        if total and self.bodyweight:
            wilks = round(self.lifter.get_weight_kilo(total) * self.lifter.get_wilks_coefficient(self.lifter.get_weight_kilo(self.bodyweight)), 2) 
        
        return wilks
        
    def get_converted_data(self):
        data = {}        
        
        data['bodyweight'] = round(self.lifter.convert_weight(self.bodyweight))
        data['squat_1'] = round(self.lifter.convert_weight(self.squat_1))
        data['squat_2'] = round(self.lifter.convert_weight(self.squat_2))
        data['squat_3'] = round(self.lifter.convert_weight(self.squat_3))
        data['bench_1'] = round(self.lifter.convert_weight(self.bench_1))
        data['bench_2'] = round(self.lifter.convert_weight(self.bench_2))
        data['bench_3'] = round(self.lifter.convert_weight(self.bench_3))
        data['deadlift_1'] = round(self.lifter.convert_weight(self.deadlift_1))
        data['deadlift_2'] = round(self.lifter.convert_weight(self.deadlift_2))
        data['deadlift_3'] = round(self.lifter.convert_weight(self.deadlift_3))
        data['total'] = round(self.lifter.convert_weight(self.total()))
        
        return data
        
    def get_converted_data_with_unit(self):
        data = self.get_converted_data()        
        
        for k in data:
            data[k] = str(data[k]) + ' ' + self.lifter.get_converted_weight_unit()
        
        return data
        
    @staticmethod
    def clear_meet_planner(lifter):
        meet_planner = Meet_Planner.objects.filter(lifter__exact=lifter)
        
        if meet_planner:
            meet_planner.delete()
            
    @staticmethod
    def initialize_meet_planner(lifter):
        meet_planner = Meet_Planner(lifter=lifter, bodyweight=lifter.get_current_bodyweight().weight)
                        
        squat_max = lifter.get_max(Exercise.objects.get(name__exact='Squat'))
        bench_max = lifter.get_max(Exercise.objects.get(name__exact='Bench Press'))
        deadlift_max = lifter.get_max(Exercise.objects.get(name__exact='Deadlift'))
        
        if squat_max:
            meet_planner.squat_1 = round(squat_max.weight * Meet_Planner.attempt_1_factor)
            meet_planner.squat_2 = round(squat_max.weight * Meet_Planner.attempt_2_factor)
            meet_planner.squat_3 = round(squat_max.weight * Meet_Planner.attempt_3_factor)
        
        if bench_max:
            meet_planner.bench_1 = round(bench_max.weight * Meet_Planner.attempt_1_factor)
            meet_planner.bench_2 = round(bench_max.weight * Meet_Planner.attempt_2_factor)
            meet_planner.bench_3 = round(bench_max.weight * Meet_Planner.attempt_3_factor)
        
        if deadlift_max:
            meet_planner.deadlift_1 = round(deadlift_max.weight * Meet_Planner.attempt_1_factor)
            meet_planner.deadlift_2 = round(deadlift_max.weight * Meet_Planner.attempt_2_factor)
            meet_planner.deadlift_3 = round(deadlift_max.weight * Meet_Planner.attempt_3_factor)
            
        meet_planner.save()
        return meet_planner
    
