from django.template.defaulttags import register
from django.db.models import *
from math import exp
import json

# Custom classes
class Notification():
    success_class = 'alert-success'
    error_class = 'alert-danger'
    warning_class = 'alert-warning'
    info_class = 'alert-info'
    
    success_message = 'All changes saved.'
    
class IncompleteProgram(Exception):
    pass
    
class Tools():
    def get_rm_chart_json(weight, reps):
        rm = (100 * weight / (48.8 + 53.8 * exp(-0.075 * reps))) if reps > 1 else weight #Wathan
        data = {}
        
        data['1rm'] = round(rm)
        data['2rm'] = round((rm * (48.8 + 53.8 * exp(-0.075 * 2))) / 100)
        data['3rm'] = round((rm * (48.8 + 53.8 * exp(-0.075 * 3))) / 100)
        data['4rm'] = round((rm * (48.8 + 53.8 * exp(-0.075 * 4))) / 100)
        data['5rm'] = round((rm * (48.8 + 53.8 * exp(-0.075 * 5))) / 100)
        data['6rm'] = round((rm * (48.8 + 53.8 * exp(-0.075 * 6))) / 100)
        data['7rm'] = round((rm * (48.8 + 53.8 * exp(-0.075 * 7))) / 100)
        data['8rm'] = round((rm * (48.8 + 53.8 * exp(-0.075 * 8))) / 100)
        data['9rm'] = round((rm * (48.8 + 53.8 * exp(-0.075 * 9))) / 100)
        data['10rm'] = round((rm * (48.8 + 53.8 * exp(-0.075 * 10))) / 100)

        return json.dumps(data)

class Custom():
    # Custom functions    
    @register.filter
    def get_item(dictionary, key):
        return dictionary.get(key)
        
    # Chartist
    
    # "x" (date) and "y" (number) field required. Return JS object ready for eval()
    def get_chartist_data(name, query):
        data = '{name: "' + name +'", data: ['
        exists = False
        
        for value in query:
            if not value.y:
                value.y = 'null'

            data += '{x: new Date("' + str(value.x).replace('-', '/') + '"), y:' + str(value.y) + '},'
            exists = True
        
        if exists:
            data = data[:-1] + ']}'
        else:
            data += ']}'
            
        return data
    
    # "x" (number) and "y" (number) field required. Return JS object ready for eval()
    def get_chartist_data_number(name, query):
        data = '{name: "' + name +'", data: ['
        exists = False
        
        for value in query:
            if not value.y:
                value.y = 'null'

            data += '{x: ' + str(value.x) + ', y:' + str(value.y) + '},'
            exists = True
        
        if exists:
            data = data[:-1] + ']}'
        else:
            data += ']}'
            
        return data