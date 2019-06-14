=====
Usage
=====

Instalation on Django
---------------------

To use Django Shared Schema Tenants in a project, add it to your `INSTALLED_APPS`:

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


Create new tenants
------------------

Run ``python manage.py createtenant`` to create you first tenant


Turning existing models into a Tenant Model
-------------------------------------------

The models become tenant aware through inheritance. You just have to
make your model inherit from ``SingleTenantModelMixin`` or
``MultipleTenantsModelMixin`` and you’re set.

.. code:: python

    from shared_schema_tenants.mixins import SingleTenantModelMixin, MultipleTenantsModelMixin

    class MyModelA(SingleTenantModelMixin)
        field1 = models.CharField(max_length=100)
        field2 = models.IntegerField()

    # ...

    # 'default' tenant selected
    instance = MyModelA(field1='test default tenant', field2=0)
    instance.save()

    # ...

    # 'other' tenant selected
    instance = MyModelA(field1='test other tenant', field2=1)
    instance.save()

    print(MyModel.objects.filter(field1__icontains="test"))
    # prints only the instance with 'test other tenant' in field1

    Obs.: For Django 1.8 and 1.9 you have to access the data by the active tenant through :python:`MyModel.tenant_objects.all()` due to a `Django bug that was fixes in version 1.10 <https://code.djangoproject.com/ticket/14891>`_


Selecting tenant on requests
----------------------------

Tenant site
~~~~~~~~~~~

If you access the site from a domain registered to a tenant, that tenant
is automatically selected.

Tenant-Slug HTTP header
~~~~~~~~~~~~~~~~~~~~~~~

If the header ``Tenant-Slug`` could be found in the request, the tenant
with that slug is automatically selected.

Forcing tenant selection
~~~~~~~~~~~~~~~~~~~~~~~~

You can force tenant selection using set\_tenant method.

.. code:: python

    from shared_schema_tenants.helpers import set_current_tenant

    from .models import MyModel

    def my_function():
        set_current_tenant('default')

        return MyModel.objects.all() # return only the models with tenant__slug='default'


    Obs.: For Django 1.8 and 1.9 you have to access the data by the active tenant through :python:`MyModel.tenant_objects.all()` due to a `Django bug that was fixes in version 1.10 <https://code.djangoproject.com/ticket/14891>`_

Accessing current tenant
------------------------

From Request
~~~~~~~~~~~~

You can access the current tenant from the request.

.. code:: python

    def my_view(request):
        current_tenant = request.tenant
        # ...


From ``get_current_tenant`` helper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from shared_schema_tenants.helpers import get_current_tenant

    def my_view(request):
        current_tenant = get_current_tenant()
        # ...


The models that inherit from ``SingleTenantModelMixin`` or
``MultipleTenantsModelMixin`` are also tenant aware. If you retrieve a
collection from database with a tenant context in your request, your
collection will already be filtered by that tenant.



Configuration options
---------------------

To configure how Django Shared Schema Tenants works you can set a bunch of options in the SHARED_SCHEMA_TENANTS dictionary in django settings

SERIALIZERS
~~~~~~~~~~~
It's a dict where you can replace the serializers to be used in Django Shared Schema Tenants REST API endpoints.
default value:

.. code:: python
    {
        'TENANT_SERIALIZER': 'shared_schema_tenants.serializers.TenantSerializer',
        'TENANT_SITE_SERIALIZER': 'shared_schema_tenants.serializers.TenantSiteSerializer',
        'TENANT_SETTINGS_SERIALIZER': 'shared_schema_tenants.serializers.TenantSettingsSerializer',
        'TENANT_SITE_SERIALIZER': 'shared_schema_tenants.serializers.TenantSiteSerializer',
    }

DEFAULT_TENANT_SLUG
~~~~~~~~~~~~~~~~~~~

In here you can define you default tenant (tenant to be use in case the middleware can't retrieve the tenant from the request)

default value: ``'default'``


TENANT_SETTINGS_FIELDS
~~~~~~~~~~~~~~~~~~~~~~

In here you define the fields in tenant setting. Every field is a dict and must have the followiing format:

.. code:: python
    {
        'settings_key_one': {
            'type': 'number'
            'default': DEFAULT_VALUE_OF_THE_CORRECT_TYPE,
            'validators': [
                VALIDATOR_ONE, # validators must return clead data for the field or
                VALIDATOR_TWO, # raise django.core.exceptions.ValidationError
            ],
        },
        'settings_key_two': {
            'type': 'string'
            'default': DEFAULT_VALUE_OF_THE_CORRECT_TYPE,
            'validators': [
                VALIDATOR_THREE, # validators must return clead data for the field or
            ],
        },

    }

The available types are ``'number'``, ``'string'``, ``'boolean'``, ``'object'`` and ``'list'``.

default value: ``{ }``


TENANT_SETTINGS_FIELDS
~~~~~~~~~~~~~~~~~~~~~~

In here you define the fields in tenant extra_data. This field is a dict and must have the following format:

.. code:: python
    {
        'extra_data_key_one': {
            'type': 'number'
            'default': DEFAULT_VALUE_OF_THE_CORRECT_TYPE,
            'validators': [
                VALIDATOR_ONE, # validators must return clead data for the field or
                VALIDATOR_TWO, # raise django.core.exceptions.ValidationError
            ],
        },
        'extra_data_key_two': {
            'type': 'string'
            'default': DEFAULT_VALUE_OF_THE_CORRECT_TYPE,
            'validators': [
                VALIDATOR_THREE, # validators must return clead data for the field or
            ],
        },

    }

The available types are ``'number'``, ``'string'``, ``'boolean'``, ``'object'`` and ``'list'``.

default value: { }


DEFAULT_SITE_DOMAIN
~~~~~~~~~~~~~~~~~~~

In here you define your default site domain.

default value: ``'localhost'``


TENANT_HTTP_HEADER
~~~~~~~~~~~~~~~~~~

In here you can defined which http header we should use to extract the tenant slug

default value: ``'Tenant-Slug'``
