Enhydris-synoptic is an app that adds a page to Enhydris that shows
current conditions in several stations.

Note that it does not check permissions; any synoptic view created
will be public, regardless of whether the timeseries from which it is
derived are marked top secret.

Enhydris-synoptic is free software, available under the GNU Affero
General Public License.

**Installing**

- ``pip install enhydris-synoptic``

- In the Enhydris ``settings.py`` file, add ``enhydris_synoptic`` to
  ``INSTALLED_APPS``. In addition, if it's not already there, add
  ``ROOT_URLCONF = 'urls'``.

- In your ``urls.py`` add a pattern for ``enhydris_synoptic``; for
  example::

    from django.conf.urls import include, url

    from enhydris.urls import urlpatterns

    from enhydris_synoptic import urls as synoptic_urls

    urlpatterns.insert(0, url(r'^synoptic/', include(synoptic_urls)))

- In the Enhydris configuration directory, execute ``python manage.py
  migrate``.

- Go to the admin and setup a view.
