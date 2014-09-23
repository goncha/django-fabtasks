from django.conf.urls import patterns, url
from mc import views

urlpatterns = patterns('',
    url(r'^rpc/$', views.rpc, name='rpc'),
)
