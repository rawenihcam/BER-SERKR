from django.template.defaulttags import register

# Custom classes
class Notification():
    success_class = 'alert-success'
    error_class = 'alert-danger'
    warning_class = 'alert-warning'
    info_class = 'alert-info'
    
    success_message = 'All changes saved.'
    
class IncompleteProgram(Exception):
    pass
    
# Custom functions    
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)