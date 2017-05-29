
class Message ():
    def __init__(self, message = '', type = ''):
        self.message = message
        self.type = type
        
        if self.type == 'S':
            self.css_class = 'alert-success'
        elif self.type == 'E':
            self.css_class = 'alert-danger'
        elif self.type == 'W':
            self.css_class = 'alert-warning'
        else:
            self.css_class = 'alert-info'
            
    def __str__(self):
        return self.message