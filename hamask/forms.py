import datetime

from django import forms

from .models import Exercise

class LoginForm (forms.Form):
    email = forms.EmailField (label='Email', max_length=254)
    password = forms.CharField (widget=forms.PasswordInput)
    
class StatForm (forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    exercise = forms.ModelChoiceField (queryset=Exercise.objects.all()
                , empty_label='- Choose -')
    entry_date = forms.DateField (initial=datetime.date.today
                    , input_formats=['%Y-%m-%d'])
    weight = forms.IntegerField (min_value=1)
    reps = forms.IntegerField (min_value=1)