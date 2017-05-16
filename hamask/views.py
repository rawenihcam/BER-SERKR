from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.urls import reverse
from django.views import generic

#from .models import Question

# Create your views here.
def index(request):
    return HttpResponse("BER-SERKR INDEX")