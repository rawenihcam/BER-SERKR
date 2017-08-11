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
            log = workout.log('COMPL')
        # Edit workout
        elif 'edit' in request.POST:
            workout = get_object_or_404(Workout, pk=request.POST['edit'])
            log = workout.log('COMPL')
            
            return HttpResponseRedirect (reverse ('hamask:log_update', kwargs={'pk':log.id}))
        # Skip workout
        elif 'skip' in request.POST:
            workout = get_object_or_404(Workout, pk=request.POST['skip'])
            log = workout.log('SKIPD')
            
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
            
            last_workout = lifter.get_last_workout()
            last_exercises = {}
            
            if workouts:               
                for workout in workouts:
                    exercises[workout.id] = workout.get_workout_exercises()
                    
            if last_workout:
                last_exercises[last_workout.id] = last_workout.get_exercise_log()
            
            return render (request, 'hamask/index.html', {'workouts': workouts
                                                            , 'exercises': exercises
                                                            , 'last_workout': last_workout
                                                            , 'last_exercises': last_exercises,})

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
            elif 'copy_group' in request.POST:
                group = Workout_Group.objects.get(pk=request.POST['copy_group'])
                group.copy_group(program=None)
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
    
    if request.POST:
        if 'create_log' in request.POST:
            log = Workout_Log(lifter=lifter, status='COMPL')
            log.save()
            
            return HttpResponseRedirect (reverse ('hamask:log_update', kwargs={'pk':log.id}))
    else:    
        logs = lifter.get_last_workouts()
        return render (request, 'hamask/logs.html', {'logs': logs})
    
def log_update(request, pk, template_name='hamask/log.html'):
    log = get_object_or_404(Workout_Log, pk=pk)
    if log.get_lifter().id != request.session['lifter']:
        raise Http404("Invalid log.")
    
    # Build forms
    form = WorkoutLogForm(request.POST or None, instance=log, prefix='log')
    ExerciseFormset = modelformset_factory(Workout_Exercise_Log, form=WorkoutExerciseLogForm, can_delete=True)
    exercise_formset = ExerciseFormset(request.POST or None, prefix='exercise_log', queryset=log.get_exercise_log())
    
    if 'delete' in request.POST:
        log.delete()
        messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
        return HttpResponseRedirect (reverse ('hamask:logs'))
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
                exercise.workout_log = log
                if exercise.order == None:
                    exercise.order = log.get_next_exercise_order() 
                exercise.save()
                
            # Delete
            #for exercise in exercise_formset.deleted_objects:
             #   exercise.delete()
            
            messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
            return HttpResponseRedirect (reverse ('hamask:log_update', kwargs={'pk':log.id}))
        else:
            return render (request, template_name, {'form': form
                                                   , 'exercise_formset': exercise_formset
                                                   , 'id': log.id})

def reorder_exercise_log(request):
    exercise_log = Workout_Exercise_Log.objects.get(pk=request.GET.get('exercise_log_id', None))
    order = request.GET.get('order', None)
    data = {}
    
    try:
        if order == 'UP':
            exercise_log.set_order_up()
        elif order == 'DOWN':
            exercise_log.set_order_down()
    except ObjectDoesNotExist:
        pass
    else:
        data = {'exercise_log_id': exercise_log.id}
    
    return JsonResponse(data)
    
def delete_exercise_log(request):
    exercise_log = Workout_Exercise_Log.objects.get(pk=request.GET.get('exercise_log_id', None))
    data = {'exercise_log_id': exercise_log.id}
    exercise_log.delete()    
    
    return JsonResponse(data)
    
def logs_by_exercise(request, exercise='0'):
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    form = LogByExerciseForm(request.POST or None)
    
    if request.POST:
        # Create
        if 'create_log' in request.POST:
            log = Workout_Log(lifter=lifter, status='COMPL')
            log.save()
            
            return HttpResponseRedirect (reverse ('hamask:log_update', kwargs={'pk':log.id}))
        
        # Search
        else:
            form = LogByExerciseForm(request.POST)
            
            if form.is_valid():
                exercise = form.cleaned_data['exercise']
                return HttpResponseRedirect (reverse ('hamask:logs_by_exercise', kwargs={'exercise':exercise}))
            else:
                return HttpResponseRedirect (reverse ('hamask:logs_by_exercise'))
    else:    
        if exercise != '0':
            form = LogByExerciseForm(initial={'exercise': exercise})
            logs = lifter.get_exercise_logs(exercise=exercise)
        else:
            form = LogByExerciseForm()
            logs = None
            
        return render (request, 'hamask/logs_by_exercise.html', {'form': form, 'logs': logs})
        
def next_workouts(request):
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    programs = lifter.get_started_programs()
    workouts = {}
    exercises = {}
    
    for program in programs:
        workouts[program.id] = program.get_next_workouts() 
    
        for workout in workouts[program.id]:
            exercises[workout.id] = workout.get_workout_exercises()
    
    return render (request, 'hamask/next_workouts.html', {'programs': programs
                                                            , 'workouts': workouts
                                                            , 'exercises': exercises,})
                                                   
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