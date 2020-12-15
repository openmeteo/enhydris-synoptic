from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

from . import *  # NOQA

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "openmeteo",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": 5432,
    }
}

INSTALLED_APPS.append("enhydris_synoptic")  # NOQA
ENHYDRIS_SYNOPTIC_ROOT = "/tmp/enhydris-synoptic-root"

headless = ChromeOptions()
headless.add_argument("--headless")
SELENIUM_WEBDRIVERS = {
    "default": {
        "callable": webdriver.Chrome,
        "args": [],
        "kwargs": {"options": headless},
    },
}
