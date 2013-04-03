from google.appengine.ext import webapp
from gaeo.utils import TaiwanTimeZone

# get template register
register = webapp.template.create_template_register() 

@register.filter
def twtz(value):
    from datetime import timedelta
    return (value + timedelta(hours=8)).replace(tzinfo=TaiwanTimeZone())
