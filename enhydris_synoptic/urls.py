from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<slug>[^/]+)/$', views.SynopticView.as_view(),
        name='synoptic_view'),
]
