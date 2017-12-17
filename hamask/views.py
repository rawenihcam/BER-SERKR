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
                email = request.POST['email'].lower()
                password = request.POST['password']            
                user = authenticate (request, username=email, password=password)
                
                if user is not None:
                    login (request, user)
                    request.session['lifter'] = Lifter.objects.get(email__exact=email).id
                
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
            elif 'restart' in request.POST:
                program.restart()
                messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
                return HttpResponseRedirect (reverse ('hamask:program_update', kwargs={'pk':program.id}))
            elif 'copy' in request.POST:
                new_program = program.copy_program()
                messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
                return HttpResponseRedirect (reverse ('hamask:program_update', kwargs={'pk':new_program.id}))
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

def program_import(request):            
    lifter = Lifter.objects.get(pk=request.session['lifter'])    
    
    form = ProgramImportForm(request.POST or None)

    if form.is_valid():
        program = Program.objects.get(pk=form.cleaned_data['program'])
        copy = program.copy_program(lifter)
        copy.save()
            
        messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
        return HttpResponseRedirect (reverse ('hamask:programs'))
    else:
        return render (request, 'hamask/program_import.html', {'form': form})
    
def workout_update(request, pk, template_name='hamask/workout.html'):
    workout = get_object_or_404(Workout, pk=pk)
    lifter_id = request.session['lifter']
    
    if workout.workout_group.program.lifter.id != lifter_id:
         raise Http404("Invalid workout.")
    
    # Build forms
    form = WorkoutForm(request.POST or None, instance=workout, prefix='workout')
    ExerciseFormset = modelformset_factory(Workout_Exercise, form=WorkoutExerciseForm, can_delete=True)
    exercise_formset = ExerciseFormset(request.POST or None
                        , prefix='exercise'
                        , queryset=workout.get_workout_exercises()
                        , form_kwargs={'lifter': lifter_id})
    
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
                
                # Manage order
                if exercise.order == None:
                    exercise.order = workout.get_next_exercise_order()
                    
                exercise.save()
                
            # Delete
            #for exercise in exercise_formset.deleted_objects:
                #exercise.delete()
            
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
    
def update_workout_notes(request):
    exercise = Workout_Exercise.objects.get(pk=request.GET.get('workout_exercise_id', None))
    exercise.notes = request.GET.get('notes', None)
    exercise.save()    
    
    return JsonResponse({'notes_formt': exercise.notes_formt()})

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
    lifter_id = request.session['lifter']
    log = get_object_or_404(Workout_Log, pk=pk)
    if log.get_lifter().id != lifter_id:
        raise Http404("Invalid log.")
    
    # Build forms
    form = WorkoutLogForm(request.POST or None, instance=log, prefix='log')
    ExerciseFormset = modelformset_factory(Workout_Exercise_Log, form=WorkoutExerciseLogForm, can_delete=True)
    exercise_formset = ExerciseFormset(request.POST or None
                        , prefix='exercise_log'
                        , queryset=log.get_exercise_log()
                        , form_kwargs={'lifter': lifter_id})
    
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
    
def update_log_notes(request):
    exercise_log = Workout_Exercise_Log.objects.get(pk=request.GET.get('workout_exercise_log_id', None))
    exercise_log.notes = request.GET.get('notes', None)
    exercise_log.save()    
    
    return JsonResponse({'notes_formt': exercise_log.notes_formt()})
    
def logs_by_exercise(request, exercise='0'):
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    form = LogByExerciseForm(request.POST or None, lifter = lifter.id)
    
    if request.POST:
        # Create
        if 'create_log' in request.POST:
            log = Workout_Log(lifter=lifter, status='COMPL')
            log.save()
            
            return HttpResponseRedirect (reverse ('hamask:log_update', kwargs={'pk':log.id}))
        
        # Search
        else:
            form = LogByExerciseForm(request.POST, lifter = lifter.id)
            
            if form.is_valid():
                exercise = form.cleaned_data['exercise']
                return HttpResponseRedirect (reverse ('hamask:logs_by_exercise', kwargs={'exercise':exercise}))
            else:
                return HttpResponseRedirect (reverse ('hamask:logs_by_exercise'))
    else:    
        if exercise != '0':
            form = LogByExerciseForm(initial={'exercise': exercise}, lifter = lifter.id)
            logs = lifter.get_exercise_logs(exercise=exercise)
        else:
            form = LogByExerciseForm(lifter = lifter.id)
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
    maxes = lifter.get_pl_maxes()
    prs = lifter.get_last_prs()
    stats = lifter.get_stats()
    return render (request, 'hamask/stats.html', {'maxes': maxes, 'prs': prs, 'stats': stats,})
    
def stat_create(request, template_name='hamask/stat.html'):
    lifter_id = request.session['lifter']
    form = StatForm(request.POST or None
            , lifter = lifter_id)
        
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
    lifter_id = request.session['lifter']
    lifter_stat = get_object_or_404(Lifter_Stats, pk=pk)
    
    if lifter_stat.lifter.id != lifter_id:
         raise Http404("Invalid stat.")
    
    form = StatForm(request.POST or None
            , instance=lifter_stat
            , lifter = lifter_id)
    
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
            
def max_progression(request):            
    lifter = Lifter.objects.get(pk=request.session['lifter'])    
    
    exercises = Exercise.get_exercises('MAIN', lifter)
    data = '['
    
    for exercise in exercises:
        query = lifter.get_maxes_chart(exercise)
        data += Custom.get_chartist_data(exercise.name, query) + ','
        
    data = data[:-1] + ']'
    return render (request, 'hamask/max_progression.html', {'data': data})
            
def work_intensity(request, pk=None):            
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    exercise = None

    if pk:
        exercise = get_object_or_404(Exercise, pk=pk)    
    
    if exercise:
        form = WorkIntensityForm(request.POST or None, lifter = lifter.id, exercise = exercise.id)
    else:
        form = WorkIntensityForm(request.POST or None, lifter = lifter.id, exercise = '')

    if request.POST:
        if form.is_valid():
            exercise = form.cleaned_data['exercise']
            
            if exercise == '0':
                return HttpResponseRedirect (reverse ('hamask:work_intensity'))

            return HttpResponseRedirect (reverse ('hamask:work_intensity', kwargs={'pk': exercise}))                
    else:
        data = ''
        if exercise:
            # Intensity
            data = '['
            
            query = lifter.get_exercise_intensity_chart(exercise)
            data += Custom.get_chartist_data('Intensity', query) + ','
                
            data = data[:-1] + ', '
            print(data)
            # Volume
            query = lifter.get_exercise_volume_chart(exercise)
            data += Custom.get_chartist_data('Volume', query) + ','
                
            data = data[:-1] + ']'
            print(data)
        return render (request, 'hamask/work_intensity.html', {'form': form, 'data': data})
            
def program_intensity(request, pk=None):            
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    program = None

    if pk:
        program = get_object_or_404(Program, pk=pk)

        if program.lifter != lifter:
         raise Http404("Invalid program.")
    
    
    if program:
        form = ProgramIntensityForm(request.POST or None, lifter = lifter.id, program = program.id)
    else:
        form = ProgramIntensityForm(request.POST or None, lifter = lifter.id, program = '')

    if request.POST:
        if form.is_valid():
            program = form.cleaned_data['program']
            
            if program == '0':
                return HttpResponseRedirect (reverse ('hamask:program_intensity'))

            return HttpResponseRedirect (reverse ('hamask:program_intensity', kwargs={'pk':program}))                
    else:
        data = ''
        if program:
            # Intensity
            data = '['
            
            query = program.get_intensity_chart()
            data += Custom.get_chartist_data_number('Intensity', query) + ','
                
            data = data[:-1] + ', '

            # Volume
            query = program.get_volume_chart()
            data += Custom.get_chartist_data_number('Volume', query) + ','
                
            data = data[:-1] + ']'

        return render (request, 'hamask/program_intensity.html', {'form': form, 'data': data})
            
def profile(request):
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    
    form = ProfileForm(request.POST or None, instance=lifter, prefix='lifter')
    password_form = ChangePasswordForm(request.POST or None, prefix='password')
    
    if 'save' in request.POST:
        if form.is_valid():
            form.save()
            
            messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
            return HttpResponseRedirect (reverse ('hamask:profile'))
    elif 'change_password' in request.POST:
        if password_form.is_valid():
            password = password_form.cleaned_data['password']
            confirm = password_form.cleaned_data['confirm_password']
            
            if password and confirm:
                if password == confirm:
                    user = User.objects.get(username=lifter.email)
                    user.set_password(password)
                    user.save()
                    
                    login (request, user)
                    request.session['lifter'] = lifter.id
            
                    messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
                else:
                    messages.error(request, 'Password and confirmation must match.', extra_tags=Notification.error_class)
            else:
                messages.error(request, 'Password and confirmation are required.', extra_tags=Notification.error_class)

            return HttpResponseRedirect (reverse ('hamask:profile'))                
    else:
        return render (request, 'hamask/profile.html', {'form': form, 'password_form': password_form})
        
def bodyweight(request):
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    logs = lifter.get_all_bodyweights()
    
    form = BodyweightForm(request.POST or None, prefix='bodyweight')
    
    if form.is_valid():
        bodyweight = form.save(commit=False)
        bodyweight.lifter = lifter
        bodyweight.save()
            
        messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
        return HttpResponseRedirect (reverse ('hamask:bodyweight'))
    else:
        return render (request, 'hamask/bodyweight.html', {'form': form, 'logs': logs})
        
def bodyweight_update(request, pk, template_name='hamask/bodyweight.html'):
    lifter = Lifter.objects.get(pk=request.session['lifter'])
    bodyweight = get_object_or_404(Lifter_Weight, pk=pk)    
    if bodyweight.lifter.id != lifter.id:
        raise Http404("Invalid request.")
        
    
    logs = lifter.get_all_bodyweights()    
    form = BodyweightForm(request.POST or None, instance=bodyweight)
    
    if 'delete' in request.POST:
        bodyweight.delete()
        messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
        return HttpResponseRedirect (reverse ('hamask:bodyweight'))
    else:
        if form.is_valid():
            form.save()                    
            
            messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
            return HttpResponseRedirect (reverse ('hamask:bodyweight'))
        else:
            return render (request, template_name, {'form': form, 'logs': logs, 'id': bodyweight.id})
    
def custom_exercises(request, template_name='hamask/custom_exercises.html'):
    lifter = get_object_or_404(Lifter, pk=request.session['lifter'])
    
    # Build forms
    ExerciseFormset = modelformset_factory(Exercise, form=CustomExerciseForm, can_delete=True)
    exercise_formset = ExerciseFormset(request.POST or None, prefix='custom_exercise', queryset=Exercise.get_lifter_exercises(lifter))
    
    if exercise_formset.is_valid():
        exercise_formset.save(commit=False)
        
        # Update
        exercises_changed = dict(exercise_formset.changed_objects)
        for exercise in exercises_changed:
            exercise.save()
        
        # Create
        for exercise in exercise_formset.new_objects: 
            exercise.lifter = lifter
            exercise.save()
        
        messages.success(request, Notification.success_message, extra_tags=Notification.success_class)
        return HttpResponseRedirect (reverse ('hamask:custom_exercises'))
    else:
        return render (request, template_name, {'exercise_formset': exercise_formset})
            
def delete_custom_exercise(request):
    exercise = Exercise.objects.get(pk=request.GET.get('exercise_id', None))
    data = {'exercise_id': exercise.id}
    exercise.delete()    
    
    return JsonResponse(data)

def rm_calculator(request):            
    lifter = Lifter.objects.get(pk=request.session['lifter'])    
    
    form = RmCalculatorForm(request.POST or None)

    return render (request, 'hamask/rm_calculator.html', {'form': form})
            
def get_rm_calculator_data(request):
    data = Tools.get_rm_chart_json(int(request.GET.get('weight', None)), int(request.GET.get('reps', None)))
    
    return JsonResponse(data, safe=False)