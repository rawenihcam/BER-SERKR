from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.urls import reverse
from django.views import generic

from .forms import *
from .models import Lifter, Lifter_Stats

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
    maxes = Lifter_Stats.objects.filter(lifter__exact=request.session['lifter']
            ).filter(reps__exact=1
            ).filter(exercise__name__in=['Squat', 'Bench Press', 'Deadlift']
            ).order_by('-entry_date')[:3]
    return render (request, 'hamask/stats.html', {'maxes': maxes})
    
def stat(request):
    if request.method == 'POST':
        form = StatForm (request.POST)
        
        if form.is_valid():
            stat = Lifter_Stats (lifter=Lifter.objects.get(pk=request.session['lifter'])
                    , exercise=Exercise.objects.get(pk=request.POST['exercise'])
                    , weight=request.POST['weight']
                    , reps=request.POST['reps'])
                    
            stat.save()
            
            return HttpResponseRedirect (reverse ('hamask:stats'))
    else:
        form = StatForm()
        return render (request, 'hamask/stat.html', {'form': form})