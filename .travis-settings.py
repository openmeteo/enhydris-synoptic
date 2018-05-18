from . import *

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'openmeteo',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': 5432,
    }
}

INSTALLED_APPS.append('enhydris_synoptic')
ENHYDRIS_SYNOPTIC_ROOT = '/tmp/enhydris-synoptic-root'
