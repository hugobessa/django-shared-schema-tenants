from django.db import transaction
from django.utils.text import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError

from rest_framework import serializers

from shared_schema_tenants.models import (Tenant, TenantSite, TenantRelationship)

from shared_schema_tenants.helpers.tenants import create_default_tenant_groups

from shared_schema_tenants.helpers import (
    TenantSettingsHelper, TenantExtraDataHelper)


class TenantSerializer(serializers.ModelSerializer):
    extra_data = serializers.JSONField()

    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'extra_data',]

    def validate_extra_data(self, extra_data):
        extra_data_helper = TenantExtraDataHelper()
        try:
            validated_extra_data = extra_data_helper.validate_fields(self.context, extra_data)
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        return extra_data

    def create(self, validated_data):
        with transaction.atomic():
            tenant = Tenant.objects.create(**validated_data)

            rel = tenant.relationships.create(user=self.context['request'].user)
            rel.groups.add(create_default_tenant_groups()[0])

            return tenant

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.slug = validated_data.get('slug', instance.slug)

        extra_data_helper = TenantExtraDataHelper(instance=instance)
        instance = extra_data_helper.update_fields(
                validated_data.get('extra_data', {}), commit=False)


        instance.save()

        return instance


class TenantSettingsSerializer(serializers.Serializer):

    def to_internal_value(self, data):
        helper = TenantSettingsHelper()
        validated_data = helper.validate_settings(self.context, data)
        helper.update_settings(validated_data, partial=True)
        return helper.get_instance()

    def to_representation(self, obj):
        return obj.settings


class TenantSiteSerializer(serializers.Serializer):
    tenant = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all())
    domain = serializers.CharField(required=True)

    def to_representation(self, instance):
        return {'domain': instance.site.domain}

    def validate_domain(self, domain):
        if Site.objects.filter(domain=domain).exists():
            raise ValidationError(_((
                'This domain is already being used '
                'by another organization')))

        return domain

    def create(self, validated_data):
        tenant = validated_data['tenant']
        domain = validated_data['domain']

        with transaction.atomic():
            site = Site.objects.create(name=domain, domain=domain)
            return TenantSite.objects.create(tenant=tenant, site=site)

