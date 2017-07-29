from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.forms import AuthenticationForm
from model_tenants.models import Tenant, TenantSite, TenantRelationship

admin.site.register(Tenant)
admin.site.register(TenantSite)
admin.site.register(TenantRelationship)
