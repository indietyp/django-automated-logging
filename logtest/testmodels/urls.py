from . import views
from django.conf.urls import url

urlpatterns = [
    url(r'^$', views.save_test),
    url(r'^d/$', views.save_test),
]
