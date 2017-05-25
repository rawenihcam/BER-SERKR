from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.urls import reverse
from django.views import generic

from .forms import *
from .models import Lifter, Lifter_Stats
from .control import *



# Create your views here.
def index(request):
    if request.method == 'POST':
        form = LoginForm (request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']            
            user = authenticate (request, username=email, password=password)
            
            if user is not None:
                login (request, user)
                request.session['lifter'] = Lifter.objects.get(email=email).id
            
            return HttpResponseRedirect (reverse ('hamask:index'))
    else:
        # If user is not authenticated, show login form
        if not request.user.is_authenticated:
            form = LoginForm()
            return render (request, 'hamask/login.html', {'form': form})
        else:
            return render (request, 'hamask/index.html')
            
def programs(request):
    return render (request, 'hamask/programs.html')
    
def logs(request):
    return render (request, 'hamask/logs.html')
    
def stats(request):            
    maxes = Lifter.objects.get(pk=request.session['lifter']).get_maxes()
    return render (request, 'hamask/stats.html', {'maxes': maxes})
    
def stat(request):
    success_message = Message ('All changes saved.', 'S')
    if request.method == 'POST':
        if 'save' in request.POST or 'saveadd' in request.POST:
            form = StatForm (request.POST)
            
            if form.is_valid():
                """stat = Lifter_Stats (lifter=Lifter.objects.get(pk=request.session['lifter'])
                        , exercise=Exercise.objects.get(pk=request.POST['exercise'])
                        , entry_date=request.POST['entry_date']
                        , weight=request.POST['weight']
                        , reps=form.cleaned_data['reps'])"""
                form.save()
                        
                """stat.save()"""
                
                if 'saveadd' in request.POST:
                    form = StatForm()
                    return HttpResponseRedirect (reverse ('hamask:stat'), {'form': form})
                else:
                    print (success_message)
                    return HttpResponseRedirect (reverse ('hamask:stats'), {'messages': 'FUCK YOU'})
            else:
                return render (request, 'hamask/stat.html', {'form': form})
    else:
        form = StatForm()
        return render (request, 'hamask/stat.html', {'form': form})