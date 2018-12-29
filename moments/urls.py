from django.urls import path
from django.conf.urls import url

from .import views

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    url(r'^(?P<momentID>[\w-]+)/$', views.moment),
]