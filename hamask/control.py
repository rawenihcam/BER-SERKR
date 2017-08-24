from django.template.defaulttags import register
from django.db.models import *

# Custom classes
class Notification():
    success_class = 'alert-success'
    error_class = 'alert-danger'
    warning_class = 'alert-warning'
    info_class = 'alert-info'
    
    success_message = 'All changes saved.'
    
class IncompleteProgram(Exception):
    pass
    
class Custom():
    # Custom functions    
    @register.filter
    def get_item(dictionary, key):
        return dictionary.get(key)
        
    # Chartist
    
    # "x" (date) and "y" (number) field required. Return JS object ready for eval()
    def get_chartist_data(query):
        values_list = query
        data = '['
        
        if values_list:
            for value in values_list:
                data += '{x: new Date("' + str(value.x) + '"), y:' + str(value.y) + '},'
            
            data = data[:-1] + ']'
        else:
            data = []
            
        return data