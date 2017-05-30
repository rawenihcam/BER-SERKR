import datetime

from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from .models import Lifter_Stats, Exercise, Program

class LoginForm (forms.Form):
    email = forms.EmailField (label='Email', max_length=254)
    password = forms.CharField (widget=forms.PasswordInput)
    
class ProgramForm (ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'start_date', 'rep_scheme', 'auto_update_stats', 'rounding']
        labels = {
            'rep_scheme': _('Prefered rep scheme'),
        }
        help_texts = {
            'start_date': _('Start date will be used to plan your workouts.'),
            'rep_scheme': _('Will help you build your program, can be changed for each exercise later.'),
            'auto_update_stats': _('Uncheck this if you don''t want the system to automatically log your new PRs.'),
        }
    
class StatForm (ModelForm):
    # Redefine constructor to enforce required fields
    def __init__(self, *args, **kwargs):
        super(StatForm, self).__init__(*args, **kwargs)
        
        self.fields['weight'].required = True
        self.fields['reps'].required = True        
    
    class Meta:
        model = Lifter_Stats
        fields = ['exercise', 'entry_date', 'weight', 'reps']