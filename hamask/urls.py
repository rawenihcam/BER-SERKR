from django.conf.urls import url

from . import views

app_name = 'hamask'
urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^index/', views.index, name='index'),
	url(r'^login/', views.index, name='index'),
	url(r'^logout/', views.logout_view, name='logout'),
	url(r'^programs/program/workout/(?P<pk>[0-9]+)', views.workout_update, name='workout_update'),
    url(r'^ajax/reorder_exercise/', views.reorder_exercise, name='reorder_exercise'),
    url(r'^ajax/delete_exercise/', views.delete_exercise, name='delete_exercise'),
    url(r'^ajax/update_workout_notes/', views.update_workout_notes, name='update_workout_notes'),
    url(r'^ajax/reorder_group/', views.reorder_group, name='reorder_group'),
	url(r'^ajax/delete_group/', views.delete_group, name='delete_group'),
	url(r'^ajax/update_group/', views.update_group, name='update_group'),
	url(r'^programs/program/(?P<pk>[0-9]+)', views.program_update, name='program_update'),
	url(r'^programs/program/', views.program_create, name='program_create'),
	url(r'^programs/', views.programs, name='programs'),    
    url(r'^ajax/reorder_exercise_log/', views.reorder_exercise_log, name='reorder_exercise_log'),
    url(r'^ajax/delete_exercise_log/', views.delete_exercise_log, name='delete_exercise_log'),
    url(r'^ajax/update_log_notes/', views.update_log_notes, name='update_log_notes'),
	url(r'^logs/log/(?P<pk>[0-9]+)', views.log_update, name='log_update'),
	url(r'^logs/', views.logs, name='logs'),
	url(r'^logs_by_exercise/(?P<exercise>[0-9]+)', views.logs_by_exercise, name='logs_by_exercise'),
	url(r'^logs_by_exercise/', views.logs_by_exercise, name='logs_by_exercise'),
	url(r'^next_workouts/', views.next_workouts, name='next_workouts'),
	url(r'^stats/stat/(?P<pk>[0-9]+)', views.stat_update, name='stat_update'),
	url(r'^stats/stat/', views.stat_create, name='stat_create'),
	url(r'^stats/', views.stats, name='stats'),
	url(r'^max_progression/', views.max_progression, name='max_progression'),
	url(r'^profile/', views.profile, name='profile'),
	url(r'^bodyweight/(?P<pk>[0-9]+)', views.bodyweight_update, name='bodyweight_update'),
	url(r'^bodyweight/', views.bodyweight, name='bodyweight'),
]