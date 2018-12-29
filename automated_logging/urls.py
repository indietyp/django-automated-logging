from . import views
from django.conf.urls import url

urlpatterns = [
    url(r'^$', views.request_testcase),
    url(r'^500$', views.exception_testcase),
]
