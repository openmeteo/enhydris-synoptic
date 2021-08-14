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

Installing
==========

- Install Enhydris 3 or later

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

Configuration reference
=======================

- ``ENHYDRIS_SYNOPTIC_ROOT``: The filesystem path where the generated
  files will be stored (see above).

- ``ENHYDRIS_SYNOPTIC_URL``: The URL where the generated
  files will be served (see above).

- ``ENHYDRIS_SYNOPTIC_STATION_LINK_TARGET``: In the rectangles shown on
  the map, the station name is a link. This is the link target. The
  default is ``station/{station.id}/`` (the code will use ``.format()``
  to replace ``{station.id}`` with the station id).  This default link
  target leads to a page created by enhydris-synoptic that has a short
  report about the station, and charts for the last 24 hours. However,
  in some installations this is undesirable, and it is preferred for the
  link to lead to the Enhydris station page—in that case, set
  ``ENHYDRIS_SYNOPTIC_STATION_LINK_TARGET`` to
  ``/stations/{station.id}/`` (if the synoptic domain name is different
  from the main Enhydris domain name, you need to specify the full URL).
  (It would be better to use ``django.urls.reverse()`` here instead of a
  hardwired URL, but it isn't easy to find a general enough solution for
  all that.)

Meta
====

| Copyright (C) 2015-2017 TEI of Epirus
| Copyright (C) 2018-2021 National Technical University of Athens
| Copyright (C) 2018-2021 Institute of Communication and Computer Systems

Enhydris-synoptic is free software: you can redistribute it and/or
modify it under the terms of the GNU Affero General Public License, as
published by the Free Software Foundation; either version 3 of the
License, or (at your option) any later version.

The software is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
licenses for more details.

You should have received a copy of the license along with this
program.  If not, see http://www.gnu.org/licenses/.

Enhydris was funded by several organizations:

* In 2015-2017 by the `TEI of Epirus`_ as part of the IRMA_ project.
* In 2018-2021 by NTUA_ and ICCS_ as part of the OpenHi_ project.

.. _ntua: http://www.ntua.gr/
.. _tei of epirus: http://www.teiep.gr/en/
.. _irma: http://www.irrigation-management.eu/
.. _iccs: https://www.iccs.gr
.. _openhi: https://openhi.net

