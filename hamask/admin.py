from django.contrib import admin

# Register your models here.
from .models import Exercise, Lifter, Rep_Scheme

class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'has_stats')
    ordering = ['name']
    
class LifterAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    ordering = ['first_name', 'last_name']

admin.site.register (Exercise, ExerciseAdmin)
admin.site.register (Lifter, LifterAdmin)
admin.site.register (Rep_Scheme)
