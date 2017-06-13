from django.conf.urls import url

from . import views

app_name = 'hamask'
urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^login/', views.index, name='index'),
	url(r'^programs/program/workout/(?P<pk>[0-9]+)', views.workout_update, name='workout_update'),
    url(r'^ajax/reorder_exercise/', views.reorder_exercise, name='reorder_exercise'),
    url(r'^ajax/delete_exercise/', views.delete_exercise, name='delete_exercise'),
    url(r'^ajax/reorder_group/', views.reorder_group, name='reorder_group'),
	url(r'^ajax/delete_group/', views.delete_group, name='delete_group'),
	url(r'^programs/program/(?P<pk>[0-9]+)', views.program_update, name='program_update'),
	url(r'^programs/program/', views.program_create, name='program_create'),
	url(r'^programs/', views.programs, name='programs'),
	url(r'^logs/', views.logs, name='logs'),
	url(r'^stats/stat/(?P<pk>[0-9]+)', views.stat_update, name='stat_update'),
	url(r'^stats/stat/', views.stat_create, name='stat_create'),
	url(r'^stats/', views.stats, name='stats'),
]