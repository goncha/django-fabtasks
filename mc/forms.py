__author__ = 'Administrator'
from django.forms import  ModelForm
from mc.models import YigoEnv

class YigoEnvForm(ModelForm):
    class Meta():
        model=YigoEnv
