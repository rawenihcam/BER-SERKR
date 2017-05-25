
class Message ():
    def __init__(self, message = '', message_type = ''):
        self.message = message
        self.message_type = message_type
        
        if self.message_type == 'S':
            self.message_class = 'alert-success'
        elif self.message_type == 'E':
            self.message_class = 'alert-danger'
        elif self.message_type == 'W':
            self.message_class = 'alert-warning'
        else:
            self.message_class = 'alert-info'
            
    def __str__(self):
        return self.message