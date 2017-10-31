from rest_framework import generics, views, response, status, permissions
from django.db import transaction

from shared_schema_tenants.models import Tenant, TenantSite
from shared_schema_tenants.permissions import DjangoTenantModelPermissions
from shared_schema_tenants.utils import import_class
from shared_schema_tenants.settings import get_setting
from shared_schema_tenants.helpers.tenants import get_current_tenant


class TenantListView(generics.ListCreateAPIView):
    permission_classes = [DjangoTenantModelPermissions]

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [permissions.IsAuthenticated]
        return super(TenantListView, self).get_permissions()

    def get_serializer_class(self):
        return import_class(get_setting('TENANT_SERIALIZER'))

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Tenant.objects.filter(
                relationships__user=self.request.user).distinct()
        else:
            return Tenant.objects.none()


class TenantDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [DjangoTenantModelPermissions]

    def get_serializer_class(self):
        return import_class(get_setting('TENANT_SERIALIZER'))

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Tenant.objects.filter(
                relationships__user=self.request.user).distinct()
        else:
            return Tenant.objects.none()

    def get_object(self):
        return get_current_tenant()


class TenantSettingsDetailsView(views.APIView):
    permission_classes = [DjangoTenantModelPermissions]

    def get_serializer_class(self):
        return import_class(get_setting('TENANT_SETTINGS_SERIALIZER'))

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Tenant.objects.filter(
                relationships__user=self.request.user).distinct()
        else:
            return Tenant.objects.none()

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(
            self.request.tenant,
            context={'request': request, 'view': self})
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(
            data=self.request.data,
            context={'request': request, 'view': self})

        if serializer.is_valid():
            serializer.save()
            tenant = get_current_tenant()
            return_serializer = self.get_serializer_class()(tenant)
            return response.Response(return_serializer.data, status=status.HTTP_200_OK)

        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TenantSiteListView(generics.ListCreateAPIView):
    permission_classes = [DjangoTenantModelPermissions]

    def get_serializer_class(self):
        return import_class(get_setting('TENANT_SITE_SERIALIZER'))

    def get_queryset(self):
        return TenantSite.objects.all()

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'POST':
            data = kwargs.get('data', {})
            data['tenant'] = get_current_tenant()
            kwargs['data'] = data
        return super(TenantSiteListView, self).get_serializer(*args, **kwargs)


class TenantSiteDetailsView(generics.DestroyAPIView):
    permission_classes = [DjangoTenantModelPermissions]

    def get_serializer_class(self):
        return import_class(get_setting('TENANT_SITE_SERIALIZER'))

    def get_queryset(self):
        return TenantSite.objects.all()

    def destroy(self, request, *args, **kwargs):
        tenant_site = self.get_object()
        site = tenant_site.site

        with transaction.atomic():
            response = super(TenantSiteDetailsView, self).destroy(request, *args, **kwargs)
            site.delete()

        return response
