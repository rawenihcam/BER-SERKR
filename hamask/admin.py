from django.contrib import admin

# Register your models here.
from .models import Exercise, Lifter

class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'has_stats', 'lifter')
    ordering = ['name']
    
class LifterAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    ordering = ['first_name', 'last_name']

admin.site.register (Exercise, ExerciseAdmin)
admin.site.register (Lifter, LifterAdmin)
