from django.db import models
from django.conf import settings
from django.contrib.auth.signals import user_logged_in

import json

from model_utils.models import TimeStampedModel

from shared_schema_tenants.exceptions import TenantNotFoundError
from shared_schema_tenants.managers import (
    SingleTenantModelManager, MultipleTenantModelManager)
from shared_schema_tenants.settings import DEFAULT_TENANT_SETTINGS, DEFAULT_TENANT_EXTRA_DATA
from shared_schema_tenants.validators import validate_json


class Tenant(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, primary_key=True)

    if 'postgresql' in settings.DATABASES['default']['ENGINE']:
        from django.contrib.postgres.fields import JSONField
        extra_data = JSONField(blank=True, null=True)
        settings = JSONField(blank=True, null=True,
                            default=DEFAULT_TENANT_SETTINGS)
    else:
        _extra_data = models.TextField(blank=True, null=True,
                            validators=[validate_json],
                            default=DEFAULT_TENANT_EXTRA_DATA)
        _settings = models.TextField(blank=True, null=True,
                            validators=[validate_json],
                            default=json.loads(DEFAULT_TENANT_SETTINGS))

        @property
        def extra_data(self):
            import json
            return json.loads(self._extra_data)

        @settings.setter
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
    site = models.OneToOneField('sites.Site', related_name="tenant_site")

    objects = SingleTenantModelManager()

    def __str__(self):
        return '%s - %s' % (self.tenant.name, self.site.domain)


class TenantRelationship(TimeStampedModel):
    tenant = models.ForeignKey('Tenant', related_name="relationships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="relationships")
    groups = models.ManyToManyField('auth.Group',
                                    related_name="user_tenant_groups")
    permissions = models.ManyToManyField('auth.Permission',
                                        related_name="user_tenant_permissions")

    def __str__(self):
        groups_str = ', '.join([g.name for g in self.groups.all()])
        return '%s - %s (%s)' % (str(self.user), str(self.tenant), groups_str)

    class Meta:
        unique_together = [['user', 'tenant']]
