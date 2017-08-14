# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

import django

DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "lq54#hsg57uikn$*=dk+4t$(zg*2k6!^5+8opzp^lsgyp$s-rj"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "shared_schema_tenants",
]

SITE_ID = 1

if django.VERSION >= (1, 10):
    MIDDLEWARE = (
        'shared_schema_tenants.middleware.TenantMiddleware',
    )
else:
    MIDDLEWARE_CLASSES = (
        'shared_schema_tenants.middleware.TenantMiddleware',
    )
