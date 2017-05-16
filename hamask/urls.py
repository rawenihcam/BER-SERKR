from django.conf.urls import url

from . import views

app_name = 'hamask'
urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^login/', views.index, name='index'),
]