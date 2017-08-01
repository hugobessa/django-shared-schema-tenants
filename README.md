# Django Model Tenants

Model based tenants in Django.

## Instalation

``` bash
pip install git+https://github.com/hugobessa/django_model_tenants.git#master
```

## Configuration

1. Add `'model_tenants'` to your `INSTALLED_APPS` variable in django settings

``` python
INSTALLED_APPS = [
  ...
  'model_tenants',
]
```

2. Run `python manage.py migrate` to apply Django Model Tenants migrations



## Usage

### Create new tenants

 Run `python manage.py createtenant` to create you first tenant 

### Turning existing models into a Tenant Model

The models become tenant aware through inheritance. You just have to make your model inherit from `SingleTenantModelMixin` or `MultipleTenantsModelMixin` and you're set.


``` python
from model_tenants.mixins import SingleTenantModelMixin, MultipleTenantsModel

class MyModelA(SingleTenantModelMixin)
    field1 = models.CharField(max_length=100)
    field2 = models.IntegerField()

...

# 'default' tenant selected
instance = MyModelA(field1='test default tenant', field2=0)
instance.save()

...

# 'other' tenant selected
instance = MyModelA(field1='test other tenant', field2=1)
instance.save()

print(MyModel.objects.filter(field1__icontains="test")) 
# prints only the instance with 'test other tenant' in field1

```


### Selecting tenant from request

#### Tenant site

  If you access the site from a domain registered to a tenant, that tenant is automatically selected.

#### Tenant-Slug HTTP header

  If the header `Tenant-Slug` could be found in the request, the tenant with that slug is automatically selected.


#### Forcing tenant selection

You can force tenant selection using set_tenant method.

``` python
from model_tenants.helpers import set_tenant

from .models import MyModel

def my_function():
    set_tenant('default')

    return MyModel.objects.all() # return only the models with tenant__slug='default'

```


### Accessing current tenant

#### From Request

  You can access the current tenant from the request.

  ``` python
  def my_view(request):
      current_tenant = request.tenant
      ...
  ```

#### From `get_current_tenant` helper

  ``` python
  from model_tenants.helpers import get_current_tenant

  def my_function():
      current_tenant = get_current_tenant()
      ...
  ```

The models that inherit from `SingleTenantModelMixin` or `MultipleTenantsModelMixin` are also tenant aware. If you reatrieve a collection from database with a tenant context in your request, your collection will already be filtered by that tenant.