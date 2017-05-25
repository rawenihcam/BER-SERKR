import datetime

from django import forms
from django.forms import ModelForm

from .models import Lifter_Stats, Exercise

class LoginForm (forms.Form):
    email = forms.EmailField (label='Email', max_length=254)
    password = forms.CharField (widget=forms.PasswordInput)
    
class StatForm (ModelForm):
    """id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    exercise = forms.ModelChoiceField (queryset=Exercise.objects.all()
                , empty_label='- Choose -')
    entry_date = forms.DateField (initial=datetime.date.today
                    , input_formats=['%Y-%m-%d'])
    weight = forms.IntegerField (min_value=1)
    reps = forms.IntegerField (min_value=1)"""
    
    class Meta:
        model = Lifter_Stats
        fields = ['exercise', 'entry_date', 'weight', 'reps']