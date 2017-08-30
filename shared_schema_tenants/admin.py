from django import forms
from django.contrib import admin
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.utils.text import ugettext_lazy as _
import json

from shared_schema_tenants.models import Tenant, TenantSite, TenantRelationship
from shared_schema_tenants.helpers.tenant_extra_data import TenantExtraDataHelper
from shared_schema_tenants.helpers.tenant_settings import TenantSettingsHelper


class TenantSiteForm(forms.ModelForm):
    site = forms.CharField(max_length=255)

    class Meta:
        model = TenantSite
        fields = ['site', 'tenant']

    def __init__(self, *args, **kwargs):
        super(TenantSiteForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            self.initial['site'] = kwargs.get('instance').site.domain

    def clean_site(self):
        site = self.cleaned_data['site']
        instance = getattr(self, 'instance')
        new_site_instance, created = Site.objects.get_or_create(
            domain=site, defaults={'name': self.data['name']})
        try:
            old_site_instance = instance.site
        except Site.DoesNotExist:
            old_site_instance = None

        if not created and old_site_instance and old_site_instance != new_site_instance:
            raise ValidationError(
                _('A site with this domain already asigned to an organization'))

        return new_site_instance

    def save(self, *args, **kwargs):
        instance = getattr(self, 'instance')
        delete_old_site = False
        if instance:
            old_instance = TenantSite.objects.filter(id=instance.id).first()
            if old_instance and old_instance.site != self.cleaned_data['site']:
                delete_old_site = True
                old_site = old_instance.site

        instance = super(TenantSiteForm, self).save(*args, **kwargs)

        if delete_old_site:
            old_site.delete()

        return instance


class TenantForm(forms.ModelForm):

    class Meta:
        model = Tenant
        fields = '__all__'

    def clean__extra_data(self):
        extra_data = self.cleaned_data.get('extra_data', {})
        extra_data_helper = TenantExtraDataHelper()
        try:
            validated_extra_data = extra_data_helper.validate_fields(
                {}, extra_data, partial=False)
        except ValidationError as e:
            raise ValidationError(json.dumps(e.message_dict))
        else:
            return validated_extra_data

    def clean__settings(self):
        settings = self.cleaned_data.get('settings', {})
        settings_helper = TenantSettingsHelper()
        try:
            validated_settings = settings_helper.validate_fields(
                {}, settings, partial=False)
        except ValidationError as e:
            raise ValidationError(json.dumps(e.message_dict))
        else:
            return validated_settings


class TenantSiteInLine(admin.StackedInline):
    model = TenantSite
    form = TenantSiteForm
    extra = 0
    min_num = 1


class TenantAdmin(admin.ModelAdmin):
    model = Tenant
    form = TenantForm
    inlines = [TenantSiteInLine]
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Tenant, TenantAdmin)
admin.site.register(TenantRelationship)
