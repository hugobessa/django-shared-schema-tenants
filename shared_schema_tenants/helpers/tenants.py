from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.conf import settings as django_settings


def get_current_tenant():
    from shared_schema_tenants.middleware import TenantMiddleware
    return TenantMiddleware.get_current_tenant()


def set_tenant(tenant_slug):
    from shared_schema_tenants.middleware import TenantMiddleware
    return TenantMiddleware.set_tenant(tenant_slug)


def create_default_tenant_groups():
    with transaction.atomic():
        group, created = Group.objects.get_or_create(name='tenant_owner')

        if created:
            default_permissions_names = []
            app_models = [
                {
                    'app_name': 'plans',
                    'models': [
                        'plan', 'plancategory', 'planupdateflowsettings',
                        'scheduledplanupdate', 'planmigration',
                        'planupgradesuggestion', 'benefit', 'basebenefit',
                        'resource', 'resourceuse', 'plancontract',
                        'plancontractusedata', 'scheduledbill',
                        'plancredit', 'planownertype', 'planowner',
                        'systemtoken',
                    ]
                },
                {
                    'app_name': 'basic_auth',
                    'models': [
                        'user',
                    ]
                },
                {
                    'app_name': 'shared_schema_tenants',
                    'models': [
                        'tenant', 'tenantsite', 'tenantinvitation',
                    ]
                },
            ]

            for app in app_models:
                app_name = app['app_name']
                for model_name in app['models']:
                    default_permissions_names.append('%s.add_%s' % (app_name, model_name))
                    default_permissions_names.append('%s.change_%s' % (app_name, model_name))
                    default_permissions_names.append('%s.delete_%s' % (app_name, model_name))
                    if 'admin_view_permission' in django_settings.INSTALLED_APPS:
                        default_permissions_names.append('%s.view_%s' % (app_name, model_name))

            for perm in default_permissions_names:
                try:
                    group.permissions.add(Permission.objects.get(
                        content_type__app_label=perm.split('.')[0],
                        codename=perm.split('.')[1]))
                except Permission.DoesNotExist:
                    pass

        return [group]
