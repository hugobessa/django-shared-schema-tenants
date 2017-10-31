from django.db import models
from django.conf import settings as django_settings
from django.contrib.sites.models import Site
from django.db.models.signals import post_delete

import json

from model_utils.models import TimeStampedModel

from shared_schema_tenants.managers import (
    SingleTenantModelManager)
from shared_schema_tenants.settings import get_setting
from shared_schema_tenants.validators import validate_json


class Tenant(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, primary_key=True)

    if 'postgresql' in django_settings.DATABASES['default']['ENGINE']:
        from django.contrib.postgres.fields import JSONField
        extra_data = JSONField(blank=True, null=True,
                               default=get_setting('DEFAULT_TENANT_EXTRA_DATA'))
        settings = JSONField(blank=True, null=True,
                             default=get_setting('DEFAULT_TENANT_SETTINGS'))
    else:
        _extra_data = models.TextField(blank=True, null=True,
                                       validators=[validate_json],
                                       default=json.dumps(get_setting('DEFAULT_TENANT_EXTRA_DATA')))
        _settings = models.TextField(blank=True, null=True,
                                     validators=[validate_json],
                                     default=json.dumps(get_setting('DEFAULT_TENANT_SETTINGS')))

        @property
        def extra_data(self):
            import json
            return json.loads(self._extra_data)

        @extra_data.setter
        def extra_data(self, value):
            import json
            self._extra_data = json.dumps(value)

        @property
        def settings(self):
            import json
            return json.loads(self._settings)

        @settings.setter
        def settings(self, value):
            import json
            self._settings = json.dumps(value)

    def __str__(self):
        return self.name


class TenantSite(TimeStampedModel):
    tenant = models.ForeignKey('Tenant', related_name="tenant_sites")
    site = models.OneToOneField(Site, related_name="tenant_site")

    objects = SingleTenantModelManager

    def __str__(self):
        return '%s - %s' % (self.tenant.name, self.site.domain)


def post_delete_tenant_site(sender, instance, *args, **kwargs):
    if instance.site:
        instance.site.delete()
post_delete.connect(post_delete_tenant_site, sender=TenantSite)


class TenantRelationship(TimeStampedModel):
    tenant = models.ForeignKey('Tenant', related_name="relationships")
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, related_name="relationships")
    groups = models.ManyToManyField('auth.Group',
                                    related_name="user_tenant_groups",
                                    blank=True)
    permissions = models.ManyToManyField('auth.Permission',
                                         related_name="user_tenant_permissions",
                                         blank=True)

    def __str__(self):
        groups_str = ', '.join([g.name for g in self.groups.all()])
        return '%s - %s (%s)' % (str(self.user), str(self.tenant), groups_str)

    class Meta:
        unique_together = [('user', 'tenant')]
