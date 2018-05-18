======================================================
Enhydris-synoptic - Display current weather conditions
======================================================

.. image:: https://travis-ci.org/openmeteo/enhydris-synoptic.svg?branch=master
    :alt: Build button
    :target: https://travis-ci.org/openmeteo/enhydris-synoptic

.. image:: https://codecov.io/github/openmeteo/enhydris-synoptic/coverage.svg?branch=master
    :alt: Coverage
    :target: https://codecov.io/gh/openmeteo/enhydris-synoptic

Enhydris-synoptic is an app that adds a page to Enhydris that shows
current conditions in several stations.

Note that it does not check permissions; any synoptic view created
will be public, regardless of whether the timeseries from which it is
derived are marked top secret.

Enhydris-synoptic is free software, available under the GNU Affero
General Public License.

**Installing and configuring**

- Install Enhydris 2 or later

- Make sure ``enhydris_synoptic`` is in the PYTHONPATH, or link to it from the
  top-level directory of Enhydris.

- In the Enhydris ``enhydris/settings/local.py`` file, add
  ``enhydris_synoptic`` to ``INSTALLED_APPS``, and set
  ``ENHYDRIS_SYNOPTIC_ROOT`` and ``ENHYDRIS_SYNOPTIC_URL``.

  Enhydris-synoptic works by creating static files which are then served
  by the web server. ``ENHYDRIS_SYNOPTIC_ROOT`` indicates where these
  files shall be stored. ``ENHYDRIS_SYNOPTIC_URL`` is currently not used
  anywhere, but it's better to set it anyway; later versions might start
  to use it without warning.

- In the Enhydris configuration directory, execute ``python manage.py
  migrate``.

- Run ``celery`` and ``celerybeat``, and configure ``celerybeat`` to
  execute the ``enhydris_synoptic.tasks.create_static_files`` task once
  in a while.

- Configure your web server to serve ``ENHYDRIS_SYNOPTIC_ROOT`` at
  ``ENHYDRIS_SYNOPTIC_URL``.

- Go to the admin and setup a view.

After celery executes, the report will be available at
``ENHYDRIS_SYNOPTIC_URL + slug + '/'``, where ``slug`` is the URL identifier
given to the synoptic view.
