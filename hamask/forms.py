import datetime

from django import forms
from django.forms import ModelForm, BaseModelFormSet
from django.utils.translation import ugettext_lazy as _

from .models import *

class LoginForm (forms.Form):
    email = forms.EmailField (label='Email', max_length=254)
    password = forms.CharField (widget=forms.PasswordInput)
    
class ProgramForm (ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'auto_update_stats', 'rounding', 'repeatable']
        """labels = {
            'rep_scheme': _('Prefered rep scheme'),
        }"""
        help_texts = {
            'start_date': _('Start date will be used to plan your workouts.'),
            'rep_scheme': _('Will help you build your program, can be changed for each exercise later.'),
            'auto_update_stats': _('Uncheck this if you don''t want the system to automatically log your new PRs.'),
        }

class WorkoutForm (ModelForm):
    class Meta:
        model = Workout
        fields = ['name', 'day_of_week']
        
class WorkoutExerciseForm (ModelForm):
    class Meta:
        model = Workout_Exercise
        fields = ['id', 'exercise', 'sets', 'reps', 'rep_scheme', 'weight', 'percentage', 'rpe', 'is_amrap', 'notes']
        
    def __init__(self, *args, **kwargs):
        # Calling Django's init
        super(WorkoutExerciseForm, self).__init__(*args, **kwargs)
       
        # Custom fields
        self.fields['exercise'].choices = Exercise.get_exercise_select()
        
class WorkoutLogForm (ModelForm):
    class Meta:
        model = Workout_Log
        fields = ['workout_date']
        
class WorkoutExerciseLogForm (ModelForm):
    class Meta:
        model = Workout_Exercise_Log
        fields = ['id', 'exercise', 'sets', 'reps', 'weight', 'rpe', 'is_amrap', 'notes']
        
    def __init__(self, *args, **kwargs):
       # Calling Django's init
       super(WorkoutExerciseLogForm, self).__init__(*args, **kwargs)
       
       # Custom fields
       self.fields['exercise'].choices = Exercise.get_exercise_select()       

class LogByExerciseForm (forms.Form):
    exercise = forms.ChoiceField (label='Exercise', choices=Exercise.get_exercise_select())
       
class StatForm (ModelForm):
    # Redefine constructor to enforce required fields
    def __init__(self, *args, **kwargs):
        super(StatForm, self).__init__(*args, **kwargs)
        
        self.fields['weight'].required = True
        self.fields['reps'].required = True
        self.fields['exercise'].choices = Exercise.get_exercise_select()         
    
    class Meta:
        model = Lifter_Stats
        fields = ['exercise', 'entry_date', 'weight', 'reps']