from django.shortcuts import render
from rest_framework import generics, permissions, mixins, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from django.db import transaction

from model_tenants.permissions import (DjangoTenantModelPermission,
                                      ValidInvitationPermission)
from model_tenants.serializers import *
from model_tenants.models import *


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


class TenantSiteListView(generics.ListCreateAPIView):
    serializer_class = TenantSiteSerializer
    permission_classes = [DjangoTenantModelPermission]

    def get_queryset(self):
        return TenantSite.objects.filter().distinct()


    def get_serializer(self, *args, **kwargs):
        from model_tenants.middleware import TenantMiddleware
        data = kwargs.get('data', {})
        data['tenant'] = TenantMiddleware.get_current_tenant()
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
