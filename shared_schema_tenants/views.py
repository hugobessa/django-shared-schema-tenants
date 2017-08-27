from rest_framework import generics, views, response, status
from django.db import transaction

from shared_schema_tenants.permissions import DjangoTenantModelPermission
from shared_schema_tenants.models import Tenant, TenantSite
from shared_schema_tenants.utils import import_class
from shared_schema_tenants.settings import (
    TENANT_SERIALIZER, TENANT_SITE_SERIALIZER,
    TENANT_SETTINGS_SERIALIZER)
from shared_schema_tenants.helpers.tenants import get_current_tenant


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


class TenantSettingsDetailsView(views.APIView):
    serializer_class = TenantSettingsSerializer
    permission_classes = [DjangoTenantModelPermission]

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer_class(
            self.request.tenant,
            context={'request': request, 'view': self})
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class(
            data=self.request.data,
            context={'request': request, 'view': self})

        if serializer.is_valid():
            return response.Response(serializer.data, status=status.HTTP_200_OK)

        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TenantSiteListView(generics.ListCreateAPIView):
    serializer_class = TenantSiteSerializer
    permission_classes = [DjangoTenantModelPermission]

    def get_queryset(self):
        return TenantSite.objects.filter().distinct()

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data', {})
        data['tenant'] = get_current_tenant()
        kwargs['data'] = data
        return super(TenantSiteListView, self).get_serializer(*args, **kwargs)


class TenantSiteDetailsView(generics.DestroyAPIView):
    serializer_class = TenantSiteSerializer
    permission_classes = [DjangoTenantModelPermission]

    def get_queryset(self):
        return TenantSite.objects.filter().distinct()

    def destroy(self, request, *args, **kwargs):
        tenant_site = self.get_object()
        site = tenant_site.site

        with transaction.atomic():
            response = super(TenantSiteDetailsView, self).destroy(request, *args, **kwargs)
            site.delete()

        return response
