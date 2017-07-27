from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.urls import reverse
from django.views import generic

from .forms import *
from .models import *
from .control import *

# Create your views here.
def index(request):
    if request.method == 'POST':
        # Login
        if 'login' in request.POST:
            form = LoginForm (request.POST)
            if form.is_valid():
                email = request.POST['email']
                password = request.POST['password']            
                user = authenticate (request, username=email, password=password)
                
                if user is not None:
                    login (request, user)
                    request.session['lifter'] = Lifter.objects.get(email=email).id
                
        # Log workout
        elif 'log' in request.POST:
            workout = get_object_or_404(Workout, pk=request.POST['log'])
            workout.log('COMPL')
        # Edit workout
        elif 'edit' in request.POST:
            workout = get_object_or_404(Workout, pk=request.POST['edit'])
            workout.log('IN_PROGR')
        # Skip workout
        elif 'skip' in request.POST:
            workout = get_object_or_404(Workout, pk=request.POST['skip'])
            workout.log('SKIPD')
            
        return HttpResponseRedirect (reverse ('hamask:index'))
    else:
        # If user is not authenticated, show login form
        if not request.user.is_authenticated:
            form = LoginForm()
            return render (request, 'hamask/login.html', {'form': form})
        else:
            lifter = Lifter.objects.get(pk=request.session['lifter'])
            workouts = lifter.get_next_workouts()
            exercises = {} 
            
            if workouts:               
                for workout in workouts:
                    exercises[workout.id] = workout.get_workout_exercises()
            
            return render (request, 'hamask/index.html', {'workouts': workouts, 'exercises': exercises,})

def logout_view(request):
    logout(request)
    return HttpResponseRedirect (reverse ('hamask:index'))
            
def programs(request):
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    programs = lifter.get_programs()
    return render (request, 'hamask/programs.html', {'programs': programs})

def program_create(request, template_name='hamask/program.html'):
    form = ProgramForm(request.POST or None)
        
    if form.is_valid():
        program = form.save(commit=False)
        program.lifter = Lifter.objects.get(pk=request.session['lifter'])
        program.save()
                
        if 'save' in request.POST:
            messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
            return HttpResponseRedirect (reverse ('hamask:program_update', kwargs={'pk':program.id}))
    else:
        return render (request, template_name, {'form': form})

def program_update(request, pk, template_name='hamask/program.html'):
    program = get_object_or_404(Program, pk=pk)
    if program.lifter.id != request.session['lifter']:
         raise Http404("Invalid program.")
    
    form = ProgramForm(request.POST or None, instance=program)
    
    if 'delete' in request.POST:
        program.delete()
        messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
        return HttpResponseRedirect (reverse ('hamask:programs'))
    else:
        if form.is_valid():
            form.save()
                    
            if 'save' in request.POST:
                messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
                return HttpResponseRedirect (reverse ('hamask:program_update', kwargs={'pk':program.id}))
            elif 'add_group' in request.POST:
                order = program.get_next_workout_group_order()
                group = Workout_Group(program=program, name='Block ' + str(order + 1), order=order)
                group.save()
                
                messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
                return HttpResponseRedirect (reverse ('hamask:program_update', kwargs={'pk':program.id}))
            elif 'add_workout' in request.POST:
                group = Workout_Group.objects.get(pk=request.POST['add_workout'])
                order = group.get_next_workout_order()
                workout = Workout(workout_group=group, name='Day ' + str(order + 1), order=order)
                workout.save()
                
                return HttpResponseRedirect (reverse ('hamask:workout_update', kwargs={'pk':workout.id}))
            elif 'start' in request.POST:
                program.start()
                messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
                return HttpResponseRedirect (reverse ('hamask:program_update', kwargs={'pk':program.id}))
            elif 'end' in request.POST:
                program.end()
                messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
                return HttpResponseRedirect (reverse ('hamask:program_update', kwargs={'pk':program.id}))
        else:
            groups = program.get_workout_groups()
            workouts = {}
            exercises = {}
            for group in groups:
                workouts[group.id] = group.get_workouts()
            for k, w in workouts.items():
                for workout in w:
                    exercises[workout.id] = workout.get_workout_exercises()
            
            return render (request, template_name, {'form': form
                            , 'program': program
                            , 'groups': groups
                            , 'workouts': workouts
                            , 'exercises': exercises,})

def reorder_group(request):
    group = Workout_Group.objects.get(pk=request.GET.get('group_id', None))
    order = request.GET.get('order', None)
    data = {}
    
    try:
        if order == 'UP':
            group.set_order_up()
        elif order == 'DOWN':
            group.set_order_down()
    except ObjectDoesNotExist:
        pass
    else:
        data = {'group_id': group.id}
    
    return JsonResponse(data)

def delete_group(request):
    group = Workout_Group.objects.get(pk=request.GET.get('group_id', None))
    data = {'group_id': group.id}
    group.delete()    
    
    return JsonResponse(data)
    
def update_group(request):
    group = Workout_Group.objects.get(pk=request.GET.get('group_id', None))
    group.name = request.GET.get('group_name', None)
    group.save()
    data = {'group_id': group.id}    
    
    return JsonResponse(data)
    
def workout_update(request, pk, template_name='hamask/workout.html'):
    workout = get_object_or_404(Workout, pk=pk)
    if workout.workout_group.program.lifter.id != request.session['lifter']:
         raise Http404("Invalid workout.")
    
    # Build forms
    form = WorkoutForm(request.POST or None, instance=workout, prefix='workout')
    ExerciseFormset = modelformset_factory(Workout_Exercise, form=WorkoutExerciseForm, can_delete=True)
    exercise_formset = ExerciseFormset(request.POST or None, prefix='exercise', queryset=workout.get_workout_exercises())
    
    if 'delete' in request.POST:
        program = workout.workout_group.program
        workout.delete()
        messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
        return HttpResponseRedirect (reverse ('hamask:program_update', kwargs={'pk':program.id}))
    else:
        if form.is_valid() and exercise_formset.is_valid():
            form.save()
            
            exercise_formset.save(commit=False)
            
            # Update
            exercises_changed = dict(exercise_formset.changed_objects)
            for exercise in exercises_changed:
                exercise.save()
            
            # Create
            for exercise in exercise_formset.new_objects: 
                exercise.workout = workout
                if exercise.order == None:
                    exercise.order = workout.get_next_exercise_order() 
                exercise.save()
                
            # Delete
            #for exercise in exercise_formset.deleted_objects:
             #   exercise.delete()
            
            messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
            return HttpResponseRedirect (reverse ('hamask:workout_update', kwargs={'pk':workout.id}))
        else:
            return render (request, template_name, {'form': form
                                                   , 'exercise_formset': exercise_formset
                                                   , 'id': workout.id
                                                   , 'program_id': workout.workout_group.program.id,})

def reorder_exercise(request):
    exercise = Workout_Exercise.objects.get(pk=request.GET.get('exercise_id', None))
    order = request.GET.get('order', None)
    data = {}
    
    try:
        if order == 'UP':
            exercise.set_order_up()
        elif order == 'DOWN':
            exercise.set_order_down()
    except ObjectDoesNotExist:
        pass
    else:
        data = {'exercise_id': exercise.id}
    
    return JsonResponse(data)
    
def delete_exercise(request):
    exercise = Workout_Exercise.objects.get(pk=request.GET.get('exercise_id', None))
    data = {'exercise_id': exercise.id}
    exercise.delete()    
    
    return JsonResponse(data)

def logs(request):
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    logs = lifter.get_last_workouts()
    return render (request, 'hamask/logs.html', {'logs': logs})
    
def log_create(request):
    return render (request, 'hamask/log.html')
    
def log_update(request):
    return render (request, 'hamask/log.html')
    
def stats(request):            
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    maxes = lifter.get_maxes()
    prs = lifter.get_last_prs()
    stats = lifter.get_stats()
    return render (request, 'hamask/stats.html', {'maxes': maxes, 'prs': prs, 'stats': stats,})
    
def stat_create(request, template_name='hamask/stat.html'):
    form = StatForm(request.POST or None)
        
    if form.is_valid():
        stat = form.save(commit=False)
        stat.lifter = Lifter.objects.get(pk=request.session['lifter'])
        stat.save()
                
        if 'saveadd' in request.POST:
            messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
            return HttpResponseRedirect (reverse ('hamask:stat_create'))
        else:
            messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
            return HttpResponseRedirect (reverse ('hamask:stats'))
    else:
        return render (request, template_name, {'form': form})

def stat_update(request, pk, template_name='hamask/stat.html'):
    lifter_stat = get_object_or_404(Lifter_Stats, pk=pk)
    if lifter_stat.lifter.id != request.session['lifter']:
         raise Http404("Invalid stat.")
    
    form = StatForm(request.POST or None, instance=lifter_stat)
    
    if 'delete' in request.POST:
        lifter_stat.delete()
        messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
        return HttpResponseRedirect (reverse ('hamask:stats'))
    else:
        if form.is_valid():
            form.save()
                    
            if 'saveadd' in request.POST:
                messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
                return HttpResponseRedirect (reverse ('hamask:stat_create'))
            else:
                messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
                return HttpResponseRedirect (reverse ('hamask:stats'))
        else:
            return render (request, template_name, {'form': form, 'id': lifter_stat.id,})