#
# WARNING: this module is only used to run the unit tests. Do not use it to run
# HyperKitty, use the hyperkitty_standalone module instead (please see the
# HyperKitty docs to find it).
#

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = True
TEMPLATE_DEBUG = DEBUG

MAILMAN_API_URL=r'http://%(username)s:%(password)s@localhost:8001/3.0/'
MAILMAN_USER='mailmanapi'
MAILMAN_PASS='mailmanpass'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.messages.middleware.MessageMiddleware',
    'hyperkitty.lib.store.KittyStoreDjangoMiddleware',
)

ROOT_URLCONF = 'hyperkitty.tests_conf.urls_test'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'hyperkitty',
)

LOGIN_URL          = '/hyperkitty/accounts/login/'
KITTYSTORE_URL = 'sqlite:'
KITTYSTORE_DEBUG=False
USE_MOCKUPS = False
