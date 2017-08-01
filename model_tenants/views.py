from django.shortcuts import render
from rest_framework import generics, permissions, mixins, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from django.db import transaction

from model_tenants.permissions import DjangoTenantModelPermission
from model_tenants.models import *
from model_tenants.utils import import_class
from model_tenants.settings import (
    TENANT_SERIALIZER, TENANT_SITE_SERIALIZER, 
    TENANT_SETTINGS_SERIALIZER)
from model_tenants.helpers.tenants import get_current_tenant


TenantSerializer = import_class(TENANT_SERIALIZER)
TenantSiteSerializer = import_class(TENANT_SITE_SERIALIZER)
TenantSettingsSerializer = import_class(TENANT_SETTINGS_SERIALIZER)


class TenantListView(generics.ListCreateAPIView):
    serializer_class = TenantSerializer
    permission_classes = [DjangoTenantModelPermission]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Tenant.objects.filter(
                relationships__user=self.request.user).distinct()
        else:
            return Tenant.objects.none()


class TenantDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TenantSerializer
    permission_classes = [DjangoTenantModelPermission]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Tenant.objects.filter(
                relationships__user=self.request.user).distinct()
        else:
            return Tenant.objects.none()

    
    def get_object(self):
        return get_current_tenant()


class TenantSettingsDetailsView(generics.RetrieveUpdateAPIView):
    serializer_class = TenantSettingsSerializer
    permission_classes = [DjangoTenantModelPermission]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Tenant.objects.filter(
                relationships__user=self.request.user).distinct()
        else:
            return Tenant.objects.none()


class TenantSiteListView(generics.ListCreateAPIView):
    serializer_class = TenantSiteSerializer
    permission_classes = [DjangoTenantModelPermission]

    def get_queryset(self):
        return TenantSite.objects.filter().distinct()

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data', {})
        data['tenant'] = get_current_tenant()
        kwargs['data'] = data
        return super().get_serializer(*args, **kwargs)


class TenantSiteDetailsView(generics.RetrieveDestroyAPIView):
    serializer_class = TenantSiteSerializer
    permission_classes = [DjangoTenantModelPermission]

    def get_queryset(self):
        return TenantSite.objects.filter().distinct()

    def destroy(self, request, *args, **kwargs):
        tenant_site = self.get_object()
        site = tenant_site.site

        with transaction.atomic():
            response = super().destroy(request, *args, **kwargs)
            site.delete()

        return response
