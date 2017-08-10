============
Installation
============

At the command line::

    $ easy_install django-shared-schema-tenants

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv django-shared-schema-tenants
    $ pip install django-shared-schema-tenants


To use Django Shared Schema Tenants in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'shared_schema_tenants.apps.SharedSchemaTenantsConfig',
        ...
    )


You also have to add TenantMiddleware to django  `MIDDLEWARES`:

.. code-block:: python

    MIDDLEWARES = [
        # ...
        'shared_schema_tenants.middleware.TenantMiddleware',
        # ...
    ]
