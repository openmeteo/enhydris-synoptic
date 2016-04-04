from django.conf.urls import include, url

from enhydris.urls import urlpatterns

from enhydris_synoptic import urls as synoptic_urls

urlpatterns.insert(0, url(r'^synoptic/', include(synoptic_urls)))
