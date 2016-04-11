from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<slug>[^/]+)/$', views.SynopticView.as_view(),
        name='synoptic_view'),
    url(r'^station/(?P<pk>\d+)/$', views.SynopticStationView.as_view(),
        name='synoptic_station_view'),
    url(r'^chart/(?P<pk>\d+)\.png$', views.ChartView.as_view(),
        name='synoptic_chart_view'),
]
