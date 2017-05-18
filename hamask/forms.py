from django import forms
from material import *

class LoginForm (forms.Form):
    email = forms.EmailField (label='Email', max_length=254)
    password = forms.CharField (widget=forms.PasswordInput)
    
    layout = Layout('email', 'password')