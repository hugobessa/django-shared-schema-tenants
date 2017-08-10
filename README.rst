=============================
Django Shared Schema Tenants
=============================

.. image:: https://badge.fury.io/py/django-shared-schema-tenants.svg
    :target: https://badge.fury.io/py/django-shared-schema-tenants

.. image:: https://travis-ci.org/hugobessa/django-shared-schema-tenants.svg?branch=master
    :target: https://travis-ci.org/hugobessa/django-shared-schema-tenants

.. image:: https://codecov.io/gh/hugobessa/django-shared-schema-tenants/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/hugobessa/django-shared-schema-tenants

A lib to help in the creation applications with shared schema without suffering

Documentation
-------------

The full documentation is at https://django-shared-schema-tenants.readthedocs.io.

Quickstart
----------

Install Django Shared Schema Tenants::

    pip install django-shared-schema-tenants

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'shared_schema_tenants.apps.SharedSchemaTenantsConfig',
        ...
    )

Add Django Shared Schema Tenants's URL patterns:

.. code-block:: python

    from shared_schema_tenants import urls as shared_schema_tenants_urls


    urlpatterns = [
        ...
        url(r'^', include(shared_schema_tenants_urls)),
        ...
    ]

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
