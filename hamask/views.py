from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.urls import reverse
from django.views import generic

from .forms import *
from .models import Lifter, Lifter_Stats

# Message control data
success_class = 'alert-success'
error_class = 'alert-danger'
warning_class = 'alert-warning'
info_class = 'alert-info'

success_message = 'All changes saved.'

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
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    maxes = lifter.get_maxes()
    stats = lifter.get_stats()
    return render (request, 'hamask/stats.html', {'maxes': maxes, 'stats': stats,})
    
def stat(request):
    if request.method == 'POST':
        if 'save' in request.POST or 'saveadd' in request.POST:
            form = StatForm (request.POST)
            
            if form.is_valid():
                stat = form.save(commit=False)
                stat.lifter = Lifter.objects.get(pk=request.session['lifter'])
                stat.save()
                
                if 'saveadd' in request.POST:
                    form = StatForm()
                    return HttpResponseRedirect (reverse ('hamask:stat'), {'form': form})
                else:
                    messages.success(request, success_message, extra_tags=success_class)
                    return HttpResponseRedirect (reverse ('hamask:stats'))
            else:
                return render (request, 'hamask/stat.html', {'form': form})
    else:
        form = StatForm()
        return render (request, 'hamask/stat.html', {'form': form})